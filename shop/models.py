from django.db import models
from .utils import process_no_bg_image, translatable_property


# ==========================================
# 🏷️ CATEGORY MANAGEMENT
# ==========================================

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    is_featured_in_hero = models.BooleanField(
        default=False,
        help_text="Show this category's newest in-stock product as an auto-rotating homepage announcement slide."
    )
    show_newest_row = models.BooleanField(
        default=True,
        help_text="Show this category's own \"Newest In\" slideshow row on the homepage."
    )

    # Per-language name overrides: `name` above is the default/fallback.
    # Leave either blank to fall back to `name` for that language. The slug
    # (used in URLs) is intentionally NOT translated.
    name_ru = models.CharField(max_length=100, blank=True, verbose_name="Name (Russian)")
    name_ky = models.CharField(max_length=100, blank=True, verbose_name="Name (Kyrgyz)")

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

    def __str__(self):
        return self.name

    translated_name = translatable_property('name')


# ==========================================
# ☎️ CONTACT SETTINGS (SINGLETON)
# ==========================================

class ContactSettings(models.Model):
    """
    Store-wide contact channels, editable by the admin from Django admin.
    Only one row ever exists (enforced via save()); the shop.contact_settings
    context processor exposes it to every template as `contact_settings`.
    """
    email = models.EmailField(
        blank=True,
        help_text="Public support email shown on the Contact page."
    )
    phone_number = models.CharField(
        max_length=32, blank=True,
        help_text="Phone number for calls/SMS, e.g. +996700123456"
    )
    whatsapp_number = models.CharField(
        max_length=32, blank=True,
        help_text="WhatsApp number with country code, digits only, e.g. 996700123456"
    )
    telegram_username = models.CharField(
        max_length=100, blank=True,
        help_text="Telegram username without the @, e.g. techvault_support"
    )
    instagram_username = models.CharField(
        max_length=100, blank=True,
        help_text="Instagram username without the @, e.g. techvault.shop"
    )

    class Meta:
        verbose_name = "Contact Settings"
        verbose_name_plural = "Contact Settings"

    def __str__(self):
        return "Contact Settings"

    def save(self, *args, **kwargs):
        # Enforce a single row: this table only ever holds the store's one
        # shared set of contact channels.
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Never allow deleting the singleton row from anywhere in the app.
        pass

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    @property
    def whatsapp_digits(self):
        return ''.join(ch for ch in self.whatsapp_number if ch.isdigit())

    @property
    def phone_digits(self):
        digits = ''.join(ch for ch in self.phone_number if ch.isdigit() or ch == '+')
        return digits

    @property
    def telegram_handle(self):
        return self.telegram_username.lstrip('@').strip()

    @property
    def instagram_handle(self):
        return self.instagram_username.lstrip('@').strip()


# ==========================================
# 📖 ABOUT PAGE CONTENT (SINGLETON)
# ==========================================

