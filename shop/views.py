from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Avg, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST

from .cart import Cart
from .forms import (
    AddToCartForm, CheckoutForm, CustomerAuthenticationForm,
    CustomerProfileForm, CustomerSignupForm, ReviewForm,
)
from .models import (
    Category, CustomerProfile, GamificationSettings, HomePageContent,
    Order, OrderItem, Product, Review,
)


def home(request):
    """Landing page for guests/staff. Logged-in customers get their profile as 'home' instead."""
    if _get_customer_profile(request):
        return redirect('shop:profile')

    featured_products = Product.objects.filter(available=True, featured=True).select_related('category')[:6]
    categories = Category.objects.all()
    store_reviews = Review.objects.filter(product__isnull=True).select_related('customer')[:8]
    store_rating = Review.objects.filter(product__isnull=True).aggregate(avg=Avg('rating'))['avg']
    context = {
        'homepage': HomePageContent.get_solo(),
        'featured_products': featured_products,
        'categories': categories,
        'store_reviews': store_reviews,
        'store_rating': round(store_rating, 1) if store_rating else 0,
    }
    return render(request, 'shop/home.html', context)


def menu(request):
    """Full menu with category filter chips + search."""
    categories = Category.objects.all()
    products = Product.objects.filter(available=True).select_related('category')

    selected_category = request.GET.get('category', '')
    query = request.GET.get('q', '').strip()

    if selected_category:
        products = products.filter(category__slug=selected_category)

    if query:
        products = products.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )

    favorite_ids = _favorite_ids(request)

    context = {
        'categories': categories,
        'products': products,
        'selected_category': selected_category,
        'query': query,
        'favorite_ids': favorite_ids,
    }
    return render(request, 'shop/menu.html', context)


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, available=True)
    related_products = Product.objects.filter(
        category=product.category, available=True
    ).exclude(pk=product.pk)[:4]
    form = AddToCartForm()
    customer_profile = _get_customer_profile(request)
    already_reviewed = bool(
        customer_profile and product.reviews.filter(customer=customer_profile).exists()
    )
    context = {
        'product': product,
        'related_products': related_products,
        'form': form,
        'is_favorited': product.id in _favorite_ids(request),
        'reviews': product.reviews.select_related('customer').all(),
        'review_form': ReviewForm() if customer_profile and not already_reviewed else None,
        'already_reviewed': already_reviewed,
    }
    return render(request, 'shop/product_detail.html', context)


def cart_detail(request):
    cart = Cart(request)
    return render(request, 'shop/cart.html', {'cart': cart})


@require_POST
def cart_add(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id, available=True)
    form = AddToCartForm(request.POST)
    quantity = form.cleaned_data['quantity'] if form.is_valid() else 1

    size = request.POST.get('size', '') if product.category.is_drink else ''
    if size not in (Product.SIZE_REGULAR, Product.SIZE_LARGE):
        size = Product.SIZE_REGULAR if product.category.is_drink else ''

    cart.add(product=product, quantity=quantity, size=size)
    label = f" ({Product.size_label(size)})" if size else ""
    messages.success(request, f'Added {quantity} x {product.name}{label} to your cart.')

    next_url = request.POST.get('next') or 'shop:menu'
    return redirect(next_url)


@require_POST
def cart_update(request, item_key):
    cart = Cart(request)
    try:
        quantity = int(request.POST.get('quantity', 1))
    except (TypeError, ValueError):
        quantity = 1
    cart.update_quantity(item_key, quantity)
    if quantity < 1:
        messages.info(request, 'Item removed from your cart.')
    return redirect('shop:cart_detail')


@require_POST
def cart_remove(request, item_key):
    cart = Cart(request)
    cart.remove_key(item_key)
    messages.info(request, 'Removed from your cart.')
    return redirect('shop:cart_detail')


def checkout(request):
    cart = Cart(request)
    if cart.is_empty():
        messages.warning(request, "Your cart is empty. Add something delicious first!")
        return redirect('shop:menu')

    customer_profile = _get_customer_profile(request)
    initial = {}
    if customer_profile:
        initial = {'customer_name': customer_profile.full_name, 'contact_number': customer_profile.mobile_number}

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                order = form.save(commit=False)
                order.total_amount = cart.get_total_price()
                if customer_profile:
                    order.customer_user = request.user
                order.save()
                for item in cart:
                    OrderItem.objects.create(
                        order=order,
                        product=item['product'],
                        product_name=item['product'].name,
                        size=item.get('size', ''),
                        unit_price=item['price'],
                        quantity=item['quantity'],
                    )
                order.recalculate_total()
            cart.clear()
            return redirect('shop:order_success', order_id=order.id)
    else:
        form = CheckoutForm(initial=initial)

    return render(request, 'shop/checkout.html', {'form': form, 'cart': cart})


def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'shop/order_success.html', {'order': order})


def about(request):
    return render(request, 'shop/about.html')


# ---------------------------------------------------------------------------
# Customer accounts — signup, login, logout, profile, favorites.
# The 'customer' user type differs from a 'guest' only in that a customer
# has signed in; guests keep ordering anonymously through the session cart
# exactly as before. Staff/admin accounts never touch these views.
# ---------------------------------------------------------------------------

