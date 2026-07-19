from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Category, Product, Testimonial, Order, OrderItem, ActivityLog, ShopSettings,
    CustomerProfile, HomePageContent, GamificationSettings, Review,
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_drink', 'product_count', 'created_at')
    list_filter = ('is_drink',)
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)

    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = 'Products'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('thumbnail', 'name', 'category', 'price', 'price_large', 'points', 'available', 'featured', 'created_at')
    list_filter = ('category', 'available', 'featured')
    list_editable = ('available', 'featured')
    search_fields = ('name', 'description', 'ingredients')
    prepopulated_fields = {'slug': ('name',)}
    autocomplete_fields = ('category',)
    fieldsets = (
        (None, {'fields': ('category', 'name', 'slug', 'description', 'ingredients')}),
        ('Pricing, Size & Media', {'fields': ('price', 'price_large', 'image')}),
        ('Visibility', {'fields': ('available', 'featured')}),
        ('Gamification', {'fields': ('points',)}),
    )

    def thumbnail(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="height:40px;width:40px;object-fit:cover;border-radius:6px;" />', obj.image.url)
        return "—"
    thumbnail.short_description = 'Image'


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ('customer_name', 'rating', 'active', 'created_at')
    list_filter = ('active', 'rating')
    list_editable = ('active',)
    search_fields = ('customer_name', 'quote')


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'product_name', 'size', 'unit_price', 'quantity', 'subtotal')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer_name', 'contact_number', 'dining_option', 'customer_user', 'total_amount', 'status_badge', 'created_at')
    list_filter = ('status', 'dining_option', 'created_at')
    list_editable = ()
    search_fields = ('customer_name', 'contact_number', 'id')
    readonly_fields = ('total_amount', 'customer_user', 'points_awarded', 'created_at', 'updated_at')
    inlines = [OrderItemInline]
    actions = ['mark_pending', 'mark_preparing', 'mark_ready', 'mark_completed', 'mark_cancelled']
    fieldsets = (
        ('Customer', {'fields': ('customer_name', 'contact_number', 'customer_user', 'dining_option', 'notes')}),
        ('Order Info', {'fields': ('status', 'total_amount', 'points_awarded', 'created_at', 'updated_at')}),
    )

    def status_badge(self, obj):
        colors = {
            'pending': '#f0ad4e',
            'preparing': '#5bc0de',
            'ready': '#6F4E37',
            'completed': '#5cb85c',
            'cancelled': '#d9534f',
        }
        color = colors.get(obj.status, '#999')
        return format_html(
            '<span style="background:{};color:white;padding:3px 10px;border-radius:12px;font-size:12px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def _bulk_update_status(self, request, queryset, status, label):
        updated = queryset.update(status=status)
        self.message_user(request, f"{updated} order(s) marked as {label}.")

    def mark_pending(self, request, queryset):
        self._bulk_update_status(request, queryset, Order.STATUS_PENDING, 'Pending')
    def mark_preparing(self, request, queryset):
        self._bulk_update_status(request, queryset, Order.STATUS_PREPARING, 'Preparing')
    def mark_ready(self, request, queryset):
        self._bulk_update_status(request, queryset, Order.STATUS_READY, 'Ready')
    def mark_completed(self, request, queryset):
        self._bulk_update_status(request, queryset, Order.STATUS_COMPLETED, 'Completed')
    def mark_cancelled(self, request, queryset):
        self._bulk_update_status(request, queryset, Order.STATUS_CANCELLED, 'Cancelled')

    mark_pending.short_description = "Mark selected orders as Pending"
    mark_preparing.short_description = "Mark selected orders as Preparing"
    mark_ready.short_description = "Mark selected orders as Ready"
    mark_completed.short_description = "Mark selected orders as Completed"
    mark_cancelled.short_description = "Mark selected orders as Cancelled"


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('description', 'action', 'created_at')
    list_filter = ('action',)
    search_fields = ('description',)
    readonly_fields = ('action', 'description', 'created_at')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(ShopSettings)
class ShopSettingsAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'email', 'updated_at')

    def has_add_permission(self, request):
        return not ShopSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(HomePageContent)
class HomePageContentAdmin(admin.ModelAdmin):
    list_display = ('hero_title', 'updated_at')

    def has_add_permission(self, request):
        return not HomePageContent.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(GamificationSettings)
class GamificationSettingsAdmin(admin.ModelAdmin):
    list_display = ('program_name', 'enabled', 'updated_at')

    def has_add_permission(self, request):
        return not GamificationSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'mobile_number', 'points', 'created_at')
    search_fields = ('full_name', 'mobile_number', 'user__username')
    readonly_fields = ('points',)
    filter_horizontal = ('favorites',)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('customer', 'product', 'rating', 'created_at')
    list_filter = ('rating',)
    search_fields = ('customer__full_name', 'comment')


admin.site.site_header = "Brew's Ko Administration"
admin.site.site_title = "Brew's Ko Admin"
admin.site.index_title = "Manage your coffee shop"
