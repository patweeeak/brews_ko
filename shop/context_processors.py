from .cart import Cart
from .models import GamificationSettings, ShopSettings


def cart_summary(request):
    """Makes cart item count, brand info, and gamification status available in every template."""
    cart = Cart(request)
    shop = ShopSettings.get_solo()
    gamification = GamificationSettings.get_solo()

    customer_profile = None
    if request.user.is_authenticated and not request.user.is_staff:
        customer_profile = getattr(request.user, 'customer_profile', None)

    is_cashier = request.user.is_authenticated and hasattr(request.user, 'cashier_profile')

    return {
        'cart_item_count': len(cart),
        'shop_name': shop.name,
        'shop_address': shop.address,
        'shop_phone': shop.phone,
        'shop_email': shop.email,
        'shop_hours': shop.hours,
        'shop_facebook': shop.facebook,
        'shop_instagram': shop.instagram,
        'gamification_enabled': gamification.enabled,
        'gamification_program_name': gamification.program_name,
        'customer_profile': customer_profile,
        'is_cashier': is_cashier,
    }