class AboutPageContent(models.Model):
    """
    Store-wide site identity and "About Us" page copy, editable by the admin
    from the in-app management panel. Singleton like ContactSettings: only
    one row ever exists (enforced via save()).
    """
    site_name = models.CharField(
        max_length=60, default="TechVault",
        help_text="The store/market name shown in the navbar, browser tab, and footer across the whole site."
    )
    badge_text = models.CharField(
        max_length=100, blank=True, default="Enterprise Architecture",
        help_text="Small pill label above the page heading, e.g. 'Family Owned Since 2010'."
    )
    heading = models.CharField(max_length=150, default="About TechVault")
    intro_text = models.TextField(
        default=(
            "TechVault is an online showcase for the phones, laptops, and tablets we carry. "
            "Browse the full catalog, compare specifications, and find your next device before you visit us."
        ),
        help_text="The main story paragraph under the heading. Write about your shop, your market, and what makes you different."
    )

    visit_heading = models.CharField(max_length=150, blank=True, default="See It In Person")
    visit_text = models.TextField(
        blank=True,
        default=(
            "This catalog is for browsing: use it to compare specifications and shortlist the devices you like, "
            "then stop by our store to see them up close and speak with our team."
        )
    )
    store_address_line1 = models.CharField(max_length=200, blank=True, default="100 Tech Vault Plaza, Suite 404")
    store_address_line2 = models.CharField(max_length=200, blank=True, default="Silicon District, CA 94016")
    store_image = models.ImageField(
        upload_to='about/', blank=True, null=True,
        help_text="Optional photo of your storefront. Falls back to a generic map graphic if left empty."
    )

    cta_heading = models.CharField(max_length=150, blank=True, default="Ready to Find Your Next Device?")
    cta_text = models.TextField(
        blank=True,
        default="Browse our full catalog of phones, laptops, and tablets, then visit us in-store or get in touch to learn more."
    )

    # Per-language overrides for every field above. Each defaults to blank
    # and falls back to the base (English) field when empty, so filling
    # these in is entirely optional per language.
    site_name_ru = models.CharField(max_length=60, blank=True, verbose_name="Store / Market Name (Russian)")
    site_name_ky = models.CharField(max_length=60, blank=True, verbose_name="Store / Market Name (Kyrgyz)")
    badge_text_ru = models.CharField(max_length=100, blank=True, verbose_name="Badge Text (Russian)")
    badge_text_ky = models.CharField(max_length=100, blank=True, verbose_name="Badge Text (Kyrgyz)")
    heading_ru = models.CharField(max_length=150, blank=True, verbose_name="Page Heading (Russian)")
    heading_ky = models.CharField(max_length=150, blank=True, verbose_name="Page Heading (Kyrgyz)")
    intro_text_ru = models.TextField(blank=True, verbose_name="Your Story (Russian)")
    intro_text_ky = models.TextField(blank=True, verbose_name="Your Story (Kyrgyz)")
    visit_heading_ru = models.CharField(max_length=150, blank=True, verbose_name="Visit Section Heading (Russian)")
    visit_heading_ky = models.CharField(max_length=150, blank=True, verbose_name="Visit Section Heading (Kyrgyz)")
    visit_text_ru = models.TextField(blank=True, verbose_name="Visit Section Text (Russian)")
    visit_text_ky = models.TextField(blank=True, verbose_name="Visit Section Text (Kyrgyz)")
    store_address_line1_ru = models.CharField(max_length=200, blank=True, verbose_name="Address Line 1 (Russian)")
    store_address_line1_ky = models.CharField(max_length=200, blank=True, verbose_name="Address Line 1 (Kyrgyz)")
    store_address_line2_ru = models.CharField(max_length=200, blank=True, verbose_name="Address Line 2 (Russian)")
    store_address_line2_ky = models.CharField(max_length=200, blank=True, verbose_name="Address Line 2 (Kyrgyz)")
    cta_heading_ru = models.CharField(max_length=150, blank=True, verbose_name="Banner Heading (Russian)")
    cta_heading_ky = models.CharField(max_length=150, blank=True, verbose_name="Banner Heading (Kyrgyz)")
    cta_text_ru = models.TextField(blank=True, verbose_name="Banner Text (Russian)")
    cta_text_ky = models.TextField(blank=True, verbose_name="Banner Text (Kyrgyz)")

    class Meta:
        verbose_name = "About Page Content"
        verbose_name_plural = "About Page Content"

    def __str__(self):
        return "About Page Content"

    def save(self, *args, **kwargs):
        # Enforce a single row: the About page only ever has one shared copy.
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Never allow deleting the singleton row from anywhere in the app.
        pass

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    translated_site_name = translatable_property('site_name')
    translated_badge_text = translatable_property('badge_text')
    translated_heading = translatable_property('heading')
    translated_intro_text = translatable_property('intro_text')
    translated_visit_heading = translatable_property('visit_heading')
    translated_visit_text = translatable_property('visit_text')
    translated_store_address_line1 = translatable_property('store_address_line1')
    translated_store_address_line2 = translatable_property('store_address_line2')
    translated_cta_heading = translatable_property('cta_heading')
    translated_cta_text = translatable_property('cta_text')


