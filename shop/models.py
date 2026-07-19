from django.conf import settings
from django.db import models
from django.urls import reverse
from django.core.validators import MinValueValidator, RegexValidator
from django.db.models.signals import post_save
from django.dispatch import receiver


PHONE_VALIDATOR = RegexValidator(
    regex=r'^[0-9+\-\s()]{7,20}$',
    message="Enter a valid contact number."
)


class ShopSettings(models.Model):
    """
    Singleton row holding the shop's public-facing info (name, address,
    contact details, hours, socials). Editable from the admin dashboard
    at /dashboard/settings/ — no backend/Django-admin access required.
    Everywhere the public site previously read settings.SHOP_*, it now
    reads this model via shop.context_processors.cart_summary.
    """
    name = models.CharField(max_length=150, default="Brew's Ko")
    address = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    hours = models.CharField(max_length=150, blank=True, help_text="e.g. Mon–Sun: 6:00 AM – 10:00 PM")
    facebook = models.URLField(blank=True)
    instagram = models.URLField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Shop Settings"
        verbose_name_plural = "Shop Settings"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Enforce a single row — this is a site-wide singleton.
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass  # the singleton row should never be deleted

    @classmethod
    def get_solo(cls):
        """Return the one ShopSettings row, seeding it from settings.py on first use."""
        from django.conf import settings as dj_settings
        obj, _created = cls.objects.get_or_create(pk=1, defaults={
            'name': getattr(dj_settings, 'SHOP_NAME', "Brew's Ko"),
            'address': getattr(dj_settings, 'SHOP_ADDRESS', ''),
            'phone': getattr(dj_settings, 'SHOP_PHONE', ''),
            'email': getattr(dj_settings, 'SHOP_EMAIL', ''),
            'hours': getattr(dj_settings, 'SHOP_HOURS', ''),
            'facebook': getattr(dj_settings, 'SHOP_FACEBOOK', ''),
            'instagram': getattr(dj_settings, 'SHOP_INSTAGRAM', ''),
        })
        return obj


class HomePageContent(models.Model):
    """
    Singleton controlling the editable text/images on the public homepage
    (hero + about sections). Edit at /dashboard/homepage/ — keeps the
    landing page future-proof without needing a code deploy for basic
    copy or photo changes.
    """
    hero_eyebrow = models.CharField(max_length=150, blank=True, default="Small-batch roasted, daily")
    hero_title = models.CharField(max_length=200, blank=True, default="Brewed with Passion, Served with Comfort.")
    hero_subtitle = models.CharField(max_length=255, blank=True,
                                      default="Discover handcrafted coffee and delightful treats at Brew's Ko.")
    hero_image = models.ImageField(upload_to='homepage/', blank=True, null=True)

    about_eyebrow = models.CharField(max_length=150, blank=True, default="Our Story")
    about_title = models.CharField(max_length=255, blank=True,
                                    default="A cup made with intention, in a place made for pause.")
    about_text_1 = models.TextField(
        blank=True,
        default="Brew's Ko began as a small corner counter with one espresso machine and a big dream: "
                "to give our community a warm space to slow down."
    )
    about_text_2 = models.TextField(
        blank=True,
        default="We believe great coffee shouldn't be rushed — thoughtfully sourced beans, patiently "
                "brewed, served in a space that feels like a warm hug on a busy day."
    )
    about_image = models.ImageField(upload_to='homepage/', blank=True, null=True)

    feature_1_icon = models.CharField(max_length=50, blank=True, default="bi-flower1")
    feature_1_title = models.CharField(max_length=100, blank=True, default="Ethically Sourced")
    feature_1_text = models.CharField(max_length=200, blank=True, default="Direct-trade beans from local farms")

    feature_2_icon = models.CharField(max_length=50, blank=True, default="bi-house-heart")
    feature_2_title = models.CharField(max_length=100, blank=True, default="Relaxing Atmosphere")
    feature_2_text = models.CharField(max_length=200, blank=True, default="A cozy space to work, chat, or unwind")

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Homepage Content"
        verbose_name_plural = "Homepage Content"

    def __str__(self):
        return "Homepage Content"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass

    @classmethod
    def get_solo(cls):
        obj, _created = cls.objects.get_or_create(pk=1)
        return obj


