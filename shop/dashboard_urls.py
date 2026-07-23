from django.urls import path
from . import dashboard_views as views

app_name = 'dashboard'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='index'),

    path('orders/', views.OrderListView.as_view(), name='orders'),
    path('orders/<int:pk>/', views.OrderDetailView.as_view(), name='order_detail'),

    path('products/', views.ProductListView.as_view(), name='products'),
    path('products/add/', views.ProductCreateView.as_view(), name='product_add'),
    path('products/<int:pk>/edit/', views.ProductUpdateView.as_view(), name='product_edit'),

    path('categories/', views.CategoryListView.as_view(), name='categories'),
    path('categories/add/', views.CategoryCreateView.as_view(), name='category_add'),
    path('categories/<int:pk>/edit/', views.CategoryUpdateView.as_view(), name='category_edit'),

    path('customers/', views.CustomerListView.as_view(), name='customers'),

    path('cashier/', views.CashierOrdersView.as_view(), name='cashier'),
    path('cashier/pay/<int:order_id>/', views.RecordPaymentView.as_view(), name='record_payment'),
    path('cashiers/', views.CashierManagementView.as_view(), name='cashiers'),
    path('cashiers/<int:pk>/delete/', views.CashierDeleteView.as_view(), name='cashier_delete'),

    path('receipts/', views.ReceiptListView.as_view(), name='receipts'),
    path('receipts/<int:pk>/', views.ReceiptDetailView.as_view(), name='receipt_detail'),

    path('homepage/', views.HomePageContentUpdateView.as_view(), name='homepage'),
    path('homepage/reviews/<int:pk>/delete/', views.ReviewDeleteView.as_view(), name='review_delete'),

    path('gamification/', views.GamificationView.as_view(), name='gamification'),

    path('reports/', views.ReportsView.as_view(), name='reports'),
    path('reports/data/revenue/', views.RevenueTrendDataView.as_view(), name='reports_revenue_data'),
    path('reports/data/category/', views.CategoryRevenueDataView.as_view(), name='reports_category_data'),
    path('reports/data/products/', views.TopProductsDataView.as_view(), name='reports_products_data'),

    path('settings/', views.SettingsView.as_view(), name='settings'),

    path('logout/', views.DashboardLogoutView.as_view(), name='logout'),
    path('password-change/', views.DashboardPasswordChangeView.as_view(), name='password_change'),
    path('password-change/done/', views.DashboardPasswordChangeDoneView.as_view(), name='password_change_done'),
]
