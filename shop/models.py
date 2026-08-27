from io import BytesIO
from PIL import Image, ImageOps
from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.validators import RegexValidator
from django.db import models


# ==========================================
# 👤 USER PROFILE & KYC EXTENSION
# ==========================================

class UserProfile(models.Model):
    VERIFICATION_METHOD_CHOICES = (
        ('email', 'Email Verification'),
        ('phone', 'Phone Verification'),
    )

    KYC_STATUS_CHOICES = (
        ('pending', 'Pending Verification'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')

    # Valid Kyrgyz Passport (Format: ID1234567 or AN1234567)
    passport_number = models.CharField(
        max_length=9,
        unique=True,
        blank=True,
        null=True,
        help_text="Legacy field retained for existing accounts."
    )

    # Preferred Verification Route
    verification_method = models.CharField(max_length=10, default='email')

    # Phone Verification (+996 format)
    phone_number = models.CharField(
        max_length=13,
        blank=True,
        null=True,
        validators=[
            RegexValidator(
                regex=r'^\+996\d{9}$',
                message="Phone number must be in Kyrgyz format: +996XXXXXXXXX"
            )
        ]
    )
    phone_otp = models.CharField(max_length=6, blank=True, null=True)
    is_phone_verified = models.BooleanField(default=False)

    # Email Verification
    email_otp = models.CharField(max_length=6, blank=True, null=True)
    is_email_verified = models.BooleanField(default=False)
    password_change_otp = models.CharField(max_length=6, blank=True, null=True)
    password_change_otp_created_at = models.DateTimeField(blank=True, null=True)

    # KYC Verification Status
    kyc_status = models.CharField(max_length=10, choices=KYC_STATUS_CHOICES, default='pending')

    registration_date = models.DateTimeField(auto_now_add=True)
    profile_picture = models.ImageField(upload_to="profile_pics/", blank=True, null=True)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"


# ==========================================
# 🏷️ CATEGORY MANAGEMENT
# ==========================================

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

    def __str__(self):
        return self.name


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

    def __str__(self):
        status = "SOLD" if self.is_sold else "AVAILABLE"
        return f"[{status}] {self.brand} - {self.name}"

    def save(self, *args, **kwargs):
        if self.image and hasattr(self.image, 'file'):
            try:
                img = Image.open(self.image)
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')

                datas = img.getdata()
                new_data = []
                for item in datas:
                    if item[0] > 240 and item[1] > 240 and item[2] > 240:
                        new_data.append((255, 255, 255, 0))
                    else:
                        new_data.append(item)

                img.putdata(new_data)
                canvas_size = (700, 700)
                cropped_img = ImageOps.fit(img, canvas_size, method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))

                buffer = BytesIO()
                cropped_img.save(buffer, format='PNG', quality=90)
                buffer.seek(0)

                clean_filename = f"{self.slug if self.slug else 'device'}_nobg.png"
                self.image.save(clean_filename, ContentFile(buffer.read()), save=False)
            except Exception as exc:
                print(f"[IMAGE PROCESSOR NOTICE] Error processing background: {exc}")

        super().save(*args, **kwargs)


# ==========================================
# 🧾 ORDER & TRANSACTION RECORDING
# ==========================================

class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.id} by {self.user.username}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.product.name} (Order #{self.order.id})"