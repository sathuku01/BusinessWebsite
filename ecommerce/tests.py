from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Product, Cart, CartItem, Store, StaffProfile, Order, Customer, OrderItem

User = get_user_model()


class EcommerceFeatureTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.product = Product.objects.create(name='Test Product', price=10.00, stock=5)
        self.user = User.objects.create_user(username='testuser', password='secret')

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


class ThreeTierRoleTests(TestCase):
    def setUp(self):
        self.client = Client()
        
        # Create store
        self.store = Store.objects.create(
            name='Test Store',
            code='TEST',
            address='Test Address'
        )
        
        # Create admin user
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='admin123'
        )
        StaffProfile.objects.create(user=self.admin_user, role='admin', store=self.store)
        
        # Create manager user
        self.manager_user = User.objects.create_user(
            username='manager',
            email='manager@test.com',
            password='manager123'
        )
        StaffProfile.objects.create(user=self.manager_user, role='manager', store=self.store)
        
        # Create customer user (signal creates Customer automatically)
        self.customer_user = User.objects.create_user(
            username='customer',
            email='customer@test.com',
            password='customer123'
        )
        # Get the customer created by signal
        self.customer = Customer.objects.get(user=self.customer_user)
        
        # Create product and order
        self.product = Product.objects.create(name='Test Product', price=100.00, stock=10, store=self.store)
        self.order = Order.objects.create(
            customer=self.customer,
            store=self.store,
            status='pending'
        )
        OrderItem.objects.create(order=self.order, product=self.product, quantity=2, price=100.00)

    def test_admin_can_access_dashboard(self):
        self.client.login(username='admin', password='admin123')
        response = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_manager_can_access_dashboard(self):
        self.client.login(username='manager', password='manager123')
        response = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_customer_cannot_access_dashboard(self):
        self.client.login(username='customer', password='customer123')
        response = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(response.status_code, 302)  # Redirect

    def test_anonymous_cannot_access_dashboard(self):
        response = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_manager_sees_only_store_orders(self):
        # Create another store and order
        other_store = Store.objects.create(name='Other Store', code='OTHER')
        other_product = Product.objects.create(name='Other Product', price=50.00, stock=5, store=other_store)
        other_customer_user = User.objects.create_user(username='other_customer', password='secret')
        other_customer = Customer.objects.get(user=other_customer_user)
        other_order = Order.objects.create(
            customer=other_customer,
            store=other_store,
            status='pending'
        )
        OrderItem.objects.create(order=other_order, product=other_product, quantity=1, price=50.00)
        
        # Manager logs in
        self.client.login(username='manager', password='manager123')
        response = self.client.get(reverse('orders_list'))
        
        # Should only see orders from their store
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, str(self.order.id))
        # Check that other_order is NOT in the orders queryset
        self.assertNotIn(other_order, response.context['orders'])

    def test_admin_sees_all_orders(self):
        # Create another store and order
        other_store = Store.objects.create(name='Other Store', code='OTHER')
        other_product = Product.objects.create(name='Other Product', price=50.00, stock=5, store=other_store)
        other_customer_user = User.objects.create_user(username='other_customer', password='secret')
        other_customer = Customer.objects.get(user=other_customer_user)
        other_order = Order.objects.create(
            customer=other_customer,
            store=other_store,
            status='pending'
        )
        OrderItem.objects.create(order=other_order, product=other_product, quantity=1, price=50.00)
        
        # Admin logs in
        self.client.login(username='admin', password='admin123')
        response = self.client.get(reverse('orders_list'))
        
        # Should see all orders
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, str(self.order.id))
        self.assertContains(response, str(other_order.id))

    def test_manager_can_create_product(self):
        self.client.login(username='manager', password='manager123')
        response = self.client.post(reverse('add_product'), {
            'name': 'New Product',
            'price': '200.00',
            'stock': '5',
            'description': 'Test product',
        })
        self.assertEqual(response.status_code, 302)  # Redirect on success
        self.assertTrue(Product.objects.filter(name='New Product', store=self.store).exists())

    def test_admin_can_manage_staff(self):
        self.client.login(username='admin', password='admin123')
        response = self.client.get(reverse('staff_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'admin')
        self.assertContains(response, 'manager')

    def test_manager_cannot_access_staff_management(self):
        self.client.login(username='manager', password='manager123')
        response = self.client.get(reverse('staff_list'))
        self.assertEqual(response.status_code, 302)  # Redirect

    def test_manager_can_update_order_status(self):
        self.client.login(username='manager', password='manager123')
        response = self.client.post(reverse('update_order_status', args=[self.order.pk]), {
            'status': 'shipped'
        })
        self.assertEqual(response.status_code, 302)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'shipped')

    def test_manager_can_delete_product(self):
        self.client.login(username='manager', password='manager123')
        response = self.client.post(reverse('delete_product', args=[self.product.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Product.objects.filter(pk=self.product.pk).exists())

    def test_customer_can_access_own_orders(self):
        self.client.login(username='customer', password='customer123')
        response = self.client.get(reverse('orders_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, str(self.order.id))

    def test_customer_cannot_access_other_orders(self):
        # Create another customer
        other_customer_user = User.objects.create_user(username='other_customer', password='secret')
        other_customer = Customer.objects.get(user=other_customer_user)
        other_order = Order.objects.create(
            customer=other_customer,
            store=self.store,
            status='pending'
        )
        OrderItem.objects.create(order=other_order, product=self.product, quantity=1, price=100.00)
        
        self.client.login(username='customer', password='customer123')
        response = self.client.get(reverse('order_detail', args=[other_order.pk]))
        self.assertEqual(response.status_code, 404)  # Not found (filtered out)