def _get_customer_profile(request):
    if not request.user.is_authenticated or request.user.is_staff:
        return None
    return getattr(request.user, 'customer_profile', None)


def _favorite_ids(request):
    profile = _get_customer_profile(request)
    if not profile:
        return set()
    return set(profile.favorites.values_list('id', flat=True))


def signup(request):
    if request.user.is_authenticated:
        return redirect('shop:profile')

    if request.method == 'POST':
        form = CustomerSignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            messages.success(request, f"Welcome to Brew's Ko, {user.customer_profile.full_name}!")
            return redirect('shop:profile')
    else:
        form = CustomerSignupForm()

    return render(request, 'shop/signup.html', {'form': form})


class CustomerLoginView(auth_views.LoginView):
    """Sign-in for the customer user type — kept entirely separate from /admin/login/."""
    template_name = 'shop/login.html'
    redirect_authenticated_user = True
    form_class = CustomerAuthenticationForm

    def get_success_url(self):
        return reverse_lazy('shop:profile')

    def form_valid(self, form):
        response = super().form_valid(form)
        # Merge any guest-session cart into the customer's persisted cart.
        profile = getattr(self.request.user, 'customer_profile', None)
        session_cart = self.request.session.get(settings.CART_SESSION_ID)
        if profile is not None and session_cart:
            merged = dict(profile.cart_data or {})
            for product_id, item in session_cart.items():
                if product_id in merged:
                    merged[product_id]['quantity'] += item['quantity']
                else:
                    merged[product_id] = item
            profile.cart_data = merged
            profile.save(update_fields=['cart_data'])
            del self.request.session[settings.CART_SESSION_ID]
        return response


class CustomerLogoutView(auth_views.LogoutView):
    next_page = reverse_lazy('shop:home')


@login_required(login_url='shop:login')
def profile(request):
    if request.user.is_staff:
        return redirect('dashboard:index')

    customer_profile, _created = CustomerProfile.objects.get_or_create(
        user=request.user, defaults={'full_name': request.user.get_username(), 'mobile_number': ''}
    )

    if request.method == 'POST':
        form = CustomerProfileForm(request.POST, request.FILES, instance=customer_profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated.')
            return redirect('shop:profile')
    else:
        form = CustomerProfileForm(instance=customer_profile)

    context = {
        'form': form,
        'profile': customer_profile,
        'orders': customer_profile.orders[:10],
        'favorites': customer_profile.favorites.select_related('category').all(),
        'gamification': GamificationSettings.get_solo(),
        'my_reviews': customer_profile.reviews.select_related('product').all(),
        'store_review': customer_profile.reviews.filter(product__isnull=True).first(),
        'store_review_form': ReviewForm() if not customer_profile.reviews.filter(product__isnull=True).exists() else None,
    }
    return render(request, 'shop/profile.html', context)


@login_required(login_url='shop:login')
@require_POST
def toggle_favorite(request, product_id):
    if request.user.is_staff:
        return redirect('dashboard:index')

    product = get_object_or_404(Product, id=product_id)
    customer_profile, _created = CustomerProfile.objects.get_or_create(
        user=request.user, defaults={'full_name': request.user.get_username(), 'mobile_number': ''}
    )

    if customer_profile.favorites.filter(id=product.id).exists():
        customer_profile.favorites.remove(product)
        messages.info(request, f'Removed {product.name} from your favorites.')
    else:
        customer_profile.favorites.add(product)
        messages.success(request, f'Added {product.name} to your favorites.')

    next_url = request.POST.get('next') or product.get_absolute_url()
    return redirect(next_url)


@login_required(login_url='shop:login')
@require_POST
def add_review(request):
    """
    Add a rating + comment, either for a specific product (POST 'product_id')
    or for the store overall (product_id omitted/blank). Customer-only.
    """
    if request.user.is_staff:
        return redirect('dashboard:index')

    customer_profile = _get_customer_profile(request)
    if not customer_profile:
        return redirect('shop:login')

    product = None
    product_id = request.POST.get('product_id')
    if product_id:
        product = get_object_or_404(Product, id=product_id)

    if Review.objects.filter(customer=customer_profile, product=product).exists():
        messages.warning(request, "You've already reviewed this.")
        return redirect(request.POST.get('next') or 'shop:home')

    form = ReviewForm(request.POST, request.FILES)
    if form.is_valid():
        review = form.save(commit=False)
        review.customer = customer_profile
        review.product = product
        review.save()
        messages.success(request, 'Thanks for your review!')
    else:
        messages.error(request, 'Please provide a valid rating and comment.')

    return redirect(request.POST.get('next') or 'shop:home')


@login_required(login_url='shop:login')
@require_POST
def delete_review(request, review_id):
    customer_profile = _get_customer_profile(request)
    review = get_object_or_404(Review, id=review_id, customer=customer_profile)
    review.delete()
    messages.info(request, 'Review deleted.')
    return redirect(request.POST.get('next') or 'shop:profile')
