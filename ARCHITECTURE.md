# Architecture Documentation

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        BUSINESS WEBSITE (Django 6.0)                        │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        ▼                           ▼                           ▼
┌───────────────┐           ┌───────────────┐           ┌───────────────┐
│   CUSTOMER    │           │ STORE MANAGER │           │    ADMIN      │
│  (Storefront) │           │  (Dashboard)  │           │  (Dashboard)  │
└───────┬───────┘           └───────┬───────┘           └───────┬───────┘
        │                           │                           │
        └───────────────────────────┼───────────────────────────┘
                                    ▼
                    ┌───────────────────────────────┐
                    │      SHARED BACKEND           │
                    │  (Views, Models, Signals,     │
                    │   DRF API, Cart Logic)        │
                    └───────────────┬───────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        ▼                           ▼                           ▼
┌───────────────┐           ┌───────────────┐           ┌───────────────┐
│  SQLITE/      │           │  MEDIA FILES  │           │  STATIC FILES │
│  POSTGRESQL   │           │  (Uploads)    │           │  (CSS/JS)     │
└───────────────┘           └───────────────┘           └───────────────┘
```

---

## Data Model Architecture

### Core Models (ecommerce/models.py)

```
User (AbstractUser)
├── email (unique, required)
├── first_name, last_name
├── is_staff, is_superuser (Django admin)
└── staff_profile (OneToOne) ──────────────────┐
                                               ▼
Customer (OneToOne User)              StaffProfile
├── phone_number                      ├── role: 'manager' | 'admin'
├── address                           ├── store (FK Store)
├── profile_picture                   ├── hire_date
                                        └── is_active
                                               │
                                               ▼
                                    ┌────────────────────┐
                                    │       Store        │
                                    │  (Multi-tenant)    │
                                    └─────────┬──────────┘
                                              │
        ┌─────────────────────────────────────┼─────────────────────────────────────┐
        ▼                                     ▼                                     ▼
┌───────────────┐                    ┌───────────────┐                    ┌───────────────┐
│   Product     │                    │    Order      │                    │  Consignment  │
│  (store FK)   │                    │  (store FK)   │                    │  (store FK)   │
└───────┬───────┘                    └───────┬───────┘                    └───────┬───────┘
        │                                     │                                     │
        ▼                                     ▼                                     ▼
┌───────────────┐                    ┌───────────────┐                    ┌───────────────┐
│ ProductImage  │                    │  OrderItem    │                    │ ConsignmentItem│
│ (FK Product)  │                    │  (FK Order)   │                    │ (FK Consignment)│
└───────────────┘                    └───────┬───────┘                    └───────┬───────┘
                                             │                                     │
                                             ▼                                     ▼
                                    ┌──────────────────┐                 ┌──────────────────┐
                                    │     Payment      │                 │     Expense      │
                                    │  (FK Order)      │                 │  (store FK)      │
                                    └────────┬─────────┘                 └────────┬─────────┘
                                             │                                     │
                                             ▼                                     ▼
                                    ┌──────────────────┐                 ┌──────────────────┐
                                    │      Debt        │                 │ StockAdjustment  │
                                    │ (FK Order, Cust) │                 │ (FK Product)     │
                                    └──────────────────┘                 └──────────────────┘
```

### Key Relationships

| Model | Store Scoped | Notes |
|-------|-------------|-------|
| `User` | No | Global auth |
| `StaffProfile` | Yes (via store FK) | Manager/Admin profile |
| `Customer` | No | Linked to User |
| `Product` | **Yes** | Manager creates in their store |
| `Order` | **Yes** | Auto-assigned from product/cart |
| `OrderItem` | Via Order | No direct store FK |
| `Payment` | Via Order | No direct store FK |
| `Debt` | Via Order | No direct store FK |
| `Consignment` | **Yes** | Manager creates in their store |
| `ConsignmentItem` | Via Consignment | Links Product |
| `Expense` | **Yes** | Per-store expenses |
| `StockAdjustment` | Via Product | Audit trail |
| `Supplier` | **No** | Global (supplies chain) |
| `Category`, `Brand` | No | Global catalog |

---

## Authentication & Authorization Flow

### 1. User Registration
```
POST /auth/register/
    │
    ▼
CustomUserCreationForm → User.save()
    │
    ├─► Signal: post_save User → create Customer (if not staff)
    │
    ▼
login(request, user)
    │
    ▼
merge_guest_cart_into_user_cart()
```

### 2. User Login
```
POST /auth/login-page/
    │
    ▼
CustomAuthenticationForm → authenticate()
    │
    ▼