class GamificationSettings(models.Model):
    """
    Singleton toggle for the customer points/rewards program. While
    disabled, no point balances, hints, or history are shown anywhere on
    the customer-facing site — admin can flip it on once ready.
    """
    enabled = models.BooleanField(
        default=False,
        help_text="Turn on to reveal points to customers and start awarding them on completed orders."
    )
    program_name = models.CharField(max_length=100, blank=True, default="Brew's Ko Rewards")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Gamification Settings"
        verbose_name_plural = "Gamification Settings"

    def __str__(self):
        return self.program_name or "Gamification Settings"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass

    @classmethod
    def get_solo(cls):
        obj, _created = cls.objects.get_or_create(pk=1)
        return obj


class Category(models.Model):
    """Product category, e.g. Espresso, Latte, Pastries."""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=110, unique=True, blank=True,
                             help_text="Auto-generated from name if left blank.")
    description = models.TextField(blank=True)
    icon = models.CharField(
        max_length=50, blank=True,
        help_text="Optional Bootstrap Icon class, e.g. 'bi-cup-hot'."
    )
    is_drink = models.BooleanField(
        default=True,
        help_text="Uncheck for non-drink categories (e.g. pastries) — controls whether size options are shown."
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('shop:menu') + f'?category={self.slug}'


class Product(models.Model):
    """A single menu item. Drinks can have both Regular and Large sizes
    available at once (each with its own price, set by the admin) — the
    customer picks the size when adding to cart, not the admin."""
    SIZE_REGULAR = 'regular'
    SIZE_LARGE = 'large'
    SIZE_CHOICES = [
        (SIZE_REGULAR, 'Regular'),
        (SIZE_LARGE, 'Large'),
    ]

    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name='products'
    )
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=170, unique=True, blank=True)
    description = models.TextField(blank=True)
    ingredients = models.TextField(
        blank=True,
        help_text="e.g. Espresso, Steamed Milk, Vanilla Syrup. Shown on the product detail page."
    )
    price = models.DecimalField(
        max_digits=8, decimal_places=2, validators=[MinValueValidator(0)],
        help_text="Regular size price (or the only price, for non-drink items)."
    )
    price_large = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)],
        help_text="Large size price. Required for drink categories — Regular and Large are both always offered."
    )
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    available = models.BooleanField(default=True, help_text="Uncheck to hide from the menu.")
    featured = models.BooleanField(default=False, help_text="Show on the homepage's Featured section.")
    points = models.PositiveIntegerField(
        default=0,
        help_text="Gamification points a customer earns per unit ordered (admin-assigned)."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category__name', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                counter += 1
                slug = f"{base_slug}-{counter}"
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('shop:product_detail', kwargs={'slug': self.slug})

    @property
    def ingredient_list(self):
        return [i.strip() for i in self.ingredients.split(',') if i.strip()]

    @property
    def has_large_option(self):
        return bool(self.category.is_drink and self.price_large)

    def price_for_size(self, size):
        if size == self.SIZE_LARGE and self.price_large:
            return self.price_large
        return self.price

    @classmethod
    def size_label(cls, size):
        return dict(cls.SIZE_CHOICES).get(size, '')

    @property
    def average_rating(self):
        avg = self.reviews.aggregate(avg=models.Avg('rating'))['avg']
        return round(avg, 1) if avg else 0

    @property
    def review_count(self):
        return self.reviews.count()


class Testimonial(models.Model):
    """Customer review shown on the homepage."""
    customer_name = models.CharField(max_length=100)
    quote = models.TextField()
    rating = models.PositiveSmallIntegerField(
        default=5, validators=[MinValueValidator(1)],
        help_text="1 to 5 stars"
    )
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.customer_name} ({self.rating}★)"


