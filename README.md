# Business Website 🛒

A full-featured Django-based e-commerce platform for managing products, orders, inventory, and payments. Built with a clean admin panel and customer‑facing storefront.

---

## 👥 Development Team

- **Hamisi Ali** – Backend Developer  
- **bkoimett** – Frontend Developer 
- **Sathuku** – Fullstack Developer

---

## 🚀 Features

### Customer-Facing Storefront
- Product browsing with category/brand filtering, search, price/stock filters
- Guest cart with session persistence
- User registration/login with cart merge on login
- Checkout flow with stock validation
- Order history, debt tracking, profile management

### Staff Interfaces (Three-Tier Architecture)
| Role | Access |
|------|--------|
| **Admin** | Full system access: all stores' data, staff management, system settings, delete payments |
| **Store Manager** | Store-scoped access: products (CRUD), orders (view/update/delete), payments, debts, consignments, expenses, financial reports (read-only), stock adjustments |
| **Customer** | Own orders, debts, cart, checkout, profile |

### Inventory & Financial Management
- **Consignments**: Supplier management, multi-item consignments with box/unit costing
- **Expenses**: Categorized expense tracking per store
- **Financial Reports**: Purchases, sales, COGS estimation, gross/net profit, low-stock alerts
- **Stock Adjustments**: Audit trail for inventory changes

### Technical
- REST API (DRF) with role-based permissions
- Content Security Policy (CSP) middleware
- Environment-based configuration (.env)
- Database seeding for development

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Django 6.0 (Python) |
| API | Django REST Framework |
| Frontend | HTML5, CSS3, Bootstrap 5, Custom Design System |
| Database | SQLite (dev) / PostgreSQL (prod) |
| Auth | Custom User Model + StaffProfile (role-based) |
| Version Control | Git + GitHub |
| Media Storage | Local filesystem (customizable to S3) |

---

## 📂 Project Structure

```text
BusinessWebsite/
├── ecommerce/                 # Main Django app
│   ├── models.py              # User, Store, StaffProfile, Product, Order, Payment, Consignment, Expense, etc.
│   ├── models/                # Split models (user.py, staff.py)
│   ├── forms.py               # Product, Consignment, Expense, Staff forms
│   ├── views.py               # Business logic (FBVs + DRF ViewSets)
│   ├── decorators.py          # @manager_required, @admin_required
│   ├── permissions.py         # DRF permission classes
│   ├── cart.py                # Cart logic (guest/user, merge on login)
│   ├── signals.py             # Auto-create Customer, Debt, cart merge
│   ├── context_processors.py  # cart_summary, staff_context
│   ├── serializers.py         # DRF serializers
│   ├── urls.py                # URL routing
│   ├── admin.py               # Django Admin config
│   ├── management/commands/   # seed_data command
│   ├── templates/             # HTML templates (base, dashboard, orders, products, staff, etc.)
│   ├── static/                # CSS, JS, images
│   └── tests.py               # 20 tests (role access, store scoping, CRUD)
├── ecommerce_manager/         # Django project settings
│   ├── settings.py            # AUTH_USER_MODEL, CSP, .env config
│   └── urls.py                # Root URL config
├── media/                     # Uploaded product images
├── db.sqlite3                 # Default database (dev)
├── manage.py                  # Django CLI entry point
├── requirements.txt           # Python dependencies
├── README.md                  # This file
├── ROLE_MATRIX.md             # Permission matrix
├── ARCHITECTURE.md            # Architecture documentation
└── MIGRATION_GUIDE.md         # Production migration guide
```

---

## ⚙️ Setup Instructions

### Prerequisites
- Python 3.8+
- Git
- Virtual environment (recommended)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/sathuku01/BusinessWebsite.git
   cd BusinessWebsite
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate      # Linux/macOS
   venv\Scripts\activate         # Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment** (copy and edit)
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

5. **Apply database migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Seed development data** (creates admin, manager, customers, products, orders)
   ```bash
   python manage.py seed_data
   ```

7. **Run the development server**
   ```bash
   python manage.py runserver
   ```

8. Open `http://127.0.0.1:8000` in your browser.

---

## 🔐 Default Credentials (after `seed_data`)

| Role | Username | Password | Access |
|------|----------|----------|--------|
| **Admin** | `admin` | `admin123` | Full system + staff management |
| **Manager** | `manager` | `manager123` | Store-scoped dashboard |
| **Customers** | `alice`/`bob`/`carol`/`david`/`eve` | `test1234` | Storefront only |

---

## 🏗️ Three-Tier Architecture

### Role Model
```
User (AbstractUser)
  ├── Customer (OneToOne)           → Storefront users
  └── StaffProfile (OneToOne)       → Internal staff
        ├── role: 'manager' | 'admin'
        └── store: FK to Store      → Managers scoped to one store
```

### Store Scoping
- Managers only see data for their assigned `Store`
- Admins see all stores' data
- Products, Orders, Consignments, Expenses all have `store` FK

### Key Files
- `ecommerce/decorators.py` — `@manager_required`, `@admin_required`
- `ecommerce/permissions.py` — `IsManagerOrAdmin`, `IsAdmin`
- `ecommerce/context_processors.py` — `staff_context` (adds `is_manager`, `is_admin`, `user_store` to templates)

---

## 🧪 Running Tests

```bash
# All tests
python manage.py test

# Specific test classes
python manage.py test ecommerce.tests.EcommerceFeatureTests
python manage.py test ecommerce.tests.ThreeTierRoleTests
```

**Test Coverage**: 20 tests covering:
- Public product access
- Cart/checkout flows
- Role-based dashboard access
- Store scoping (managers see only their store)
- CRUD permissions per role
- Staff management (admin only)

---

## 🚀 Deployment Notes

### Production Checklist
- [ ] Set `DEBUG=False` in `.env`
- [ ] Set strong `DJANGO_SECRET_KEY` in `.env`
- [ ] Configure `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS`
- [ ] Use PostgreSQL (update `DATABASES` in settings)
- [ ] Set `SECURE_SSL_REDIRECT=True`
- [ ] Configure media storage (S3/CloudFront recommended)
- [ ] Run `collectstatic`
- [ ] Review `MIGRATION_GUIDE.md` for custom user model migration

### Custom User Model Migration (Production)
See `MIGRATION_GUIDE.md` for data migration steps when deploying to existing database.

---

## 🤝 Contributing

Contributions are welcome!  
Please open an issue first to discuss any major changes. For minor fixes, feel free to submit a pull request.

---

## 📄 License

This project is licensed under the **MIT License** – see the [LICENSE](LICENSE) file for details.

---

## 📧 Contact

For questions or support, reach out to the development team.

---

## 📚 Additional Documentation

- [Role Matrix](ROLE_MATRIX.md) — Detailed permission table
- [Architecture](ARCHITECTURE.md) — System architecture, data flow, signals
- [Migration Guide](MIGRATION_GUIDE.md) — Production deployment with custom user model