login(request, user)
    │
    ▼
Signal: user_logged_in → merge_guest_cart_into_user_cart()
    │
    ▼
Redirect based on role:
    ├─ Admin/Manager → /admin-dashboard/
    └─ Customer → /dashboard/
```

### 3. Role Detection (Context Processor)
```python
# ecommerce/context_processors.staff_context(request)
if request.user.is_authenticated and hasattr(user, 'staff_profile'):
    profile = user.staff_profile
    if profile.is_active:
        is_manager = profile.role in ['manager', 'admin']
        is_admin = profile.role == 'admin'
        user_store = profile.store
```

### 4. View Authorization (Decorators)
```python
@manager_required  # Checks staff_profile.role in ['manager', 'admin']
@admin_required    # Checks staff_profile.role == 'admin'

# In view:
is_admin = user.is_superuser or (staff_profile.role == 'admin')
store = None if is_admin else user.staff_profile.store
queryset = Model.objects.all() if is_admin else Model.objects.filter(store=store)
```

---

## Cart System Architecture

### Guest Cart (Session-Based)
```
Session Key: 'bizstore_guest_cart'
Cart: user=NULL, session_key=<uuid>
    │
    ├─► Created on first add_to_cart
    ├─► Persists across sessions (30 days)
    └─► Merged on user login
```

### User Cart
```
Cart: user=<User>, session_key=NULL
    │
    └─► One per user (get_or_create)
```

### Cart Merge on Login
```python
merge_guest_cart_into_user_cart(request, user):
    1. Get guest_cart from session
    2. Get/create user_cart
    3. For each guest_item:
         - Get/create user_item for same product
         - Sum quantities
    4. Delete guest_cart items + guest_cart
    5. Clear session key
```

---

## Signal Architecture

| Signal | Sender | Action |
|--------|--------|--------|
| `pre_save` | `OrderItem` | Set price from product |
| `post_save` | `Order` | Create `Debt` record |
| `post_save` | `OrderItem` | Update debt balance |
| `post_save` | `Payment` | Update debt balance |
| `post_save` | `User` | Auto-create `Customer` |
| `user_logged_in` | - | Merge guest cart |
| `post_delete` | `ProductImage` | Delete image file |

### Debt Auto-Creation Flow
```
Order Created
    │
    ├─► post_save Order (created=True)
    │       └─► Debt.objects.create(
    │               customer=order.customer,
    │               order=order,
    │               outstanding_balance=order.get_total_amount()
    │           )
    │
    ├─► OrderItem saved
    │       └─► post_save OrderItem → debt.calculate_outstanding_balance()
    │
    └─► Payment saved
            └─► post_save Payment → debt.calculate_outstanding_balance()
```

---

## Store Scoping Implementation

### Pattern Used in All Manager Views
```python
def manager_view(request):
    user = request.user
    is_admin = user.is_superuser or (hasattr(user, 'staff_profile') and user.staff_profile.role == 'admin')
    store = None if is_admin else user.staff_profile.store
    
    if is_admin:
        queryset = Model.objects.all()
    else:
        queryset = Model.objects.filter(store=store)
    
    # For related models:
    # Payment → filter(order__store=store)
    # Debt → filter(order__store=store)
    # OrderItem → filter(order__store=store)
```

### URL Structure
```
/admin-dashboard/                 → Shared dashboard (role-filtered tabs)
/admin-dashboard/products/        → Products (store-scoped)
/admin-dashboard/orders/          → Orders (store-scoped)
/admin-dashboard/payments/        → Payments (store-scoped)
/admin-dashboard/debts/           → Debts (store-scoped)
/admin-dashboard/consignments/    → Consignments (store-scoped)
/admin-dashboard/expenses/        → Expenses (store-scoped)
/admin-dashboard/reports/         → Reports (store-scoped)
/admin-dashboard/financial-report/→ Financial report (store-scoped)
/admin-dashboard/staff/           → Staff management (Admin only)
```

---

## API Layer (DRF)

### ViewSet Pattern
```python
class ProductViewSet(ModelViewSet):
    permission_classes = [IsManagerOrAdmin]
    
    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'staff_profile') and user.staff_profile.role == 'manager':
            return Product.objects.filter(store=user.staff_profile.store)
        return Product.objects.all()
```

### Serializers
- `CustomerSerializer` — All fields
- `ProductSerializer` — All fields + store
- `OrderSerializer` — Nested items, payments, computed totals
- `PaymentSerializer` — + outstanding_balance
- `DebtSerializer` — Nested order + customer

---

## Frontend Architecture

### Template Inheritance
```
base.html (458 lines)
├── Navbar (role-aware via context processor)
├── Sidebar (admin templates)
├── Messages block
└── {% block content %}

