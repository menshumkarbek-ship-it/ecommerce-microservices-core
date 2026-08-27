from decimal import Decimal
from io import BytesIO
from unittest.mock import patch

from django.contrib.auth.models import User
from django.contrib.auth.models import Group
from django.core.files.uploadedfile import SimpleUploadedFile
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

    def make_profile_picture(self, filename='avatar.png'):
        from PIL import Image

        image_data = BytesIO()
        Image.new('RGB', (8, 8), color='indigo').save(image_data, format='PNG')
        return SimpleUploadedFile(filename, image_data.getvalue(), content_type='image/png')

    def test_specs_page_renders(self):
        product = self.make_product('Phone', 'phone', '100.00')
        response = self.client.get(reverse('shop:product_specs', args=[product.slug]))
        self.assertEqual(response.status_code, 200)

    def test_homepage_hero_uses_newest_available_phone(self):
        laptop_category = Category.objects.create(name='Laptops', slug='laptops')
        Product.objects.create(
            category=laptop_category,
            brand='Example',
            name='Newest Laptop',
            slug='newest-laptop',
            price=Decimal('900.00'),
            description='A tested laptop.',
        )
        phone = self.make_product('Newest Phone', 'newest-phone', '500.00')

        response = self.client.get(reverse('shop:home'))

        self.assertEqual(response.context['hero_product'], phone)

    @patch('shop.views.send_mail')
    def test_change_password_updates_authenticated_user(self, mock_send_mail):
        self.client.force_login(self.user)

        response = self.client.post(reverse('shop:change_password'), {'action': 'send_code'})
        self.assertEqual(response.status_code, 200)
        self.user.profile.refresh_from_db()
        verification_code = self.user.profile.password_change_otp

        response = self.client.post(reverse('shop:change_password'), {
            'otp_code': verification_code,
            'new_password1': 'new-safe-password-456',
            'new_password2': 'new-safe-password-456',
        })

        self.assertRedirects(response, reverse('shop:account_settings'))
        mock_send_mail.assert_called_once()
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('new-safe-password-456'))

    def test_profile_picture_can_be_uploaded_and_removed(self):
        self.client.force_login(self.user)
        profile = self.user.profile
        profile_data = {
            'username': self.user.username,
            'first_name': '',
            'last_name': '',
            'email': '',
            'phone_number': '',
            'passport_number': 'ID1234567',
        }

        response = self.client.post(
            reverse('shop:account_settings'),
            data={**profile_data, 'profile_picture': self.make_profile_picture()},
        )
        self.assertRedirects(response, reverse('shop:account_settings'))
        profile.refresh_from_db()
        picture_name = profile.profile_picture.name
        self.assertTrue(profile.profile_picture)
        self.assertTrue(profile.profile_picture.storage.exists(picture_name))

        response = self.client.post(
            reverse('shop:account_settings'),
            data={**profile_data, 'remove_profile_picture': 'on'},
        )
        self.assertRedirects(response, reverse('shop:account_settings'))
        profile.refresh_from_db()
        self.assertFalse(profile.profile_picture)
        self.assertFalse(profile.profile_picture.storage.exists(picture_name))

    def test_customer_dropdown_keeps_account_settings_without_payment_link(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse('shop:home'))

        self.assertContains(response, 'Account Settings')
        self.assertNotContains(response, 'Update Payment Method')

    def test_staff_dropdown_shows_admin_tools_without_customer_links(self):
        staff = User.objects.create_user(username='manager', password='manager-password-123', is_staff=True)
        self.client.force_login(staff)

        response = self.client.get(reverse('shop:home'))

        self.assertContains(response, 'Audit Log')
        self.assertContains(response, 'Add Product Portal')
        self.assertContains(response, 'Purchased Orders')
        self.assertContains(response, 'Account Settings')
        self.assertNotContains(response, 'Update Payment Method')

    def test_manager_dropdown_matches_admin_permissions(self):
        manager = User.objects.create_user(username='group-manager', password='manager-password-123')
        manager.groups.add(Group.objects.create(name='Managers'))
        self.client.force_login(manager)

        response = self.client.get(reverse('shop:home'))

        self.assertContains(response, 'Audit Log')
        self.assertContains(response, 'Add Product Portal')
        self.assertContains(response, 'Account Settings')
        self.assertNotContains(response, 'Update Payment Method')

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
