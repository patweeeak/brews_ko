"""
Shopping cart. Guests get a session-based cart; signed-in customers get
their cart persisted on CustomerProfile.cart_data instead, so it survives
logging out and back in.

Line items are keyed by "<product_id>" for single-price items, or
"<product_id>:<size>" for drinks — so a customer can have Regular and
Large of the same drink in the cart as two distinct lines.
"""
from decimal import Decimal
from django.conf import settings
from .models import Product


class Cart:
    def __init__(self, request):
        self.session = request.session
        self.profile = None
        if request.user.is_authenticated and not request.user.is_staff:
            self.profile = getattr(request.user, 'customer_profile', None)

        if self.profile is not None:
            self.cart = self.profile.cart_data or {}
        else:
            cart = self.session.get(settings.CART_SESSION_ID)
            if cart is None:
                cart = self.session[settings.CART_SESSION_ID] = {}
            self.cart = cart

    @staticmethod
    def make_key(product_id, size=''):
        return f"{product_id}:{size}" if size else str(product_id)

    def add(self, product, quantity=1, size='', override_quantity=False):
        key = self.make_key(product.id, size)
        if key not in self.cart:
            price = product.price_for_size(size) if size else product.price
            self.cart[key] = {
                'quantity': 0,
                'price': str(price),
                'name': product.name,
                'product_id': product.id,
                'size': size,
            }
        if override_quantity:
            self.cart[key]['quantity'] = quantity
        else:
            self.cart[key]['quantity'] += quantity
        if self.cart[key]['quantity'] < 1:
            self.cart[key]['quantity'] = 1
        self.save()

    def remove_key(self, key):
        if key in self.cart:
            del self.cart[key]
            self.save()

    def update_quantity(self, key, quantity):
        if key not in self.cart:
            return
        if quantity < 1:
            self.remove_key(key)
        else:
            self.cart[key]['quantity'] = quantity
            self.save()

    def save(self):
        if self.profile is not None:
            self.profile.cart_data = self.cart
            self.profile.save(update_fields=['cart_data'])
        else:
            self.session.modified = True

    def clear(self):
        self.cart = {}
        self.save()

    def __iter__(self):
        product_ids = {item.get('product_id') for item in self.cart.values()}
        products = Product.objects.filter(id__in=product_ids)
        products_map = {p.id: p for p in products}
        cart_copy = self.cart.copy()
        for key, item in cart_copy.items():
            product = products_map.get(item.get('product_id'))
            if not product:
                continue
            item_out = item.copy()
            item_out['product'] = product
            item_out['key'] = key
            item_out['size_label'] = Product.size_label(item.get('size', ''))
            item_out['price'] = Decimal(item['price'])
            item_out['total_price'] = item_out['price'] * item_out['quantity']
            yield item_out

    def __len__(self):
        return sum(item['quantity'] for item in self.cart.values())

    def get_total_price(self):
        return sum(
            Decimal(item['price']) * item['quantity'] for item in self.cart.values()
        )

    def is_empty(self):
        return len(self.cart) == 0