Key templates extending base:
├── admin_dashboard.html (336 lines) — Tabbed interface
├── admin_products_list.html
├── orders_list.html
├── debts_list.html
├── order_detail.html
├── product_form.html
├── consignment_form.html
├── expense_form.html
├── staff_list.html / staff_form.html
└── financial_report.html
```

### Design System (CSS Variables in base.html)
```css
:root {
  --primary: #E07A5F;
  --primary-hover: #C9664D;
  --bg: #FFFBF5;
  --surface: #FFFFFF;
  --border: #F2E8DA;
  --text: #3D405B;
  --muted: #818589;
  --success: #81B29A;
  --warning: #F2CC8F;
  --danger: #EF4444;
  --radius: 24px;
  --shadow: 0 10px 30px rgba(224, 122, 95, 0.04);
}
```

### Component Patterns
- **Stat Cards**: `.stat-card` with `.stat-icon` + `.stat-value`
- **Tables**: `.table` with status badges (`.badge-status`)
- **Forms**: `.form-control`, `.form-select` with focus states
- **Product Cards**: `.product-card` with hover lift
- **Buttons**: `.btn-primary` (rounded pill), `.btn-outline-primary`

---

## Security Architecture

### CSP Middleware (django-csp)
```python
MIDDLEWARE = [
    'csp.middleware.CSPMiddleware',  # After SecurityMiddleware
]

CSP_DEFAULT_SRC = ["'self'"]
CSP_SCRIPTS_SRC = ["'self'"]
CSP_STYLE_SRC = ["'self'"]
CSP_IMG_SRC = ["'self'", "data:"]
# ... etc
```

### Session Security
```python
SESSION_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_AGE = 9600  # 2.6 hours
SESSION_SAVE_EVERY_REQUEST = True
```

### Production Security Headers
```python
SECURE_HSTS_SECONDS = 36000
SECURE_HSTS_PRELOAD = True
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_SSL_REDIRECT = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
```

---

## Financial Report Calculation

### Data Sources
| Metric | Source |
|--------|--------|
| Stock Received | `Consignment.get_total_quantity()` (date range) |
| Total Purchases | `Consignment.get_total_cost()` (date range) |
| Total Sales | `Order.get_total_amount()` (date range) |
| Stock Sold | Sum `OrderItem.quantity` (date range) |
| Expenses | `Expense.amount` (date range) |
| COGS | `stock_sold * avg_unit_cost` (from all consignments) |
| Gross Profit | `total_sales - cogs` |
| Net Profit | `gross_profit - total_expenses` |

### Store Scoping
All queries filtered by `store=request.user.staff_profile.store` for managers.

---

## Deployment Architecture

### Development
```
SQLite (db.sqlite3)
Local media (/media/)
Local static (/static/)
Runserver (port 8000)
```

### Production (Recommended)
```
PostgreSQL (managed)
S3/CloudFront (media)
CDN (static)
Gunicorn + Nginx
Docker/K8s optional
```

### Custom User Model Migration
See `MIGRATION_GUIDE.md` for production data migration steps.

---

## File Inventory

### Core App (ecommerce/)
```
models.py          → All models (User, Store, StaffProfile, Product, Order, etc.)
views.py           → 50+ FBVs + 7 DRF ViewSets (1448 lines)
decorators.py      → @manager_required, @admin_required
permissions.py     → DRF permission classes
cart.py            → Cart logic (guest/user, merge)
signals.py         → 7 signal handlers
context_processors.py → cart_summary, staff_context
forms.py           → 9 ModelForms
serializers.py     → 6 DRF serializers
urls.py            → 40+ URL patterns
admin.py           → 10 ModelAdmins
management/commands/seed_data.py → Dev data seeding
tests.py           → 20 tests
templates/         → 30+ HTML templates
```

### Project Config (ecommerce_manager/)
```
settings.py        → AUTH_USER_MODEL, CSP, .env, context processors
urls.py            → Root URLs (admin, api, redirect to products)
```

---

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Custom User (AbstractUser) | Email unique, future extensibility |
| StaffProfile separate from Customer | Clean separation: shoppers vs staff |
| Store FK on business models | True multi-store architecture |
| Shared dashboard with tabs | Single codebase, role-filtered UI |
| Decorators over mixins | Simpler for FBVs, explicit |
| Signals for debt/cart | Decoupled, automatic |
| Context processor for roles | Available in all templates |
| Bootstrap 5 + CSS variables | No build step, easy customization |