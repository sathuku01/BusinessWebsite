# Role Matrix — Three-Tier Access Control

## Overview

| Role | Description | Store Scoped |
|------|-------------|--------------|
| **Customer** | Storefront shopper | N/A (own data only) |
| **Store Manager** | Day-to-day store operations | ✅ Yes (assigned store only) |
| **Admin** | System administration | ❌ No (all stores) |

---

## Permission Matrix

| Feature / Action | Customer | Store Manager | Admin |
|------------------|----------|---------------|-------|
| **Authentication** |
| Register/Login | ✅ | ✅ | ✅ |
| Password Change | ✅ | ✅ | ✅ |
| Profile Update | ✅ | ✅ | ✅ |
| **Products** |
| View Products (storefront) | ✅ | ✅ | ✅ |
| View Products (admin list) | ❌ | ✅ | ✅ |
| Create Product | ❌ | ✅ (auto-assigned to store) | ✅ (any store) |
| Edit Product | ❌ | ✅ (own store only) | ✅ (any store) |
| Delete Product | ❌ | ✅ (own store only) | ✅ (any store) |
| Stock Adjustments | ❌ | ✅ (own store only) | ✅ (any store) |
| **Orders** |
| Place Order (checkout) | ✅ | ❌ | ❌ |
| View Own Orders | ✅ | ❌ | ❌ |
| View All Orders (store) | ❌ | ✅ | ❌ |
| View All Orders (all stores) | ❌ | ❌ | ✅ |
| Update Order Status | ❌ | ✅ (own store) | ✅ |
| Delete Order | ❌ | ✅ (own store) | ✅ |
| Mark Order Paid | ❌ | ✅ (own store) | ✅ |
| **Payments** |
| View Own Payments | ✅ | ❌ | ❌ |
| Record Payment | ❌ | ✅ (own store orders) | ✅ |
| Edit Payment | ❌ | ✅ (own store) | ✅ |
| Delete Payment | ❌ | ❌ | ✅ |
| **Debts** |
| View Own Debts | ✅ | ❌ | ❌ |
| View All Debts (store) | ❌ | ✅ | ❌ |
| View All Debts (all stores) | ❌ | ❌ | ✅ |
| Manage Debts | ❌ | ✅ (own store) | ✅ |
| **Consignments** |
| View Consignments | ❌ | ✅ (own store) | ✅ |
| Create Consignment | ❌ | ✅ (auto-assigned to store) | ✅ |
| Manage Suppliers | ❌ | ✅ | ✅ |
| **Expenses** |
| View Expenses | ❌ | ✅ (own store) | ✅ |
| Create Expense | ❌ | ✅ (auto-assigned to store) | ✅ |
| **Reports** |
| View Financial Report | ❌ | ✅ Read-only (own store) | ✅ Read/Export |
| View Sales/Payment Reports | ❌ | ✅ (own store) | ✅ |
| **Staff Management** |
| View Staff List | ❌ | ❌ | ✅ |
| Create Manager | ❌ | ❌ | ✅ |
| Create Admin | ❌ | ❌ | ✅ |
| Edit Staff (role, store, active) | ❌ | ❌ | ✅ |
| Delete Manager | ❌ | ❌ | ✅ |
| Delete Admin | ❌ | ❌ | ❌ |
| **System** |
| Django Admin (`/admin/`) | ❌ | ❌ | ✅ (is_staff) |
| System Settings | ❌ | ❌ | ✅ |

---

## UI Navigation (Navbar Tabs)

| Tab | Customer | Manager | Admin |
|-----|----------|---------|-------|
| Dashboard | ❌ | ✅ | ✅ |
| Products | ✅ (storefront) | ✅ (admin) | ✅ (admin) |
| Orders | ✅ (my orders) | ✅ (all store) | ✅ (all) |
| Payments | ❌ | ✅ | ✅ |
| Debts | ✅ (my debts) | ✅ (all store) | ✅ (all) |
| Consignments | ❌ | ✅ | ✅ |
| Expenses | ❌ | ✅ | ✅ |
| Reports | ❌ | ✅ | ✅ |
| Financial Report | ❌ | ✅ | ✅ |
| Staff | ❌ | ❌ | ✅ |

---

## API Endpoints (DRF)

| Endpoint | Customer | Manager | Admin |
|----------|----------|---------|-------|
| `/api/products/` (list/create) | ❌ | ✅ (store-scoped) | ✅ |
| `/api/products/{id}/` | ❌ | ✅ (store-scoped) | ✅ |
| `/api/orders/` | ❌ | ✅ (store-scoped) | ✅ |
| `/api/orders/{id}/` | ❌ | ✅ (store-scoped) | ✅ |
| `/api/payments/` | ❌ | ✅ (store-scoped) | ✅ |
| `/api/debts/` | ❌ | ✅ (store-scoped) | ✅ |
| `/api/customers/` | ✅ (own only) | ❌ | ✅ |

---

## Implementation Details

### Decorators (`ecommerce/decorators.py`)
```python
@manager_required   # role in ['manager', 'admin']
@admin_required     # role == 'admin'
```

### DRF Permissions (`ecommerce/permissions.py`)
```python
IsManagerOrAdmin    # has_permission: manager or admin
IsAdmin             # has_permission: admin only
IsStoreManager      # has_object_permission: store match
```

### Context Processor (`ecommerce/context_processors.py`)
```python
staff_context(request) → {
    'is_manager': bool,
    'is_admin': bool,
    'user_store': Store or None
}
```

### View Filtering Pattern
```python
# In every manager view:
is_admin = user.is_superuser or (hasattr(user, 'staff_profile') and user.staff_profile.role == 'admin')
store = None if is_admin else user.staff_profile.store

if is_admin:
    qs = Model.objects.all()
else:
    qs = Model.objects.filter(store=store)
```

---

## Testing Coverage

All role permutations tested in `ecommerce/tests.py`:
- ✅ Admin accesses everything
- ✅ Manager accesses store-scoped data only
- ✅ Customer accesses own data only
- ✅ Anonymous redirected to login
- ✅ Manager cannot access staff management
- ✅ Admin can manage staff
- ✅ Store scoping enforced on orders, products, payments, debts