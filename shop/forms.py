from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Product, Category, ContactSettings, AboutPageContent
from .utils import build_unique_slug

# Shared widget styling for the many near-identical translated-field inputs
# added below (Russian/Kyrgyz variants of name/description/heading/etc.),
# kept as constants so all of them stay visually consistent.
TEXT_INPUT_CLASS = 'w-full bg-slate-800/80 border border-slate-700/80 rounded-2xl px-4 py-3 text-sm text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all'
TEXTAREA_CLASS = TEXT_INPUT_CLASS


# ==========================================
# 📦 PRODUCT CREATION & UPDATE FORM
# ==========================================

class ProductCreateForm(forms.ModelForm):
    slug = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full bg-slate-800/80 border border-slate-700/80 rounded-2xl px-4 py-3 text-sm text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all',
            'placeholder': _('Auto-generated if empty (e.g., iphone-15-pro-max)')
        })
    )

    description = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full bg-slate-800/80 border border-slate-700/80 rounded-2xl px-4 py-3 text-sm text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all',
            'placeholder': _('Describe the product, condition, and included accessories.'),
            'rows': 4,
        })
    )

    class Meta:
        model = Product
        fields = [
            'category', 'brand', 'name', 'name_ru', 'name_ky', 'slug', 'price',
            'description', 'description_ru', 'description_ky', 'image',
        ]
        widgets = {
            'category': forms.Select(attrs={'class': 'w-full bg-slate-800/80 border border-slate-700/80 rounded-2xl px-4 py-3 text-sm text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all cursor-pointer'}),
            'brand': forms.TextInput(attrs={'class': 'w-full bg-slate-800/80 border border-slate-700/80 rounded-2xl px-4 py-3 text-sm text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all', 'placeholder': _('Type any brand, e.g. Apple, Samsung, Anker...'), 'list': 'brand-suggestions', 'autocomplete': 'off'}),
            'name': forms.TextInput(attrs={'class': 'w-full bg-slate-800/80 border border-slate-700/80 rounded-2xl px-4 py-3 text-sm text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all', 'placeholder': _('e.g., iPhone 15 Pro Max')}),
            'name_ru': forms.TextInput(attrs={'class': TEXT_INPUT_CLASS, 'placeholder': _('Optional — falls back to the title above if left blank')}),
            'name_ky': forms.TextInput(attrs={'class': TEXT_INPUT_CLASS, 'placeholder': _('Optional — falls back to the title above if left blank')}),
            'price': forms.NumberInput(attrs={'class': 'w-full bg-slate-800/80 border border-slate-700/80 rounded-2xl px-4 py-3 text-sm text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all', 'placeholder': '999.99'}),
            'description_ru': forms.Textarea(attrs={'class': TEXTAREA_CLASS, 'placeholder': _('Optional — falls back to the description above if left blank'), 'rows': 4}),
            'description_ky': forms.Textarea(attrs={'class': TEXTAREA_CLASS, 'placeholder': _('Optional — falls back to the description above if left blank'), 'rows': 4}),
            'image': forms.FileInput(attrs={'class': 'text-sm text-slate-400 file:mr-4 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-xs file:font-bold file:bg-indigo-600 file:text-white hover:file:bg-indigo-500 cursor-pointer'}),
        }

    def clean_slug(self):
        slug = self.cleaned_data.get('slug')
        name = self.cleaned_data.get('name')

        qs = Product.objects.all()
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if not slug and name:
            return build_unique_slug(name, qs, fallback_prefix='product')

        if qs.filter(slug=slug).exists():
            return build_unique_slug(slug, qs, fallback_prefix='product')

        return slug

    def save(self, commit=True):
        # Note: 'specifications' isn't a form field (the RAM/Storage/Screen/
        # Processor panel was removed from the add-product UI), so any
        # existing value on the instance is left untouched here.
        product = super().save(commit=False)

        if commit:
            product.save()
        return product


# ==========================================
# 🏷️ CATEGORY CREATION FORM
# ==========================================