class CustomerProfile(models.Model):
    """
    Extends Django's built-in User model for the 'customer' user type.
    Created automatically on signup (see shop.views.signup). Distinct
    from staff/admin accounts (is_staff=True, no profile) and from
    anonymous guests (no account/session cart only).
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='customer_profile'
    )
    full_name = models.CharField(max_length=150)
    mobile_number = models.CharField(max_length=20, validators=[PHONE_VALIDATOR])
    photo = models.ImageField(upload_to='customers/', blank=True, null=True)
    favorites = models.ManyToManyField(Product, blank=True, related_name='favorited_by')
    points = models.PositiveIntegerField(default=0, help_text="Gamification points balance.")
    cart_data = models.JSONField(default=dict, blank=True, help_text="Persisted cart contents — survives logout/login.")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Customer Profile"
        verbose_name_plural = "Customer Profiles"

    def __str__(self):
        return self.full_name or self.user.username

    @property
    def orders(self):
        return self.user.orders.all()

    @property
    def total_orders(self):
        return self.orders.count()

    @property
    def total_spent(self):
        return self.orders.exclude(status='cancelled').aggregate(
            total=models.Sum('total_amount')
        )['total'] or 0

    @property
    def favorite_count(self):
        return self.favorites.count()


class Review(models.Model):
    """
    A star rating + comment left by a customer, for either a specific
    product (product set) or the coffee shop overall (product left null).
    Only customers can leave these — guests and staff never do, and this
    is enforced at the view layer (see shop.views.add_review).
    """
    customer = models.ForeignKey(CustomerProfile, on_delete=models.CASCADE, related_name='reviews')
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, null=True, blank=True, related_name='reviews',
        help_text="Leave blank for a store-wide review of Brew's Ko itself."
    )
    rating = models.PositiveSmallIntegerField(default=5, validators=[MinValueValidator(1)], help_text="1 to 5 stars")
    comment = models.TextField()
    image = models.ImageField(upload_to='reviews/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        target = self.product.name if self.product else "Brew's Ko"
        return f"{self.customer.full_name} on {target} ({self.rating}★)"

    @property
    def is_store_review(self):
        return self.product_id is None


class Order(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_PREPARING = 'preparing'
    STATUS_READY = 'ready'
    STATUS_COMPLETED = 'completed'
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_PREPARING, 'Preparing'),
        (STATUS_READY, 'Ready'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    DINING_FOR_HERE = 'for_here'
    DINING_TO_GO = 'to_go'
    DINING_CHOICES = [
        (DINING_FOR_HERE, 'For Here'),
        (DINING_TO_GO, 'To Go'),
    ]

    customer_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='orders', help_text="Set automatically when a signed-in customer checks out."
    )
    customer_name = models.CharField(max_length=150)
    contact_number = models.CharField(max_length=20, validators=[PHONE_VALIDATOR])
    dining_option = models.CharField(max_length=10, choices=DINING_CHOICES, default=DINING_TO_GO)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    notes = models.TextField(blank=True, help_text="Optional special instructions from the customer.")
    points_awarded = models.BooleanField(default=False, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.pk} — {self.customer_name} ({self.get_status_display()})"

    def recalculate_total(self):
        total = sum((item.subtotal for item in self.items.all()), start=0)
        self.total_amount = total
        self.save(update_fields=['total_amount'])


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, related_name='order_items')
    product_name = models.CharField(max_length=150, blank=True, help_text="Snapshot of product name at order time.")
    size = models.CharField(max_length=10, choices=Product.SIZE_CHOICES, blank=True,
                             help_text="Snapshot of the size ordered.")
    unit_price = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.quantity} x {self.product_name or (self.product.name if self.product else 'Product')}"

    def save(self, *args, **kwargs):
        if self.product and not self.product_name:
            self.product_name = self.product.name
        if self.product and not self.unit_price:
            self.unit_price = self.product.price_for_size(self.size)
        self.subtotal = self.unit_price * self.quantity
        super().save(*args, **kwargs)


class ActivityLog(models.Model):
    """
    Lightweight audit trail powering the 'Recent Activity' feed on the
    admin dashboard. Entries are created automatically via signals below.
    """
    ACTION_PRODUCT_ADDED = 'product_added'
    ACTION_PRODUCT_UPDATED = 'product_updated'
    ACTION_CATEGORY_ADDED = 'category_added'
    ACTION_CATEGORY_UPDATED = 'category_updated'
    ACTION_ORDER_RECEIVED = 'order_received'
    ACTION_ORDER_COMPLETED = 'order_completed'
    ACTION_ORDER_UPDATED = 'order_updated'
    ACTION_CUSTOMER_JOINED = 'customer_joined'

    ACTION_CHOICES = [
        (ACTION_PRODUCT_ADDED, 'Product added'),
        (ACTION_PRODUCT_UPDATED, 'Product updated'),
        (ACTION_CATEGORY_ADDED, 'Category added'),
        (ACTION_CATEGORY_UPDATED, 'Category updated'),
        (ACTION_ORDER_RECEIVED, 'Order received'),
        (ACTION_ORDER_COMPLETED, 'Order completed'),
        (ACTION_ORDER_UPDATED, 'Order updated'),
        (ACTION_CUSTOMER_JOINED, 'Customer joined'),
    ]

    ACTION_ICONS = {
        ACTION_PRODUCT_ADDED: 'bi-bag-plus-fill',
        ACTION_PRODUCT_UPDATED: 'bi-pencil-square',
        ACTION_CATEGORY_ADDED: 'bi-tags-fill',
        ACTION_CATEGORY_UPDATED: 'bi-tags',
        ACTION_ORDER_RECEIVED: 'bi-receipt',
        ACTION_ORDER_COMPLETED: 'bi-check2-circle',
        ACTION_ORDER_UPDATED: 'bi-arrow-repeat',
        ACTION_CUSTOMER_JOINED: 'bi-person-plus-fill',
    }

    action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    description = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Activity Log'
        verbose_name_plural = 'Activity Logs'

    def __str__(self):
        return self.description

    @property
    def icon(self):
        return self.ACTION_ICONS.get(self.action, 'bi-clock-history')


# ---------------------------------------------------------------------------
# Signals — automatically populate the ActivityLog feed used by the
# admin dashboard's "Recent Activity" section, and award gamification
# points when a customer's order is marked completed.
# ---------------------------------------------------------------------------

@receiver(post_save, sender=Category)
def log_category_activity(sender, instance, created, **kwargs):
    ActivityLog.objects.create(
        action=ActivityLog.ACTION_CATEGORY_ADDED if created else ActivityLog.ACTION_CATEGORY_UPDATED,
        description=f"Category '{instance.name}' was {'added' if created else 'updated'}.",
    )


@receiver(post_save, sender=Product)
def log_product_activity(sender, instance, created, **kwargs):
    ActivityLog.objects.create(
        action=ActivityLog.ACTION_PRODUCT_ADDED if created else ActivityLog.ACTION_PRODUCT_UPDATED,
        description=f"Product '{instance.name}' was {'added to the menu' if created else 'updated'}.",
    )


@receiver(post_save, sender=CustomerProfile)
def log_customer_activity(sender, instance, created, **kwargs):
    if created:
        ActivityLog.objects.create(
            action=ActivityLog.ACTION_CUSTOMER_JOINED,
            description=f"New customer '{instance.full_name}' signed up.",
        )


@receiver(post_save, sender=Order)
def log_order_activity(sender, instance, created, **kwargs):
    # Skip the internal save triggered by recalculate_total() right after
    # order creation — it only touches total_amount, not the status.
    update_fields = kwargs.get('update_fields')
    if not created and update_fields and set(update_fields) == {'total_amount'}:
        return

    if created:
        ActivityLog.objects.create(
            action=ActivityLog.ACTION_ORDER_RECEIVED,
            description=f"New order #{instance.pk} received from {instance.customer_name}.",
        )
    elif instance.status == Order.STATUS_COMPLETED:
        ActivityLog.objects.create(
            action=ActivityLog.ACTION_ORDER_COMPLETED,
            description=f"Order #{instance.pk} ({instance.customer_name}) marked as completed.",
        )
    else:
        ActivityLog.objects.create(
            action=ActivityLog.ACTION_ORDER_UPDATED,
            description=f"Order #{instance.pk} ({instance.customer_name}) updated to '{instance.get_status_display()}'.",
        )


@receiver(post_save, sender=Order)
def award_points_on_completion(sender, instance, created, **kwargs):
    """
    When a signed-in customer's order is marked Completed, credit their
    profile with points (product.points * quantity, summed across items).
    No-ops entirely while gamification is disabled or for guest orders.
    `points_awarded` prevents double-crediting if the order is saved again.
    """
    if created or instance.status != Order.STATUS_COMPLETED or instance.points_awarded:
        return
    if not instance.customer_user_id:
        return
    if not GamificationSettings.get_solo().enabled:
        return

    try:
        profile = instance.customer_user.customer_profile
    except CustomerProfile.DoesNotExist:
        return

    total_points = sum(
        (item.product.points * item.quantity) for item in instance.items.select_related('product').all()
        if item.product_id
    )
    if total_points:
        CustomerProfile.objects.filter(pk=profile.pk).update(points=models.F('points') + total_points)

    # .update() bypasses save()/signals entirely — no recursive post_save here.
    Order.objects.filter(pk=instance.pk).update(points_awarded=True)