# ==========================================
# 📱 PRODUCT CATALOG & AUTOMATED NO-BG PROCESSOR
# ==========================================

class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    brand = models.CharField(max_length=100, db_index=True, help_text="e.g., Apple, Samsung, Asus")
    name = models.CharField(max_length=255, db_index=True)
    slug = models.SlugField(max_length=255, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, db_index=True)
    description = models.TextField()
    image = models.ImageField(upload_to='products/', blank=True, null=True)

    # Per-language overrides for name/description. `name`/`description` above
    # are the default/fallback; leave either blank to fall back for that
    # language. Brand, price, and slug are intentionally not translated.
    name_ru = models.CharField(max_length=255, blank=True, verbose_name="Product Title (Russian)")
    name_ky = models.CharField(max_length=255, blank=True, verbose_name="Product Title (Kyrgyz)")
    description_ru = models.TextField(blank=True, verbose_name="Product Description (Russian)")
    description_ky = models.TextField(blank=True, verbose_name="Product Description (Kyrgyz)")

    # A short, stable, per-category catalog number (0, 1, 2, ...), assigned
    # once when the product is first created and never changed afterward.
    # Shown to customers on product cards, and lets an admin quickly find and
    # delete the exact listing once it's sold, by searching for its number
    # instead of scrolling through the whole catalog.
    category_number = models.PositiveIntegerField(default=0, db_index=True)

    specifications = models.JSONField(
        default=dict,
        help_text="Store characteristics as JSON. (e.g., {'RAM': '16GB', 'Storage': '512GB'})"
    )

    is_sold = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_sold', 'brand']),
            models.Index(fields=['is_sold', '-created_at']),
        ]
        constraints = [
            models.UniqueConstraint(fields=['category', 'category_number'], name='unique_category_number_per_category'),
        ]

    def __str__(self):
        status = "SOLD" if self.is_sold else "AVAILABLE"
        return f"[{status}] {self.brand} - {self.name} (#{self.category_number})"

    @property
    def catalog_code(self):
        """Short, human-friendly, searchable code shown on cards, e.g. 'PHONES-3'."""
        prefix = ''.join(ch for ch in self.category.name.upper() if ch.isalnum())[:6] or 'ITEM'
        return f"{prefix}-{self.category_number}"

    translated_name = translatable_property('name')
    translated_description = translatable_property('description')

    def save(self, *args, **kwargs):
        if self.pk is None and self.category_id:
            last_number = Product.objects.filter(category_id=self.category_id).aggregate(
                models.Max('category_number')
            )['category_number__max']
            self.category_number = 0 if last_number is None else last_number + 1

        if self.image and hasattr(self.image, 'file'):
            try:
                filename, content = process_no_bg_image(self.image, self.slug if self.slug else 'device')
                self.image.save(filename, content, save=False)
            except Exception as exc:
                print(f"[IMAGE PROCESSOR NOTICE] Error processing background: {exc}")

        super().save(*args, **kwargs)


# ==========================================
# 🖼️ PRODUCT GALLERY (ADDITIONAL PHOTOS)
# ==========================================

class ProductImage(models.Model):
    """
    Extra photos for a product, beyond the single primary `Product.image`.
    Admins can upload several images per product from the management panel;
    each gets the same background-removal treatment as the primary photo so
    the whole gallery looks consistent.
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='gallery_images')
    image = models.ImageField(upload_to='products/gallery/')
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'created_at']

    def __str__(self):
        return f"Photo for {self.product.name} (#{self.pk})"

    def save(self, *args, **kwargs):
        if self.image and hasattr(self.image, 'file'):
            try:
                prefix = f"{self.product.slug if self.product_id else 'device'}-gallery-{self.pk or 'new'}"
                filename, content = process_no_bg_image(self.image, prefix)
                self.image.save(filename, content, save=False)
            except Exception as exc:
                print(f"[IMAGE PROCESSOR NOTICE] Error processing gallery photo background: {exc}")

        super().save(*args, **kwargs)
