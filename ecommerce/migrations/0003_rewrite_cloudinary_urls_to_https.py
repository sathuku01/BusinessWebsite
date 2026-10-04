from django.db import migrations
from django.db.models import Value
from django.db.models.functions import Replace

HTTP_PREFIX = "http://res.cloudinary.com/"
HTTPS_PREFIX = "https://res.cloudinary.com/"

TARGETS = [("ecommerce", "productimage", "image"), ("ecommerce", "customer", "profile_picture")]


def _rewrite(apps, old, new):
    # Rewrite via SQL rather than model instances: CloudinaryField rebuilds the URL from
    # its parsed attributes on attribute access, so a save() round-trip would drop the
    # file extension and any transformation segments stored alongside it.
    for app_label, model, field in TARGETS:
        apps.get_model(app_label, model).objects.filter(
            **{f"{field}__startswith": old}
        ).update(**{field: Replace(field, Value(old), Value(new))})


def to_https(apps, schema_editor):
    _rewrite(apps, HTTP_PREFIX, HTTPS_PREFIX)


def to_http(apps, schema_editor):
    _rewrite(apps, HTTPS_PREFIX, HTTP_PREFIX)


class Migration(migrations.Migration):
    dependencies = [("ecommerce", "0002_alter_customer_profile_picture_and_more")]

    operations = [migrations.RunPython(to_https, to_http)]