from django.urls import path
from . import views

app_name = 'shop'

urlpatterns = [
    path('', views.home, name='home'),
    path('menu/', views.menu, name='menu'),
    path('about/', views.about, name='about'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),

    path('cart/', views.cart_detail, name='cart_detail'),
    path('cart/add/<int:product_id>/', views.cart_add, name='cart_add'),
    path('cart/update/<str:item_key>/', views.cart_update, name='cart_update'),
    path('cart/remove/<str:item_key>/', views.cart_remove, name='cart_remove'),

    path('checkout/', views.checkout, name='checkout'),
    path('order/success/<int:order_id>/', views.order_success, name='order_success'),

    # Order tracking — works for guests (Order ID + contact number) and customers alike
    path('track-order/', views.track_order, name='track_order'),
    path('track-order/<int:order_id>/', views.order_track_detail, name='order_track_detail'),

    # Customer accounts (separate from staff /admin/login/)
    path('account/signup/', views.signup, name='signup'),
    path('account/login/', views.CustomerLoginView.as_view(), name='login'),
    path('account/logout/', views.CustomerLogoutView.as_view(), name='logout'),
    path('account/profile/', views.profile, name='profile'),
    path('account/receipts/<int:payment_id>/', views.receipt_detail, name='receipt_detail'),
    path('favorites/toggle/<int:product_id>/', views.toggle_favorite, name='toggle_favorite'),

    path('account/photobooth/', views.photobooth, name='photobooth'),
    path('account/photobooth/save/', views.photobooth_save, name='photobooth_save'),
    path('account/photobooth/gallery/', views.photobooth_gallery, name='photobooth_gallery'),
    path('account/photobooth/<int:strip_id>/', views.photobooth_detail, name='photobooth_detail'),
    path('account/photobooth/<int:strip_id>/email/', views.photobooth_email, name='photobooth_email'),
    path('account/photobooth/<int:strip_id>/delete/', views.photobooth_delete, name='photobooth_delete'),

    path('review/add/', views.add_review, name='review_add'),
    path('review/<int:review_id>/delete/', views.delete_review, name='review_delete'),
]