class CategoryCreateForm(forms.ModelForm):
    slug = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full bg-slate-800/80 border border-slate-700/80 rounded-2xl px-4 py-3 text-sm text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all',
            'placeholder': _('Auto-generated if empty (e.g., headphones)')
        })
    )
    is_featured_in_hero = forms.BooleanField(
        required=False,
        label=_("Show as a homepage announcement slide"),
        widget=forms.CheckboxInput(attrs={
            'class': 'h-4 w-4 rounded border-slate-700 bg-slate-800 text-indigo-600 focus:ring-indigo-500'
        })
    )
    show_newest_row = forms.BooleanField(
        required=False,
        initial=True,
        label=_('Show a "Newest In" row for this category on the homepage'),
        widget=forms.CheckboxInput(attrs={
            'class': 'h-4 w-4 rounded border-slate-700 bg-slate-800 text-indigo-600 focus:ring-indigo-500'
        })
    )

    class Meta:
        model = Category
        fields = ['name', 'name_ru', 'name_ky', 'slug', 'is_featured_in_hero', 'show_newest_row']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full bg-slate-800/80 border border-slate-700/80 rounded-2xl px-4 py-3 text-sm text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all',
                'placeholder': _('e.g., Headphones, Powerbanks, Smartwatches')
            }),
            'name_ru': forms.TextInput(attrs={'class': TEXT_INPUT_CLASS, 'placeholder': _('Optional — falls back to the name above if left blank')}),
            'name_ky': forms.TextInput(attrs={'class': TEXT_INPUT_CLASS, 'placeholder': _('Optional — falls back to the name above if left blank')}),
        }

    def clean_slug(self):
        slug = self.cleaned_data.get('slug')
        name = self.cleaned_data.get('name')

        qs = Category.objects.all()
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if not slug and name:
            return build_unique_slug(name, qs, fallback_prefix='category')

        if qs.filter(slug=slug).exists():
            return build_unique_slug(slug, qs, fallback_prefix='category')

        return slug


# ==========================================
# ☎️ CONTACT SETTINGS FORM
# ==========================================

class ContactSettingsForm(forms.ModelForm):
    class Meta:
        model = ContactSettings
        fields = ['email', 'phone_number', 'whatsapp_number', 'telegram_username', 'instagram_username']
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'w-full bg-slate-800/80 border border-slate-700/80 rounded-2xl px-4 py-3 text-sm text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all',
                'placeholder': 'support@example.com'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'w-full bg-slate-800/80 border border-slate-700/80 rounded-2xl px-4 py-3 text-sm text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all',
                'placeholder': '+996 700 123 456'
            }),
            'whatsapp_number': forms.TextInput(attrs={
                'class': 'w-full bg-slate-800/80 border border-slate-700/80 rounded-2xl px-4 py-3 text-sm text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all',
                'placeholder': _('996700123456 (country code, digits only)')
            }),
            'telegram_username': forms.TextInput(attrs={
                'class': 'w-full bg-slate-800/80 border border-slate-700/80 rounded-2xl px-4 py-3 text-sm text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all',
                'placeholder': _('techvault_support (no @)')
            }),
            'instagram_username': forms.TextInput(attrs={
                'class': 'w-full bg-slate-800/80 border border-slate-700/80 rounded-2xl px-4 py-3 text-sm text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all',
                'placeholder': _('techvault.shop (no @)')
            }),
        }


# ==========================================
# 📖 ABOUT PAGE CONTENT FORM
# ==========================================

