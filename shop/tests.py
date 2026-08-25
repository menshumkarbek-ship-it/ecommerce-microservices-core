from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Category, Order, Product, UserProfile


class StorefrontTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Phones', slug='phones')
        self.user = User.objects.create_user(username='buyer', password='safe-password-123')
        UserProfile.objects.create(
            user=self.user,
            passport_number='ID1234567',
            verification_method='email',
            is_email_verified=True,
            kyc_status='verified',
        )

    def make_product(self, name, slug, price):
        return Product.objects.create(
            category=self.category,
            brand='Example',
            name=name,
            slug=slug,
            price=Decimal(price),
            description='A tested product.',
        )

    def test_specs_page_renders(self):
        product = self.make_product('Phone', 'phone', '100.00')
        response = self.client.get(reverse('shop:product_specs', args=[product.slug]))
        self.assertEqual(response.status_code, 200)

    @patch('shop.views.requests.post')
    def test_checkout_processes_every_cart_item(self, mock_post):
        first = self.make_product('Phone', 'phone', '100.00')
        second = self.make_product('Tablet', 'tablet', '200.00')
        self.client.force_login(self.user)
        self.client.post(reverse('shop:cart_add', args=[first.id]))
        self.client.post(reverse('shop:cart_add', args=[second.id]))
        mock_post.return_value.status_code = 201

        response = self.client.post(reverse('shop:checkout_order'))

        self.assertRedirects(response, reverse('shop:product_list'))
        order = Order.objects.get(user=self.user)
        self.assertEqual(order.total_price, Decimal('300.00'))
        self.assertEqual(order.items.count(), 2)
        self.assertFalse(Product.objects.filter(id__in=[first.id, second.id], is_sold=False).exists())

    def test_cart_mutation_routes_require_post(self):
        product = self.make_product('Phone', 'phone', '100.00')
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse('shop:cart_remove', args=[product.id])).status_code, 405)
        self.assertEqual(self.client.get(reverse('shop:checkout_order')).status_code, 405)
