from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from .models import Cart, CartItem, Order, OrderItem


CART_SESSION_KEY = 'bizstore_guest_cart'


def get_guest_cart_from_session(request):
    session_key = request.session.get(CART_SESSION_KEY)
    if not session_key:
        return None
    return (
        Cart.objects
        .filter(session_key=session_key, user__isnull=True)
        .order_by('-updated_at')
        .first()
    )


def get_or_create_user_cart(user):
    cart, _ = Cart.objects.get_or_create(user=user)
    return cart


def get_cart_for_request(request, create=True):
    if request.user.is_authenticated:
        if create:
            return get_or_create_user_cart(request.user)
        return Cart.objects.filter(user=request.user).first()

    session_key = request.session.get(CART_SESSION_KEY)
    if not session_key:
        if not create:
            return None
        request.session.create()
        session_key = request.session.session_key
        request.session[CART_SESSION_KEY] = session_key

    cart = Cart.objects.filter(session_key=session_key, user__isnull=True).order_by('-updated_at').first()
    if not cart and create:
        cart = Cart.objects.create(session_key=session_key)

    return cart


def add_item_to_cart(cart, product, quantity=1):
    quantity = int(quantity)
    if quantity <= 0:
        raise ValidationError('Quantity must be greater than zero.')

    item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': quantity},
    )
    if not created:
        item.quantity += quantity
        item.save(update_fields=['quantity', 'updated_at'])
    return item


def set_cart_item_quantity(cart_item, quantity):
    quantity = int(quantity)
    if quantity <= 0:
        cart_item.delete()
        return None
    cart_item.quantity = quantity
    cart_item.save(update_fields=['quantity', 'updated_at'])
    return cart_item


def remove_cart_item(cart_item):
    cart_item.delete()


def clear_cart(cart):
    cart.items.all().delete()


def validate_cart_stock(cart):
    invalid_items = []
    for item in cart.items.select_related('product'):
        if item.quantity > item.product.stock:
            invalid_items.append({
                'item': item,
                'product': item.product,
                'requested': item.quantity,
                'available': item.product.stock,
            })
    return invalid_items


def create_order_from_cart(cart, customer):
    if not cart.items.exists():
        raise ValidationError('Cart is empty.')

    invalid_items = validate_cart_stock(cart)
    if invalid_items:
        raise ValidationError('Cart contains items that exceed available stock.')

    with transaction.atomic():
        order = Order.objects.create(customer=customer, status='pending')
        for cart_item in cart.items.select_related('product'):
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                quantity=cart_item.quantity,
                price=cart_item.product.price,
            )
        clear_cart(cart)

    return order


def merge_guest_cart_into_user_cart(request, user):
    if not request or not request.session:
        return None

    guest_cart = get_guest_cart_from_session(request)
    if not guest_cart or not guest_cart.items.exists():
        return get_or_create_user_cart(user)

    user_cart = get_or_create_user_cart(user)
    with transaction.atomic():
        for guest_item in guest_cart.items.select_related('product'):
            user_item, created = CartItem.objects.get_or_create(
                cart=user_cart,
                product=guest_item.product,
                defaults={'quantity': guest_item.quantity},
            )
            if not created:
                user_item.quantity += guest_item.quantity
                user_item.save(update_fields=['quantity', 'updated_at'])

        guest_cart.items.all().delete()
        guest_cart.delete()

    request.session.pop(CART_SESSION_KEY, None)
    return user_cart


def get_cart_summary(request):
    cart = get_cart_for_request(request, create=False)
    if not cart:
        return {
            'cart': None,
            'item_count': 0,
            'total': 0,
        }

    return {
        'cart': cart,
        'item_count': cart.item_count,
        'total': cart.total,
    }
