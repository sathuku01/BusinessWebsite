from .cart import get_cart_summary


def cart_summary(request):
    return {'cart_summary': get_cart_summary(request)}
