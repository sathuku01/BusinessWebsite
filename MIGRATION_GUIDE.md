# Migration Guide — Production Deployment with Custom User Model

## Overview

This project uses a **Custom User Model** (`ecommerce.User` extending `AbstractUser`).  
Migrating an existing Django project with `auth.User` to a custom user model requires a **data migration** to preserve users, permissions, and foreign keys.

---

## Development vs Production

| Environment | Approach |
|-------------|----------|
| **Development (SQLite)** | Fresh start: delete migrations + `db.sqlite3`, run `makemigrations` + `migrate` |
| **Production (PostgreSQL)** | **Data migration required** — see below |

---

## Production Migration Strategy

### Prerequisites
- Backup database: `pg_dump > backup.sql`
- Test migration on staging first
- Schedule maintenance window

---

### Step-by-Step Migration

#### 1. Prepare New Models (Already Done)
```python
# ecommerce/models.py - User, Store, StaffProfile
AUTH_USER_MODEL = 'ecommerce.User'  # in settings.py
```

#### 2. Create Initial Migration
```bash
python manage.py makemigrations ecommerce
# Creates 0001_initial.py with User, Store, StaffProfile, etc.
```

#### 3. Create Data Migration
```bash
python manage.py makemigrations ecommerce --empty --name migrate_auth_user
```

#### 4. Edit Data Migration
```python
# ecommerce/migrations/0002_migrate_auth_user.py

from django.db import migrations
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission

def migrate_users(apps, schema_editor):
    """
    Copy auth_user → ecommerce_user
    Update all foreign keys
    """
    OldUser = apps.get_model('auth', 'User')
    NewUser = apps.get_model('ecommerce', 'User')
    Customer = apps.get_model('ecommerce', 'Customer')
    StaffProfile = apps.get_model('ecommerce', 'StaffProfile')
    Store = apps.get_model('ecommerce', 'Store')
    
    # Create default store for existing staff
    default_store, _ = Store.objects.get_or_create(
        code='MAIN',
        defaults={'name': 'Main Store', 'address': 'Migrated from legacy'}
    )
    
    for old_user in OldUser.objects.all():
        # Create new user
        new_user = NewUser.objects.create(
            id=old_user.id,  # Preserve PK for FK references
            password=old_user.password,
            last_login=old_user.last_login,
            is_superuser=old_user.is_superuser,
            username=old_user.username,
            first_name=old_user.first_name,
            last_name=old_user.last_name,
            email=old_user.email,
            is_staff=old_user.is_staff,
            is_active=old_user.is_active,
            date_joined=old_user.date_joined,
        )
        
        # Copy groups & permissions
        new_user.groups.set(old_user.groups.all())
        new_user.user_permissions.set(old_user.user_permissions.all())
        
        # Create Customer for non-staff
        if not old_user.is_staff:
            Customer.objects.get_or_create(user=new_user)
        
        # Create StaffProfile for staff
        if old_user.is_staff:
            role = 'admin' if old_user.is_superuser else 'manager'
            StaffProfile.objects.create(
                user=new_user,
                role=role,
                store=default_store
            )

def reverse_migrate(apps, schema_editor):
    # Not typically needed, but implement if rollback required
    NewUser = apps.get_model('ecommerce', 'User')
    NewUser.objects.all().delete()

class Migration(migrations.Migration):
    dependencies = [
        ('ecommerce', '0001_initial'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]
    operations = [
        migrations.RunPython(migrate_users, reverse_migrate),
    ]
```

#### 5. Update Foreign Key References (Auto-handled by PK preservation)
Since we preserve `id`, existing FKs in `Order`, `Payment`, `Cart`, etc. will point to correct `ecommerce.User` records.

**But**: Django's `auth.User` is still in `django_migrations`. Need to fake initial auth migrations:

```bash
# After data migration runs:
python manage.py migrate --fake auth 0001_initial
python manage.py migrate --fake auth 0002_alter_permission_name_max_length
# ... fake all auth migrations up to current
```

#### 6. Run Migrations
```bash
python manage.py migrate
```

#### 7. Verify
```bash
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
print('User model:', User)
print('Count:', User.objects.count())
print('Sample:', User.objects.first().username)
"
```

---

## Post-Migration Checklist

- [ ] All users can login
- [ ] Admin users access `/admin/`
- [ ] Manager users access `/admin-dashboard/`
- [ ] Customer orders/debts intact
- [ ] Permissions/groups preserved
- [ ] `seed_data` not needed (data preserved)
- [ ] Run test suite: `python manage.py test`

---

## Common Issues & Fixes

| Issue | Fix |
|-------|-----|
| `Manager isn't available; 'auth.User' has been swapped` | Ensure `AUTH_USER_MODEL` set **before** any `makemigrations` |
| `ForeignKey to 'auth.User' not resolved` | Use `settings.AUTH_USER_MODEL` in all FK definitions |
| `Duplicate key value violates unique constraint` | Preserve PK in data migration (`id=old_user.id`) |
| Admin login fails | Check `is_staff` copied correctly in data migration |
| `RelatedObjectDoesNotExist: User has no customer` | Signal creates Customer on User post_save; ensure signal runs |

---

## Alternative: Fresh Database (If Acceptable)

If you can reset production data:

```bash
# On server
DROP DATABASE yourdb;
CREATE DATABASE yourdb;
python manage.py migrate
python manage.py seed_data
```

---

## References

- [Django Docs: Substituting a custom User model](https://docs.djangoproject.com/en/5.2/topics/auth/customizing/#substituting-a-custom-user-model)
- [Django Migrations: Data Migrations](https://docs.djangoproject.com/en/5.2/topics/migrations/#data-migrations)
- [Lincoln Loop: Migrating to a Custom User Model](https://lincolnloop.com/blog/migrating-custom-user-model-django/)