from django.core.management.base import BaseCommand
from django.db import transaction
from shop.models import Category, Product, Testimonial


CATEGORY_DATA = [
    ("Espresso", "bi-cup-hot", "Bold, concentrated shots pulled from our house blend."),
    ("Latte", "bi-cup", "Silky steamed milk meets rich espresso."),
    ("Cappuccino", "bi-cup-straw", "Equal parts espresso, steamed milk, and foam."),
    ("Iced Coffee", "bi-snow", "Chilled and refreshing, brewed for warm days."),
    ("Signature Drinks", "bi-stars", "Brew's Ko originals you won't find anywhere else."),
    ("Non-Coffee", "bi-cup-hot-fill", "Teas, chocolates, and other cozy sips."),
    ("Pastries", "bi-egg-fried", "Baked fresh every morning in-house."),
    ("Desserts", "bi-cake2", "Sweet endings to any coffee run."),
]

PRODUCT_DATA = {
    "Espresso": [
        ("Classic Espresso", "A double shot of our signature house blend.", 95, True),
        ("Espresso Macchiato", "Espresso 'stained' with a dollop of foam.", 105, False),
        ("Ristretto", "A shorter, more concentrated espresso pull.", 100, False),
    ],
    "Latte": [
        ("Caffe Latte", "Smooth espresso with steamed milk and a whisper of foam.", 135, True),
        ("Vanilla Latte", "Our classic latte sweetened with vanilla syrup.", 145, False),
        ("Honey Oat Latte", "Espresso with oat milk and local honey.", 155, True),
    ],
    "Cappuccino": [
        ("Classic Cappuccino", "Rich espresso balanced with velvety foam.", 130, False),
        ("Cinnamon Cappuccino", "A dusting of cinnamon over our classic cappuccino.", 140, False),
    ],
    "Iced Coffee": [
        ("Iced Americano", "Espresso over ice with cold water, crisp and bold.", 120, True),
        ("Iced Caramel Macchiato", "Vanilla, milk, espresso, and caramel drizzle over ice.", 160, True),
        ("Cold Brew", "Slow-steeped for 18 hours, smooth and low-acid.", 150, False),
    ],
    "Signature Drinks": [
        ("Brew's Ko Special", "Our house signature — espresso, brown sugar, oat milk.", 175, True),
        ("Salted Caramel Cloud", "Espresso topped with whipped salted caramel foam.", 180, False),
    ],
    "Non-Coffee": [
        ("Matcha Latte", "Ceremonial-grade matcha whisked with steamed milk.", 150, False),
        ("Hot Chocolate", "Rich Belgian chocolate, steamed to perfection.", 140, False),
        ("Chamomile Tea", "A calming, caffeine-free herbal blend.", 110, False),
    ],
    "Pastries": [
        ("Butter Croissant", "Flaky, buttery, baked fresh every morning.", 85, True),
        ("Pain au Chocolat", "Buttery pastry wrapped around dark chocolate.", 95, False),
        ("Blueberry Muffin", "Studded with real blueberries, soft and moist.", 90, False),
    ],
    "Desserts": [
        ("Basque Burnt Cheesecake", "Caramelized top, creamy center.", 150, True),
        ("Tiramisu Cup", "Espresso-soaked ladyfingers layered with mascarpone.", 145, False),
    ],
}

TESTIMONIALS = [
    ("Ana Reyes", "Brew's Ko is my go-to spot before work — the oat milk latte never disappoints!", 5),
    ("Miguel Santos", "Cozy atmosphere, friendly staff, and the best cold brew in the city.", 5),
    ("Carla Dizon", "Their pastries are always fresh and the espresso is perfectly balanced.", 5),
    ("Paolo Ramos", "I love working here in the afternoons. Great wifi, great coffee.", 4),
    ("Jasmine Uy", "The Brew's Ko Special is unreal. Ordering online made it so easy too.", 5),
]


class Command(BaseCommand):
    help = "Seed the database with sample categories, products, and testimonials."

    @transaction.atomic
    def handle(self, *args, **options):
        for name, icon, description in CATEGORY_DATA:
            category, created = Category.objects.get_or_create(
                name=name, defaults={'icon': icon, 'description': description}
            )
            products = PRODUCT_DATA.get(name, [])
            for pname, pdesc, price, featured in products:
                Product.objects.get_or_create(
                    name=pname,
                    defaults={
                        'category': category,
                        'description': pdesc,
                        'price': price,
                        'featured': featured,
                        'available': True,
                    }
                )

        for cname, quote, rating in TESTIMONIALS:
            Testimonial.objects.get_or_create(
                customer_name=cname, defaults={'quote': quote, 'rating': rating}
            )

        self.stdout.write(self.style.SUCCESS(
            f"Seeded {Category.objects.count()} categories, "
            f"{Product.objects.count()} products, "
            f"{Testimonial.objects.count()} testimonials."
        ))
