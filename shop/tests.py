from decimal import Decimal

from django.contrib.auth.models import User, Group
from django.test import TestCase
from django.urls import reverse

from .models import Category, Product, Sale


class StorefrontTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Phones', slug='phones')

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

    def test_product_detail_page_has_no_cart_action(self):
        product = self.make_product('Phone', 'phone', '100.00')
        response = self.client.get(reverse('shop:product_detail', args=[product.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Add to Cart')
        self.assertNotContains(response, '/cart/add/')

    def test_homepage_hero_slide_uses_newest_product_in_featured_category(self):
        self.category.is_featured_in_hero = True
        self.category.save(update_fields=['is_featured_in_hero'])
        self.make_product('Older Phone', 'older-phone', '400.00')
        newest_phone = self.make_product('Newest Phone', 'newest-phone', '500.00')

        response = self.client.get(reverse('shop:home'))

        self.assertEqual(len(response.context['hero_slides']), 1)
        self.assertEqual(response.context['hero_slides'][0]['product'], newest_phone)

    def test_catalog_shows_all_products_without_a_filter(self):
        for i in range(5):
            self.make_product(f'Phone {i}', f'phone-{i}', '100.00')

        response = self.client.get(reverse('shop:product_list'))

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['has_active_filters'])
        self.assertEqual(response.context['products'].paginator.count, 5)

    def test_catalog_filter_narrows_results_but_keeps_pagination(self):
        self.make_product('Matching Phone', 'matching-phone', '100.00')
        other_category = Category.objects.create(name='Tablets', slug='tablets')
        Product.objects.create(
            category=other_category,
            brand='Example',
            name='Other Tablet',
            slug='other-tablet',
            price=Decimal('200.00'),
            description='A tested tablet.',
        )

        response = self.client.get(reverse('shop:product_list'), {'type': 'phones'})

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['has_active_filters'])
        self.assertEqual(response.context['products'].paginator.count, 1)

    def test_anonymous_visitor_sees_no_admin_management_link(self):
        response = self.client.get(reverse('shop:home'))

        self.assertNotContains(response, 'Manage Webpage')

    def test_staff_sees_management_link(self):
        staff = User.objects.create_user(username='manager', password='manager-password-123', is_staff=True)
        self.client.force_login(staff)

        response = self.client.get(reverse('shop:home'))

        self.assertContains(response, 'Manage Webpage')

    def test_manager_group_member_can_reach_add_product_page(self):
        manager = User.objects.create_user(username='group-manager', password='manager-password-123')
        manager.groups.add(Group.objects.create(name='Managers'))
        self.client.force_login(manager)

        response = self.client.get(reverse('shop:create_product'))

        self.assertEqual(response.status_code, 200)

    def test_regular_user_cannot_reach_add_product_page(self):
        user = User.objects.create_user(username='buyer', password='safe-password-123')
        self.client.force_login(user)

        response = self.client.get(reverse('shop:create_product'))

        self.assertRedirects(response, reverse('shop:product_list'))

    def test_add_product_form_offers_brand_suggestions_but_stays_free_text(self):
        self.make_product('Phone', 'phone', '100.00')
        staff = User.objects.create_user(username='manager', password='manager-password-123', is_staff=True)
        self.client.force_login(staff)

        response = self.client.get(reverse('shop:create_product'), {'action': 'new'})

        self.assertContains(response, 'id="brand-suggestions"')
        self.assertContains(response, 'value="Example"')
        self.assertContains(response, 'list="brand-suggestions"')

    def test_staff_can_create_a_new_category(self):
        staff = User.objects.create_user(username='manager', password='manager-password-123', is_staff=True)
        self.client.force_login(staff)

        response = self.client.post(reverse('shop:create_category'), {'name': 'Headphones', 'slug': ''}, follow=True)

        self.assertEqual(response.status_code, 200)
        category = Category.objects.get(name='Headphones')
        self.assertEqual(category.slug, 'headphones')

    def test_regular_user_cannot_create_a_category(self):
        user = User.objects.create_user(username='buyer', password='safe-password-123')
        self.client.force_login(user)

        response = self.client.get(reverse('shop:create_category'))

        self.assertRedirects(response, reverse('shop:product_list'))

    def test_cyrillic_category_name_gets_a_non_empty_transliterated_slug(self):
        staff = User.objects.create_user(username='manager', password='manager-password-123', is_staff=True)
        self.client.force_login(staff)

        self.client.post(reverse('shop:create_category'), {'name': 'Наушники', 'slug': ''})

        category = Category.objects.get(name='Наушники')
        self.assertEqual(category.slug, 'naushniki')
        # The homepage must be able to link to it without raising NoReverseMatch.
        response = self.client.get(reverse('shop:home'))
        self.assertEqual(response.status_code, 200)

    def test_cyrillic_product_name_gets_a_non_empty_transliterated_slug(self):
        staff = User.objects.create_user(username='manager', password='manager-password-123', is_staff=True)
        self.client.force_login(staff)

        self.client.post(reverse('shop:create_product'), {
            'category': self.category.id,
            'brand': 'Sony',
            'name': 'Наушники Про',
            'price': '199.99',
            'description': 'Test description.',
            'slug': '',
        })

        product = Product.objects.get(name='Наушники Про')
        self.assertTrue(product.slug)
        self.assertNotEqual(product.slug, '')

    def test_toggling_category_adds_and_removes_hero_slide(self):
        staff = User.objects.create_user(username='manager', password='manager-password-123', is_staff=True)
        self.client.force_login(staff)
        self.make_product('Phone', 'phone', '100.00')

        self.assertEqual(self.category.is_featured_in_hero, False)
        response = self.client.get(reverse('shop:home'))
        self.assertEqual(response.context['hero_slides'], [])

        self.client.post(reverse('shop:toggle_category_hero', args=[self.category.id]))
        self.category.refresh_from_db()
        self.assertTrue(self.category.is_featured_in_hero)

        response = self.client.get(reverse('shop:home'))
        self.assertEqual(len(response.context['hero_slides']), 1)
        self.assertEqual(response.context['hero_slides'][0]['category'], self.category)

        self.client.post(reverse('shop:toggle_category_hero', args=[self.category.id]))
        response = self.client.get(reverse('shop:home'))
        self.assertEqual(response.context['hero_slides'], [])

    def test_new_category_can_be_created_already_featured_in_hero(self):
        staff = User.objects.create_user(username='manager', password='manager-password-123', is_staff=True)
        self.client.force_login(staff)

        self.client.post(reverse('shop:create_category'), {
            'name': 'Powerbanks', 'slug': '', 'is_featured_in_hero': 'on',
        })

        category = Category.objects.get(name='Powerbanks')
        self.assertTrue(category.is_featured_in_hero)

    def test_regular_user_cannot_toggle_hero_slide(self):
        user = User.objects.create_user(username='buyer', password='safe-password-123')
        self.client.force_login(user)

        response = self.client.post(reverse('shop:toggle_category_hero', args=[self.category.id]))

        self.assertRedirects(response, reverse('shop:product_list'))
        self.category.refresh_from_db()
        self.assertFalse(self.category.is_featured_in_hero)

    def test_removing_a_product_hides_it_but_keeps_the_row_and_records_a_sale(self):
        staff = User.objects.create_user(username='manager', password='manager-password-123', is_staff=True)
        self.client.force_login(staff)
        product = self.make_product('Phone', 'phone', '250.00')

        self.client.post(reverse('shop:delete_product', args=[product.id]))

        # Gone from the storefront...
        self.assertFalse(Product.objects.filter(pk=product.pk).exists())
        self.assertEqual(self.client.get(reverse('shop:product_detail', args=['phone'])).status_code, 404)
        # ...but the row survives, so the removal is recoverable.
        product.refresh_from_db()
        self.assertIsNotNone(product.deleted_at)

        sale = Sale.objects.get(product=product)
        self.assertEqual(sale.price, Decimal('250.00'))
        self.assertEqual(sale.product_name, 'Phone')

    def test_restoring_a_product_puts_it_back_and_drops_the_recorded_sale(self):
        staff = User.objects.create_user(username='manager', password='manager-password-123', is_staff=True)
        self.client.force_login(staff)
        product = self.make_product('Phone', 'phone', '250.00')
        self.client.post(reverse('shop:delete_product', args=[product.id]))

        self.client.post(reverse('shop:restore_product', args=[product.id]))

        self.assertTrue(Product.objects.filter(pk=product.pk).exists())
        self.assertEqual(self.client.get(reverse('shop:product_detail', args=['phone'])).status_code, 200)
        # The sale it recorded must go too, or the month's report stays inflated.
        self.assertEqual(Sale.objects.filter(product=product).count(), 0)

    def test_regular_user_cannot_restore_a_removed_product(self):
        staff = User.objects.create_user(username='manager', password='manager-password-123', is_staff=True)
        self.client.force_login(staff)
        product = self.make_product('Phone', 'phone', '250.00')
        self.client.post(reverse('shop:delete_product', args=[product.id]))
        self.client.logout()

        buyer = User.objects.create_user(username='buyer', password='safe-password-123')
        self.client.force_login(buyer)
        self.client.post(reverse('shop:restore_product', args=[product.id]))

        product.refresh_from_db()
        self.assertIsNotNone(product.deleted_at)

    def test_a_removed_product_keeps_its_slug_and_catalog_number_reserved(self):
        staff = User.objects.create_user(username='manager', password='manager-password-123', is_staff=True)
        self.client.force_login(staff)
        removed = self.make_product('Phone', 'phone', '250.00')
        self.client.post(reverse('shop:delete_product', args=[removed.id]))

        self.client.post(reverse('shop:create_product'), {
            'category': self.category.id, 'brand': 'Example', 'name': 'Phone',
            'price': '300.00', 'description': 'A replacement listing.', 'slug': '',
        })

        replacement = Product.objects.get(price=Decimal('300.00'))
        self.assertNotEqual(replacement.slug, removed.slug)
        self.assertNotEqual(replacement.category_number, removed.category_number)

    def test_removed_product_is_absent_from_catalog_and_api(self):
        staff = User.objects.create_user(username='manager', password='manager-password-123', is_staff=True)
        self.client.force_login(staff)
        product = self.make_product('Phone', 'phone', '250.00')
        self.client.post(reverse('shop:delete_product', args=[product.id]))

        self.assertEqual(self.client.get(reverse('shop:product_list')).context['products'].paginator.count, 0)
        self.assertEqual(self.client.get('/api/products/').json()['results'], [])

    def test_api_list_is_paginated_and_avoids_a_query_per_product(self):
        for i in range(6):
            self.make_product(f'Phone {i}', f'phone-{i}', '100.00')

        with self.assertNumQueries(2):  # one count for paging, one for the page
            payload = self.client.get('/api/products/').json()

        self.assertEqual(payload['count'], 6)
        self.assertIn('results', payload)
        # The nested category must come from the join, not a lookup per row.
        self.assertEqual(payload['results'][0]['category']['slug'], 'phones')

    def test_homepage_gets_a_row_for_every_category_with_stock(self):
        headphones = Category.objects.create(name='Headphones', slug='headphones')
        Product.objects.create(
            category=headphones,
            brand='Sony',
            name='WH-1000XM5',
            slug='wh-1000xm5',
            price=Decimal('349.00'),
            description='Noise-cancelling headphones.',
        )
        self.make_product('Phone', 'phone', '100.00')

        response = self.client.get(reverse('shop:home'))

        sections = {s['category'].slug: s for s in response.context['category_sections']}
        self.assertIn('headphones', sections)
        self.assertIn('phones', sections)
        self.assertContains(response, 'Newest In Headphones')
