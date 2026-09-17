from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q
from django.utils.text import slugify

from shop.models import Category, Product
from shop.seed.catalog import CATEGORIES, PRODUCTS
from shop.seed.illustrations import render_product_image


class Command(BaseCommand):
    help = (
        'Fill an empty or thin catalog with ~60 gadgets across 8 categories. '
        'Safe to re-run: existing categories are reused by slug and a product '
        'whose slug already exists (even a removed one) is left alone.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--no-images', action='store_true',
            help='Skip generating illustrations (faster; products get no photo).',
        )

    def handle(self, *args, **options):
        categories = {}
        for spec in CATEGORIES:
            category, created = self._get_or_create_category(spec)
            categories[spec['key']] = (category, spec)
            self.stdout.write(f"{'Created' if created else 'Using'} category: {category.name} (/{category.slug}/)")

        added = skipped = 0
        for item in PRODUCTS:
            category, spec = categories[item['category']]
            slug = slugify(f"{item['brand']}-{item['name']}")
            # all_objects: a product the owner removed stays removed rather
            # than coming back as a fresh listing on the next seed run.
            if Product.all_objects.filter(slug=slug).exists():
                skipped += 1
                continue

            with transaction.atomic():
                product = Product(
                    category=category, brand=item['brand'], name=item['name'], slug=slug,
                    price=item['price'], description=item['description'],
                    description_ru=item['description_ru'], specifications=item['specifications'],
                )
                if not options['no_images']:
                    png = render_product_image(item['shape'] or spec['shape'], item['brand'], item['name'], spec['accent'])
                    # Assigned before save() so the model's background-removal
                    # step runs on it exactly like an uploaded photo.
                    product.image = ContentFile(png, name=f'{slug}.png')
                product.save()
            added += 1
            self.stdout.write(f"  + {item['brand']} {item['name']}")

        self.stdout.write(self.style.SUCCESS(
            f'Seed complete: {added} products added, {skipped} already present, '
            f'{Product.objects.count()} in the catalog now.'
        ))

    @staticmethod
    def _get_or_create_category(spec):
        """Reuse a category that already exists under any of the slugs this
        one has gone by (or one of its names); otherwise create it under the
        first slug."""
        # Category.name is unique too, so a store that already has "Monitor"
        # under some other slug must be matched by name, not collided with.
        existing = Category.objects.filter(
            Q(slug__in=spec['slugs']) | Q(name__in=[spec['name'], spec['name_ru']])
        ).first()
        if existing:
            # Fill in translations the owner never entered, but never rename
            # a category they already have.
            changed = []
            for field in ('name_ru', 'name_ky'):
                if not getattr(existing, field):
                    setattr(existing, field, spec[field])
                    changed.append(field)
            if changed:
                existing.save(update_fields=changed)
            return existing, False

        category = Category.objects.create(
            name=spec['name'], slug=spec['slugs'][0],
            name_ru=spec['name_ru'], name_ky=spec['name_ky'],
            is_featured_in_hero=spec['hero'], show_newest_row=True,
        )
        return category, True
