# Brew's Ko Coffee Shop

Brew's Ko is a modern Django-based coffee shop web application with a polished storefront and a staff dashboard. It supports guest ordering, customer accounts, favorites, product reviews, order management, and a CMS-style dashboard for homepage and shop settings.

## Highlights

- Responsive public site for browsing products, viewing details, and placing orders
- Session-based cart for guests with size selection for drink items
- Customer accounts with profile management, favorites, and product/store reviews
- Staff dashboard at /dashboard/ for orders, products, categories, customers, reports, homepage content, gamification, and shop settings
- Custom branded admin login experience
- Seed data command to populate sample menu items

## Tech Stack

- Django 6.0.7
- Python 3.x
- SQLite (default database)
- Bootstrap 5 + Bootstrap Icons
- Pillow for image uploads
- Vanilla JavaScript for interactive UI behavior

## Project Structure

```text
brews_ko/
├── brews_ko/                # Project settings and URL configuration
├── shop/                    # Main app: models, views, forms, URLs, dashboard logic
│   ├── management/commands/seed_data.py
│   ├── migrations/
│   └── templatetags/
├── templates/               # Public storefront and dashboard templates
├── static/                  # CSS, JavaScript, images
├── media/                   # Uploaded product, customer, and homepage images
├── requirements.txt
└── manage.py
```

## Quick Start

1. Create and activate a virtual environment

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
```

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Apply migrations

```bash
python manage.py migrate
```

4. Optional: load sample data

```bash
python manage.py seed_data
```

This adds example categories, products, and testimonials.

5. Create a staff account

```bash
python manage.py createsuperuser
```

6. Run the development server

```bash
python manage.py runserver
```

Open the following in your browser:

- Storefront: http://127.0.0.1:8000/
- Staff dashboard: http://127.0.0.1:8000/dashboard/
- Django admin: http://127.0.0.1:8000/admin/

## Main Features

### Public Storefront

- Home page with hero section, story/about content, featured products, and reviews
- Menu page with category filters and search
- Product detail page with quantity and size selection
- Cart and checkout flow for guest users
- About page and order success page

### Customer Experience

- Optional customer login/signup
- Profile page for personal information and order history
- Favorites for saved products
- Product and store reviews with ratings

### Staff Dashboard

The dashboard at /dashboard/ includes:

- Orders management with status updates
- Product and category CRUD
- Customer overview
- Homepage content editing
- Gamification settings and per-product point assignment
- Sales reports and basic revenue analytics
- Shop settings for branding/contact details

## Configuration Notes

- The project uses SQLite by default.
- Static files are served from the static/ directory, and media uploads are stored in media/.
- For production, set environment variables such as DJANGO_SECRET_KEY, DJANGO_DEBUG, and DJANGO_ALLOWED_HOSTS before deployment.
- Run collectstatic when preparing a production deployment.

## Notes for Developers

- The shop app contains the core business logic, models, and views.
- Dashboard functionality lives in shop/dashboard_views.py and is routed through shop/dashboard_urls.py.
- The seed_data management command is a good way to quickly populate the database with sample content.
