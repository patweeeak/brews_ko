"""
Admin Dashboard views for Brew's Ko.

Everything here is gated behind StaffRequiredMixin so that only
authenticated staff/superuser accounts can reach /dashboard/. Anyone
else is bounced to the Django admin login page (settings.LOGIN_URL),
with ?next= pointing back to the page they tried to open.
"""
import json
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Sum, Count, Q, F, DecimalField
from django.db.models.functions import Coalesce
from django.http import JsonResponse
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import TemplateView, ListView, DetailView, CreateView, UpdateView, View

from .models import (
    Category, Product, Order, OrderItem, ActivityLog, ShopSettings,
    HomePageContent, GamificationSettings, CustomerProfile, Review,
)
from .dashboard_forms import (
    ProductForm, CategoryForm, OrderStatusForm, ShopSettingsForm,
    HomePageContentForm, GamificationSettingsForm,
)


class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Only staff/superuser accounts may access the dashboard."""
    login_url = '/admin/login/'
    redirect_field_name = 'next'

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_staff

    def handle_no_permission(self):
        if self.request.user.is_authenticated and not self.request.user.is_staff:
            messages.error(self.request, "You don't have permission to access the admin dashboard.")
            return redirect('shop:home')
        return super().handle_no_permission()


ZERO_DECIMAL = DecimalField(max_digits=10, decimal_places=2)


def _revenue(qs):
    return qs.exclude(status=Order.STATUS_CANCELLED).aggregate(
        total=Coalesce(Sum('total_amount'), 0, output_field=ZERO_DECIMAL)
    )['total']


VALID_PERIODS = {'daily', 'weekly', 'monthly', 'annual'}
PERIOD_LABELS = {'daily': 'Today', 'weekly': 'Last 7 Days', 'monthly': 'This Month', 'annual': 'This Year'}


def _month_start(dt, offset=0):
    """First moment of the month `offset` months before dt's month (offset=0 == dt's own month)."""
    total = dt.year * 12 + (dt.month - 1) - offset
    year, month = divmod(total, 12)
    return dt.replace(year=year, month=month + 1, day=1, hour=0, minute=0, second=0, microsecond=0)


def get_period_window(period):
    """
    Single filter window for the 'Revenue by Category' / 'Top Selling Products'
    panels — e.g. period='weekly' -> (start of last 7 days, now).
    """
    now = timezone.localtime()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    if period not in VALID_PERIODS:
        period = 'monthly'

    if period == 'daily':
        start = today
    elif period == 'weekly':
        start = today - timedelta(days=6)
    elif period == 'annual':
        start = today.replace(month=1, day=1)
    else:
        start = today.replace(day=1)
    return start, now, PERIOD_LABELS[period], period


def get_trend_buckets(period):
    """
    A list of (label, start, end) buckets for the 'Revenue' trend chart —
    e.g. period='daily' -> the last 7 individual days; period='annual' ->
    the last 5 calendar years.
    """
    now = timezone.localtime()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    if period not in VALID_PERIODS:
        period = 'monthly'

    if period == 'daily':
        edges = [today - timedelta(days=d) for d in range(6, -1, -1)] + [today + timedelta(days=1)]
        fmt = lambda d: d.strftime('%a %d')
    elif period == 'weekly':
        week_start = today - timedelta(days=today.weekday())
        edges = [week_start - timedelta(weeks=w) for w in range(7, -1, -1)] + [week_start + timedelta(weeks=1)]
        fmt = lambda d: 'Wk of ' + d.strftime('%b %d')
    elif period == 'annual':
        edges = [today.replace(month=1, day=1, year=today.year - y) for y in range(4, -1, -1)]
        edges.append(today.replace(month=1, day=1, year=today.year + 1))
        fmt = lambda d: str(d.year)
    else:
        period = 'monthly'
        edges = [_month_start(today, i) for i in range(5, -1, -1)] + [_month_start(today, -1)]
        fmt = lambda d: d.strftime('%b %Y')

    return [(fmt(edges[i]), edges[i], edges[i + 1]) for i in range(len(edges) - 1)], period


class DashboardView(StaffRequiredMixin, TemplateView):
    template_name = 'dashboard/index.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        now = timezone.localtime()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=7)
        month_start = today_start.replace(day=1)

        orders = Order.objects.all()

        status_counts = {
            row['status']: row['n'] for row in orders.values('status').annotate(n=Count('id'))
        }

        products = Product.objects.all()
        categories = Category.objects.all()

        # ---- Stat cards ----
        ctx['stats'] = {
            'total_orders': orders.count(),
            'pending_orders': status_counts.get(Order.STATUS_PENDING, 0),
            'preparing_orders': status_counts.get(Order.STATUS_PREPARING, 0),
            'ready_orders': status_counts.get(Order.STATUS_READY, 0),
            'completed_orders': status_counts.get(Order.STATUS_COMPLETED, 0),
            'cancelled_orders': status_counts.get(Order.STATUS_CANCELLED, 0),
            'total_products': products.count(),
            'total_categories': categories.count(),
            'featured_products': products.filter(featured=True).count(),
            'todays_orders': orders.filter(created_at__gte=today_start).count(),
        }

        # ---- Revenue ----
        ctx['revenue'] = {
            'today': _revenue(orders.filter(created_at__gte=today_start)),
            'weekly': _revenue(orders.filter(created_at__gte=week_start)),
            'monthly': _revenue(orders.filter(created_at__gte=month_start)),
            'total': _revenue(orders),
        }

        # ---- Recent orders (newest first) ----
        ctx['recent_orders'] = orders.select_related().order_by('-created_at')[:10]

        # ---- Product management overview ----
        ctx['product_overview'] = {
            'total': products.count(),
            'available': products.filter(available=True).count(),
            'unavailable': products.filter(available=False).count(),
            'featured': products.filter(featured=True).count(),
        }
        ctx['category_overview'] = {'total': categories.count()}

        # ---- Order status chart data ----
        ctx['status_chart_labels'] = json.dumps(
            ['Pending', 'Preparing', 'Ready', 'Completed', 'Cancelled']
        )
        ctx['status_chart_data'] = json.dumps([
            status_counts.get(Order.STATUS_PENDING, 0),
            status_counts.get(Order.STATUS_PREPARING, 0),
            status_counts.get(Order.STATUS_READY, 0),
            status_counts.get(Order.STATUS_COMPLETED, 0),
            status_counts.get(Order.STATUS_CANCELLED, 0),
        ])

        # ---- Weekly revenue trend (last 7 days) for the line chart ----
        day_labels, day_totals = [], []
        for i in range(6, -1, -1):
            day = today_start - timedelta(days=i)
            day_end = day + timedelta(days=1)
            day_labels.append(day.strftime('%a'))
            day_totals.append(float(_revenue(orders.filter(created_at__gte=day, created_at__lt=day_end))))
        ctx['trend_labels'] = json.dumps(day_labels)
        ctx['trend_data'] = json.dumps(day_totals)

        # ---- Best selling products (top 5, excludes cancelled orders) ----
        ctx['best_sellers'] = (
            OrderItem.objects
            .exclude(order__status=Order.STATUS_CANCELLED)
            .values('product_name')
            .annotate(qty_sold=Sum('quantity'), revenue=Sum(F('unit_price') * F('quantity')))
            .order_by('-qty_sold')[:5]
        )

        # ---- Recent activity feed ----
        ctx['recent_activity'] = ActivityLog.objects.all()[:10]

        return ctx


class OrderListView(StaffRequiredMixin, ListView):
    model = Order
    template_name = 'dashboard/orders.html'
    context_object_name = 'orders'
    paginate_by = 15

    def get_queryset(self):
        qs = Order.objects.all().order_by('-created_at')
        status = self.request.GET.get('status', '')
        query = self.request.GET.get('q', '').strip()
        if status:
            qs = qs.filter(status=status)
        if query:
            qs = qs.filter(
                Q(customer_name__icontains=query) |
                Q(contact_number__icontains=query) |
                Q(id__iexact=query if query.isdigit() else -1)
            )
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['status_choices'] = Order.STATUS_CHOICES
        ctx['selected_status'] = self.request.GET.get('status', '')
        ctx['query'] = self.request.GET.get('q', '')
        return ctx


class OrderDetailView(StaffRequiredMixin, DetailView):
    model = Order
    template_name = 'dashboard/order_detail.html'
    context_object_name = 'order'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['status_form'] = OrderStatusForm(instance=self.object)
        return ctx

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = OrderStatusForm(request.POST, instance=self.object)
        if form.is_valid():
            form.save()
            messages.success(request, f"Order #{self.object.id} status updated to '{self.object.get_status_display()}'.")
            return redirect('dashboard:order_detail', pk=self.object.pk)
        messages.error(request, "Couldn't update the order status. Please try again.")
        ctx = self.get_context_data(status_form=form)
        return self.render_to_response(ctx)


class ProductListView(StaffRequiredMixin, ListView):
    model = Product
    template_name = 'dashboard/products.html'
    context_object_name = 'products'
    paginate_by = 20

    def get_queryset(self):
        qs = Product.objects.select_related('category').order_by('category__name', 'name')
        query = self.request.GET.get('q', '').strip()
        availability = self.request.GET.get('availability', '')
        if query:
            qs = qs.filter(Q(name__icontains=query) | Q(description__icontains=query))
        if availability == 'available':
            qs = qs.filter(available=True)
        elif availability == 'unavailable':
            qs = qs.filter(available=False)
        elif availability == 'featured':
            qs = qs.filter(featured=True)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['query'] = self.request.GET.get('q', '')
        ctx['availability'] = self.request.GET.get('availability', '')
        ctx['product_overview'] = {
            'total': Product.objects.count(),
            'available': Product.objects.filter(available=True).count(),
            'unavailable': Product.objects.filter(available=False).count(),
            'featured': Product.objects.filter(featured=True).count(),
        }
        return ctx


class CategoryListView(StaffRequiredMixin, ListView):
    model = Category
    template_name = 'dashboard/categories.html'
    context_object_name = 'categories'

    def get_queryset(self):
        return Category.objects.annotate(product_count=Count('products')).order_by('name')


class CustomerListView(StaffRequiredMixin, TemplateView):
    template_name = 'dashboard/customers.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        customers = (
            Order.objects
            .values('customer_name', 'contact_number')
            .annotate(
                order_count=Count('id'),
                total_spent=Coalesce(
                    Sum('total_amount', filter=~Q(status=Order.STATUS_CANCELLED)), 0,
                    output_field=ZERO_DECIMAL
                ),
            )
            .order_by('-order_count')
        )
        # Attach the most recent order date per customer (small dataset friendly).
        customers = list(customers)
        for c in customers:
            last = (
                Order.objects.filter(
                    customer_name=c['customer_name'], contact_number=c['contact_number']
                ).order_by('-created_at').first()
            )
            c['last_order_date'] = last.created_at if last else None
        ctx['customers'] = customers
        ctx['total_customers'] = len(customers)

        ctx['registered_customers'] = (
            CustomerProfile.objects
            .select_related('user')
            .annotate(fav_count=Count('favorites', distinct=True), order_count=Count('user__orders', distinct=True))
            .order_by('-points')
        )
        return ctx


class ReportsView(StaffRequiredMixin, TemplateView):
    template_name = 'dashboard/reports.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        # ---- Revenue trend chart (default: monthly buckets) ----
        buckets, _ = get_trend_buckets('monthly')
        orders = Order.objects.all()
        ctx['revenue_labels'] = json.dumps([b[0] for b in buckets])
        ctx['revenue_data'] = json.dumps([
            float(_revenue(orders.filter(created_at__gte=b[1], created_at__lt=b[2]))) for b in buckets
        ])

        # ---- Revenue by category (default: this month) ----
        start, end, _, _ = get_period_window('monthly')
        ctx['revenue_by_category'] = _category_revenue_rows(start, end)

        # ---- Top selling products (default: this month) ----
        ctx['best_sellers'] = _top_products_rows(start, end)[:10]

        ctx['total_revenue'] = _revenue(Order.objects.all())
        return ctx


def _category_revenue_rows(start, end):
    rows = (
        OrderItem.objects
        .exclude(order__status=Order.STATUS_CANCELLED)
        .filter(order__created_at__gte=start, order__created_at__lte=end)
        .values(cat=F('product__category__name'))
        .annotate(revenue=Sum(F('unit_price') * F('quantity')), qty=Sum('quantity'))
        .order_by('-revenue')
    )
    return list(rows)


def _top_products_rows(start, end):
    rows = (
        OrderItem.objects
        .exclude(order__status=Order.STATUS_CANCELLED)
        .filter(order__created_at__gte=start, order__created_at__lte=end)
        .values('product_name')
        .annotate(qty_sold=Sum('quantity'), revenue=Sum(F('unit_price') * F('quantity')))
        .order_by('-qty_sold')
    )
    return list(rows)


class RevenueTrendDataView(StaffRequiredMixin, View):
    """JSON data for the Reports page 'Revenue' panel dropdown (daily/weekly/monthly/annual)."""

    def get(self, request, *args, **kwargs):
        buckets, period = get_trend_buckets(request.GET.get('period', 'monthly'))
        orders = Order.objects.all()
        labels = [b[0] for b in buckets]
        data = [float(_revenue(orders.filter(created_at__gte=b[1], created_at__lt=b[2]))) for b in buckets]
        return JsonResponse({'period': period, 'labels': labels, 'data': data})


class CategoryRevenueDataView(StaffRequiredMixin, View):
    """JSON data for the Reports page 'Revenue by Category' panel dropdown."""

    def get(self, request, *args, **kwargs):
        start, end, window_label, period = get_period_window(request.GET.get('period', 'monthly'))
        rows = _category_revenue_rows(start, end)
        data = [{
            'category': r['cat'] or 'Uncategorized',
            'qty': r['qty'] or 0,
            'revenue': float(r['revenue'] or 0),
        } for r in rows]
        return JsonResponse({'period': period, 'window_label': window_label, 'rows': data})


class TopProductsDataView(StaffRequiredMixin, View):
    """JSON data for the Reports page 'Top Selling Products' panel dropdown."""

    def get(self, request, *args, **kwargs):
        start, end, window_label, period = get_period_window(request.GET.get('period', 'monthly'))
        rows = _top_products_rows(start, end)[:10]
        data = [{
            'product_name': r['product_name'],
            'qty_sold': r['qty_sold'] or 0,
            'revenue': float(r['revenue'] or 0),
        } for r in rows]
        return JsonResponse({'period': period, 'window_label': window_label, 'rows': data})


class SettingsView(StaffRequiredMixin, UpdateView):
    model = ShopSettings
    form_class = ShopSettingsForm
    template_name = 'dashboard/settings.html'
    success_url = reverse_lazy('dashboard:settings')

    def get_object(self, queryset=None):
        return ShopSettings.get_solo()

    def form_valid(self, form):
        messages.success(self.request, "Shop information updated successfully.")
        return super().form_valid(form)


# ---------------------------------------------------------------------------
# Product CRUD — fully native to the dashboard (no Django-admin links)
# ---------------------------------------------------------------------------

class ProductCreateView(StaffRequiredMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'dashboard/product_form.html'
    success_url = reverse_lazy('dashboard:products')

    def form_valid(self, form):
        messages.success(self.request, f"Product '{form.instance.name}' was added to the menu.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['is_edit'] = False
        return ctx


class ProductUpdateView(StaffRequiredMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'dashboard/product_form.html'
    success_url = reverse_lazy('dashboard:products')

    def form_valid(self, form):
        messages.success(self.request, f"Product '{form.instance.name}' was updated.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['is_edit'] = True
        return ctx


# ---------------------------------------------------------------------------
# Category CRUD — fully native to the dashboard
# ---------------------------------------------------------------------------

class CategoryCreateView(StaffRequiredMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = 'dashboard/category_form.html'
    success_url = reverse_lazy('dashboard:categories')

    def form_valid(self, form):
        messages.success(self.request, f"Category '{form.instance.name}' was added.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['is_edit'] = False
        return ctx


class CategoryUpdateView(StaffRequiredMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = 'dashboard/category_form.html'
    success_url = reverse_lazy('dashboard:categories')

    def form_valid(self, form):
        messages.success(self.request, f"Category '{form.instance.name}' was updated.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['is_edit'] = True
        return ctx


# ---------------------------------------------------------------------------
# Auth — dashboard-scoped logout & password change (never touches /admin/)
# ---------------------------------------------------------------------------

class DashboardLogoutView(auth_views.LogoutView):
    """POST-only logout that sends the staff member back to the public site."""
    next_page = reverse_lazy('shop:home')


class DashboardPasswordChangeView(StaffRequiredMixin, auth_views.PasswordChangeView):
    template_name = 'dashboard/password_change_form.html'
    success_url = reverse_lazy('dashboard:password_change_done')


class DashboardPasswordChangeDoneView(StaffRequiredMixin, auth_views.PasswordChangeDoneView):
    template_name = 'dashboard/password_change_done.html'


# ---------------------------------------------------------------------------
# Homepage CMS — hero/about text + images. The "testimonials" shown on
# the public homepage are now sourced live from real customer Review
# records (see shop.views.home) rather than manually-typed fake quotes.
# ---------------------------------------------------------------------------

class HomePageContentUpdateView(StaffRequiredMixin, UpdateView):
    model = HomePageContent
    form_class = HomePageContentForm
    template_name = 'dashboard/homepage.html'
    success_url = reverse_lazy('dashboard:homepage')

    def get_object(self, queryset=None):
        return HomePageContent.get_solo()

    def form_valid(self, form):
        messages.success(self.request, "Homepage content updated — changes are live now.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['reviews'] = Review.objects.select_related('customer', 'product').order_by('-created_at')[:30]
        return ctx


class ReviewDeleteView(StaffRequiredMixin, View):
    """POST-only: remove an inappropriate customer review (product or store)."""

    def post(self, request, pk):
        get_object_or_404(Review, pk=pk).delete()
        messages.success(request, "Review deleted.")
        return redirect('dashboard:homepage')


# ---------------------------------------------------------------------------
# Gamification — enable/disable the customer points program and assign
# per-product point values. Nothing here is ever visible to customers
# unless GamificationSettings.enabled is True.
# ---------------------------------------------------------------------------

class GamificationView(StaffRequiredMixin, TemplateView):
    template_name = 'dashboard/gamification.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.setdefault('settings_form', GamificationSettingsForm(instance=GamificationSettings.get_solo()))
        ctx['gamification'] = GamificationSettings.get_solo()
        ctx['products'] = Product.objects.select_related('category').order_by('category__name', 'name')
        ctx['top_earners'] = CustomerProfile.objects.select_related('user').order_by('-points')[:10]
        return ctx

    def post(self, request, *args, **kwargs):
        form_type = request.POST.get('form_type')

        if form_type == 'settings':
            instance = GamificationSettings.get_solo()
            form = GamificationSettingsForm(request.POST, instance=instance)
            if form.is_valid():
                form.save()
                messages.success(request, "Gamification settings updated.")
                return redirect('dashboard:gamification')
            return self.render_to_response(self.get_context_data(settings_form=form))

        if form_type == 'points':
            updated = 0
            for key, value in request.POST.items():
                if not key.startswith('points_'):
                    continue
                try:
                    product_id = int(key.split('_', 1)[1])
                    points = max(int(value), 0)
                except (ValueError, IndexError):
                    continue
                Product.objects.filter(pk=product_id).update(points=points)
                updated += 1
            messages.success(request, f"Updated points for {updated} product(s).")
            return redirect('dashboard:gamification')

        messages.error(request, "Unrecognized form submission.")
        return redirect('dashboard:gamification')
