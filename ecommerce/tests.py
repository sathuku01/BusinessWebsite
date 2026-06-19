from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Product, Cart, CartItem

class EcommerceFeatureTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.product = Product.objects.create(name='Test Product', price=10.00, stock=5)
        self.user = get_user_model().objects.create_user(username='testuser', password='secret')

    def test_public_product_list_access(self):
        response = self.client.get(reverse('product_list'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.product.name, response.content.decode())

    def test_public_product_detail_access(self):
        response = self.client.get(reverse('product_detail', args=[self.product.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.product.name, response.content.decode())

    def test_add_item_to_cart_guest(self):
        response = self.client.post(reverse('add_to_cart', args=[self.product.pk]), data={'quantity': 2})
        self.assertRedirects(response, reverse('cart_detail'))
        cart = Cart.objects.get(session_key=self.client.session["bizstore_guest_cart"])
        self.assertEqual(cart.items.first().quantity, 2)

    def test_guest_checkout_redirects_to_login(self):
        self.client.post(reverse('add_to_cart', args=[self.product.pk]), data={'quantity': 1})
        response = self.client.get(reverse('checkout'))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('checkout')}")

    def test_cart_merge_on_login(self):
        # Guest adds item
        self.client.post(reverse('add_to_cart', args=[self.product.pk]), data={'quantity': 1})
        # Login
        self.client.login(username='testuser', password='secret')
        # Cart should merged to user cart
        cart = Cart.objects.get(user=self.user)
        self.assertEqual(cart.items.first().quantity, 1)

    def test_add_invalid_quantity(self):
        response = self.client.post(reverse('add_to_cart', args=[self.product.pk]), data={'quantity': -1})
        # Adding an invalid quantity should raise a ValidationError and result in a 400 Bad Request
        self.assertEqual(response.status_code, 400)


    def test_premature_checkout_with_no_items(self):
        response = self.client.get(reverse('checkout'))
        # Expect redirect to login because cart is empty
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('checkout')}")
