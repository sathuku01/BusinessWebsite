
from django.db.models.signals import pre_save
from django.db.models.signals import post_save, post_delete
from django.contrib.auth.signals import user_logged_in
from django.utils import timezone
from django.dispatch import receiver
from .models import OrderItem, Payment, Debt, Order
from django.contrib.auth import get_user_model
from .models import Customer
from .models import ProductImage
from .cart import merge_guest_cart_into_user_cart




@receiver(pre_save, sender=OrderItem)
def set_price_from_product(sender, instance, **kwargs):
    if instance.product:
        # Always set price from product
        instance.price = instance.product.price

@receiver(post_save, sender=Payment)
def update_debt_after_payment(sender, instance, **kwargs):
    order = instance.order
    debt, created = Debt.objects.get_or_create(
        customer=order.customer,
        order=order,
        defaults={
            'outstanding_balance': order.get_total_amount() - order.get_total_paid(),
            'is_paid': False,
            'paid_at': None
        }
    )

    # Recalculate balance using your model method
    debt.calculate_outstanding_balance()


@receiver(post_save, sender=Order)
def create_debt_for_order(sender, instance, created, **kwargs):
    if created:
        Debt.objects.create(
            customer=instance.customer,
            order=instance,
            outstanding_balance=instance.get_total_amount(),
            is_paid=False,
            paid_at=None
        )

@receiver(post_save, sender=OrderItem)
def update_debt_after_orderitem(sender, instance, **kwargs):
    order = instance.order
    debt, created = Debt.objects.get_or_create(
        customer=order.customer,
        order=order,
        defaults={'outstanding_balance': 0, 'is_paid': False, 'paid_at': None}
    )
    debt.calculate_outstanding_balance()

User = get_user_model()

@receiver(post_save, sender=User)
def create_customer(sender, instance, created, **kwargs):
    if created:
        Customer.objects.create(user=instance)

@receiver(user_logged_in)
def merge_guest_cart_on_login(sender, request, user, **kwargs):
    merge_guest_cart_into_user_cart(request, user)


@receiver(post_delete, sender=ProductImage)
def delete_product_image_file(sender, instance, **kwargs):
    if instance.image:
        instance.image.delete(save=False)