class AboutPageContentForm(forms.ModelForm):
    class Meta:
        model = AboutPageContent
        fields = [
            'site_name', 'site_name_ru', 'site_name_ky',
            'badge_text', 'badge_text_ru', 'badge_text_ky',
            'heading', 'heading_ru', 'heading_ky',
            'intro_text', 'intro_text_ru', 'intro_text_ky',
            'visit_heading', 'visit_heading_ru', 'visit_heading_ky',
            'visit_text', 'visit_text_ru', 'visit_text_ky',
            'store_address_line1', 'store_address_line1_ru', 'store_address_line1_ky',
            'store_address_line2', 'store_address_line2_ru', 'store_address_line2_ky',
            'store_image',
            'cta_heading', 'cta_heading_ru', 'cta_heading_ky',
            'cta_text', 'cta_text_ru', 'cta_text_ky',
        ]
        widgets = {
            'site_name': forms.TextInput(attrs={'class': TEXT_INPUT_CLASS, 'placeholder': 'TechVault'}),
            'site_name_ru': forms.TextInput(attrs={'class': TEXT_INPUT_CLASS, 'placeholder': _('Optional — falls back to the name above if left blank')}),
            'site_name_ky': forms.TextInput(attrs={'class': TEXT_INPUT_CLASS, 'placeholder': _('Optional — falls back to the name above if left blank')}),

            'badge_text': forms.TextInput(attrs={'class': TEXT_INPUT_CLASS, 'placeholder': _('Family Owned Since 2010')}),
            'badge_text_ru': forms.TextInput(attrs={'class': TEXT_INPUT_CLASS, 'placeholder': _('Optional — falls back to the text above if left blank')}),
            'badge_text_ky': forms.TextInput(attrs={'class': TEXT_INPUT_CLASS, 'placeholder': _('Optional — falls back to the text above if left blank')}),

            'heading': forms.TextInput(attrs={'class': TEXT_INPUT_CLASS, 'placeholder': 'About TechVault'}),
            'heading_ru': forms.TextInput(attrs={'class': TEXT_INPUT_CLASS, 'placeholder': _('Optional — falls back to the heading above if left blank')}),
            'heading_ky': forms.TextInput(attrs={'class': TEXT_INPUT_CLASS, 'placeholder': _('Optional — falls back to the heading above if left blank')}),

            'intro_text': forms.Textarea(attrs={'class': TEXTAREA_CLASS, 'placeholder': _('Tell customers about your shop and your market...'), 'rows': 5}),
            'intro_text_ru': forms.Textarea(attrs={'class': TEXTAREA_CLASS, 'placeholder': _('Optional — falls back to the story above if left blank'), 'rows': 5}),
            'intro_text_ky': forms.Textarea(attrs={'class': TEXTAREA_CLASS, 'placeholder': _('Optional — falls back to the story above if left blank'), 'rows': 5}),

            'visit_heading': forms.TextInput(attrs={'class': TEXT_INPUT_CLASS, 'placeholder': _('See It In Person')}),
            'visit_heading_ru': forms.TextInput(attrs={'class': TEXT_INPUT_CLASS, 'placeholder': _('Optional — falls back to the heading above if left blank')}),
            'visit_heading_ky': forms.TextInput(attrs={'class': TEXT_INPUT_CLASS, 'placeholder': _('Optional — falls back to the heading above if left blank')}),

            'visit_text': forms.Textarea(attrs={'class': TEXTAREA_CLASS, 'placeholder': _('Invite customers to visit your store in person...'), 'rows': 3}),
            'visit_text_ru': forms.Textarea(attrs={'class': TEXTAREA_CLASS, 'placeholder': _('Optional — falls back to the text above if left blank'), 'rows': 3}),
            'visit_text_ky': forms.Textarea(attrs={'class': TEXTAREA_CLASS, 'placeholder': _('Optional — falls back to the text above if left blank'), 'rows': 3}),

            'store_address_line1': forms.TextInput(attrs={'class': TEXT_INPUT_CLASS, 'placeholder': '100 Tech Vault Plaza, Suite 404'}),
            'store_address_line1_ru': forms.TextInput(attrs={'class': TEXT_INPUT_CLASS, 'placeholder': _('Optional — falls back to the address above if left blank')}),
            'store_address_line1_ky': forms.TextInput(attrs={'class': TEXT_INPUT_CLASS, 'placeholder': _('Optional — falls back to the address above if left blank')}),

            'store_address_line2': forms.TextInput(attrs={'class': TEXT_INPUT_CLASS, 'placeholder': 'Silicon District, CA 94016'}),
            'store_address_line2_ru': forms.TextInput(attrs={'class': TEXT_INPUT_CLASS, 'placeholder': _('Optional — falls back to the address above if left blank')}),
            'store_address_line2_ky': forms.TextInput(attrs={'class': TEXT_INPUT_CLASS, 'placeholder': _('Optional — falls back to the address above if left blank')}),

            'store_image': forms.FileInput(attrs={
                'class': 'text-sm text-slate-400 file:mr-4 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-xs file:font-bold file:bg-indigo-600 file:text-white hover:file:bg-indigo-500 cursor-pointer'
            }),

            'cta_heading': forms.TextInput(attrs={'class': TEXT_INPUT_CLASS, 'placeholder': _('Ready to Find Your Next Device?')}),
            'cta_heading_ru': forms.TextInput(attrs={'class': TEXT_INPUT_CLASS, 'placeholder': _('Optional — falls back to the heading above if left blank')}),
            'cta_heading_ky': forms.TextInput(attrs={'class': TEXT_INPUT_CLASS, 'placeholder': _('Optional — falls back to the heading above if left blank')}),

            'cta_text': forms.Textarea(attrs={'class': TEXTAREA_CLASS, 'placeholder': _('Invite customers to browse or get in touch...'), 'rows': 3}),
            'cta_text_ru': forms.Textarea(attrs={'class': TEXTAREA_CLASS, 'placeholder': _('Optional — falls back to the text above if left blank'), 'rows': 3}),
            'cta_text_ky': forms.Textarea(attrs={'class': TEXTAREA_CLASS, 'placeholder': _('Optional — falls back to the text above if left blank'), 'rows': 3}),
        }
