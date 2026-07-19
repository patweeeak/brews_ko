# Brew's Ko — Coffee Shop Website

A complete, mobile-first Django website for a coffee shop, built with Django 6, Bootstrap 5,
vanilla JavaScript (Intersection Observer scroll reveal), and SQLite.

## ✨ Features

- **No customer accounts** — browse, add to cart, and check out with just a name + contact number.
- **Home page** — hero, about/philosophy, featured products, testimonials, location & hours.
- **Menu page** — category chips, live search, animated product cards (fade + slide up on scroll).
- **Product detail page** — quantity selector, related products.
- **Session-based cart** — add / update / remove items, no login required.
- **Checkout** — collects Full Name + Contact Number, creates an `Order` with `OrderItem`s.
- **Django Admin** — manage Categories, Products, Testimonials, and Orders (with status: Pending →
  Preparing → Ready → Completed / Cancelled, plus bulk status actions).
- **Branded admin login page** — `/admin/login/` uses a custom template (`templates/admin/login.html`)
  styled to match the storefront instead of Django's plain default screen.
- Warm coffee-brown & cream design system, rounded corners, soft shadows, fully responsive with a
  mobile bottom nav bar.

## 🗂 Project Structure

```
brews_ko/
├── brews_ko/            # Project settings, root urls
├── shop/                 # Main app: models, views, forms, admin, cart, seed command
│   ├── management/commands/seed_data.py
│   ├── migrations/
│   └── templatetags/shop_extras.py
├── templates/
│   ├── base.html, navbar.html, footer.html
│   └── shop/              # home, menu, product_detail, cart, checkout, order_success, about
├── static/
│   ├── css/style.css      # design system
│   └── js/main.js         # scroll reveal (Intersection Observer) + UX helpers
├── media/products/        # uploaded product images
├── requirements.txt
└── manage.py
```

## 🚀 Getting Started

1. **Create a virtual environment & install dependencies**

   ```bash
   python3 -m venv venv
   source venv/bin/activate        # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Run migrations**

   ```bash
   python manage.py migrate
   ```

3. **(Optional) Seed sample data** — adds 8 categories, ~21 products, and 5 testimonials:

   ```bash
   python manage.py seed_data
   ```

4. **Create an admin account**

   ```bash
   python manage.py createsuperuser
   ```

5. **Run the dev server**

   ```bash
   python manage.py runserver
   ```

   Visit `http://127.0.0.1:8000/` for the storefront and `http://127.0.0.1:8000/admin/` for the
   admin panel.

## 🛠 Admin Workflow

- **Login** (`/admin/login/`) — a Brew's Ko–branded login screen (not the default plain Django admin
  login). It posts to Django's normal admin auth view, so it works with any staff/superuser account
  created via `createsuperuser` or the admin's user management.
- **Categories** (`/admin/shop/category/`) — create/edit/delete categories (e.g. Espresso, Latte,
  Pastries). Slugs auto-generate from the name.
- **Products** (`/admin/shop/product/`) — add products with image, price, description; toggle
  `Available` (shows/hides from the menu) and `Featured` (shows on homepage) directly from the list.
- **Orders** (`/admin/shop/order/`) — view customer name, contact number, items, and total. Update
  `status` per-order or select multiple orders and use the bulk actions dropdown to mark them
  Pending / Preparing / Ready / Completed / Cancelled.
- **Testimonials** (`/admin/shop/testimonial/`) — manage the reviews shown on the homepage.

## 🎨 Design System

Defined as CSS custom properties in `static/css/style.css`:

| Token | Value | Usage |
|---|---|---|
| `--coffee` | `#6F4E37` | Primary buttons, headings accents |
| `--cream` | `#F5F0E6` | Page background |
| `--beige` | `#EDE3D3` | Section backgrounds, chips |
| `--accent` | `#C0785A` | Badges, price highlights |

Fonts: **Fraunces** (display/headings) + **Manrope** (body), loaded from Google Fonts.

## 📱 Scroll Reveal Animation

`static/js/main.js` uses the `IntersectionObserver` API to add an `.in-view` class to any element
with `.reveal-fade` or `.reveal-card` once it enters the viewport, triggering a CSS transition from
`opacity: 0; transform: translateY(40px)` to `opacity: 1; transform: translateY(0)`. Falls back
gracefully (`prefers-reduced-motion`, and browsers without `IntersectionObserver`).

## 🧩 Tech Stack

- Python 3 / Django 6
- SQLite (default; swap `DATABASES` in `settings.py` for Postgres/MySQL in production)
- Bootstrap 5.3 (CDN) + Bootstrap Icons
- Vanilla JavaScript (no build step required)
- Pillow (for `ImageField` support)

## 📦 Production Notes

Before deploying:

- Set `DJANGO_DEBUG=False` and a strong `DJANGO_SECRET_KEY` as environment variables.
- Set `DJANGO_ALLOWED_HOSTS` to your real domain(s).
- Run `python manage.py collectstatic` and serve `staticfiles/` + `media/` via your web server or
  a service like WhiteNoise / S3.
- Swap SQLite for Postgres/MySQL for concurrent production traffic.
