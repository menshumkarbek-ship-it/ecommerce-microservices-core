import re
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.utils.text import slugify
from .models import UserProfile, Product, Category


# ==========================================
# 🔐 CUSTOMER REGISTRATION FORM (WITH KYC & OTP)
# ==========================================

class CustomerRegistrationForm(forms.ModelForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'w-full bg-slate-800/80 border border-slate-700/80 rounded-2xl px-4 py-3 text-sm text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/50',
            'placeholder': 'Username'
        })
    )
    first_name = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'w-full bg-slate-800/80 border border-slate-700/80 rounded-2xl px-4 py-3 text-sm text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/50',
            'placeholder': 'First Name'
        })
    )
    last_name = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'w-full bg-slate-800/80 border border-slate-700/80 rounded-2xl px-4 py-3 text-sm text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/50',
            'placeholder': 'Last Name'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full bg-slate-800/80 border border-slate-700/80 rounded-2xl px-4 py-3 text-sm text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/50',
            'placeholder': 'Password (Min. 8 characters)'
        })
    )
    passport_number = forms.CharField(
        max_length=9,
        widget=forms.TextInput(attrs={
            'class': 'w-full bg-slate-800/80 border border-slate-700/80 rounded-2xl px-4 py-3 text-sm text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/50',
            'placeholder': 'ID1234567 or AN1234567'
        })
    )
    verification_method = forms.ChoiceField(
        choices=UserProfile.VERIFICATION_METHOD_CHOICES,
        widget=forms.Select(attrs={
            'class': 'w-full bg-slate-800/80 border border-slate-700/80 rounded-2xl px-4 py-3 text-sm text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 cursor-pointer'
        })
    )
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'w-full bg-slate-800/80 border border-slate-700/80 rounded-2xl px-4 py-3 text-sm text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/50',
            'placeholder': 'name@example.com'
        })
    )
    phone_number = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full bg-slate-800/80 border border-slate-700/80 rounded-2xl px-4 py-3 text-sm text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/50',
            'placeholder': '+996XXXXXXXXX'
        })
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'password']

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if password:
            validate_password(password)
        return password

    def clean_passport_number(self):
        passport = self.cleaned_data.get('passport_number', '').upper()
        if not re.match(r'^(ID|AN)\d{7}$', passport):
            raise forms.ValidationError("Invalid Kyrgyz passport format. Must be ID or AN followed by 7 digits.")
        if UserProfile.objects.filter(passport_number=passport).exists():
            raise forms.ValidationError("This passport number is already registered.")
        return passport

    def clean(self):
        cleaned_data = super().clean()
        method = cleaned_data.get('verification_method')
        email = cleaned_data.get('email')
        phone = cleaned_data.get('phone_number')

        if method == 'email' and not email:
            self.add_error('email', 'Email address is required when selecting Email Verification.')
        elif method == 'phone':
            if not phone:
                self.add_error('phone_number', 'Phone number is required when selecting Phone Verification.')
            elif not re.match(r'^\+996\d{9}$', phone):
                self.add_error('phone_number', 'Invalid Kyrgyz phone format. Use +996 followed by 9 digits.')

        return cleaned_data


# ==========================================
# 👤 USER ACCOUNT & PROFILE SETTINGS FORM
# ==========================================

class UserSettingsForm(forms.ModelForm):
    phone_number = forms.CharField(
        max_length=13,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full bg-slate-800/80 border border-slate-700/80 rounded-2xl px-4 py-3 text-sm text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all',
            'placeholder': '+996 555 123 456'
        })
    )

    passport_number = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full bg-slate-800/80 border border-slate-700/80 rounded-2xl px-4 py-3 text-sm text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all',
            'placeholder': 'Passport Number'
        })
    )

    profile_picture = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'text-sm text-slate-400 file:mr-4 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-xs file:font-bold file:bg-indigo-600 file:text-white hover:file:bg-indigo-500 cursor-pointer'
        })
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'w-full bg-slate-800/80 border border-slate-700/80 rounded-2xl px-4 py-3 text-sm text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all',
                'placeholder': 'Your username'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'w-full bg-slate-800/80 border border-slate-700/80 rounded-2xl px-4 py-3 text-sm text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all',
                'placeholder': 'First name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'w-full bg-slate-800/80 border border-slate-700/80 rounded-2xl px-4 py-3 text-sm text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all',
                'placeholder': 'Last name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full bg-slate-800/80 border border-slate-700/80 rounded-2xl px-4 py-3 text-sm text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all',
                'placeholder': 'name@example.com'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.profile_instance = kwargs.pop('profile_instance', None)
        super().__init__(*args, **kwargs)
        if self.profile_instance:
            self.fields['phone_number'].initial = self.profile_instance.phone_number
            self.fields['passport_number'].initial = self.profile_instance.passport_number

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit and self.profile_instance:
            self.profile_instance.phone_number = self.cleaned_data.get('phone_number')
            self.profile_instance.passport_number = self.cleaned_data.get('passport_number')

            uploaded_picture = self.cleaned_data.get('profile_picture')
            if uploaded_picture:
                self.profile_instance.profile_picture = uploaded_picture

            self.profile_instance.save()
        return user

    def clean_passport_number(self):
        passport = self.cleaned_data['passport_number'].upper()
        if not re.match(r'^(ID|AN)\d{7}$', passport):
            raise forms.ValidationError('Passport must start with ID or AN followed by 7 digits.')
        if UserProfile.objects.exclude(pk=self.profile_instance.pk).filter(passport_number=passport).exists():
            raise forms.ValidationError('This passport number is already registered.')
        return passport

    def clean_phone_number(self):
        phone = self.cleaned_data['phone_number'].strip()
        if phone and not re.match(r'^\+996\d{9}$', phone):
            raise forms.ValidationError('Phone number must be +996 followed by 9 digits.')
        return phone


# ==========================================
# 📦 PRODUCT CREATION & UPDATE FORM
# ==========================================

class ProductCreateForm(forms.ModelForm):
    slug = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full bg-slate-800/80 border border-slate-700/80 rounded-2xl px-4 py-3 text-sm text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all',
            'placeholder': 'Auto-generated if empty (e.g., iphone-15-pro-max)'
        })
    )

    ram_option = forms.ChoiceField(
        choices=[('', '-- Select RAM --'), ('8GB', '8GB RAM'), ('12GB', '12GB RAM'), ('16GB', '16GB RAM'), ('32GB', '32GB RAM')],
        required=False,
        widget=forms.Select(attrs={'class': 'w-full bg-slate-800/80 border border-slate-700/80 rounded-2xl px-4 py-3 text-sm text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all cursor-pointer'})
    )
    storage_option = forms.ChoiceField(
        choices=[('', '-- Select Storage --'), ('128GB', '128GB Storage'), ('256GB', '256GB Storage'), ('512GB', '512GB Storage'), ('1TB', '1TB Storage')],
        required=False,
        widget=forms.Select(attrs={'class': 'w-full bg-slate-800/80 border border-slate-700/80 rounded-2xl px-4 py-3 text-sm text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all cursor-pointer'})
    )
    screen_option = forms.ChoiceField(
        choices=[('', '-- Select Screen Size --'), ('6.1 inch OLED', '6.1 inch OLED'), ('6.7 inch OLED', '6.7 inch OLED'), ('14 inch Retina', '14 inch Retina'), ('16 inch Retina', '16 inch Retina')],
        required=False,
        widget=forms.Select(attrs={'class': 'w-full bg-slate-800/80 border border-slate-700/80 rounded-2xl px-4 py-3 text-sm text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all cursor-pointer'})
    )
    processor_option = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full bg-slate-800/80 border border-slate-700/80 rounded-2xl px-4 py-3 text-sm text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all',
            'placeholder': 'e.g., Apple A17 Pro, Snapdragon 8 Gen 3, Intel Core i7'
        })
    )
    description = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full bg-slate-800/80 border border-slate-700/80 rounded-2xl px-4 py-3 text-sm text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all',
            'placeholder': 'Describe the product, condition, and included accessories.',
            'rows': 4,
        })
    )

    class Meta:
        model = Product
        fields = ['category', 'brand', 'name', 'slug', 'price', 'description', 'image', 'ram_option', 'storage_option', 'screen_option', 'processor_option']
        widgets = {
            'category': forms.Select(attrs={'class': 'w-full bg-slate-800/80 border border-slate-700/80 rounded-2xl px-4 py-3 text-sm text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all cursor-pointer'}),
            'brand': forms.TextInput(attrs={'class': 'w-full bg-slate-800/80 border border-slate-700/80 rounded-2xl px-4 py-3 text-sm text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all', 'placeholder': 'e.g., Apple, Samsung, ASUS'}),
            'name': forms.TextInput(attrs={'class': 'w-full bg-slate-800/80 border border-slate-700/80 rounded-2xl px-4 py-3 text-sm text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all', 'placeholder': 'e.g., iPhone 15 Pro Max'}),
            'price': forms.NumberInput(attrs={'class': 'w-full bg-slate-800/80 border border-slate-700/80 rounded-2xl px-4 py-3 text-sm text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all', 'placeholder': '999.99'}),
            'image': forms.FileInput(attrs={'class': 'text-sm text-slate-400 file:mr-4 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-xs file:font-bold file:bg-indigo-600 file:text-white hover:file:bg-indigo-500 cursor-pointer'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.specifications:
            specs = self.instance.specifications
            self.fields['ram_option'].initial = specs.get('RAM', '')
            self.fields['storage_option'].initial = specs.get('Storage', '')
            self.fields['screen_option'].initial = specs.get('Screen', '')
            self.fields['processor_option'].initial = specs.get('Processor', '')

    def clean_slug(self):
        slug = self.cleaned_data.get('slug')
        name = self.cleaned_data.get('name')

        if not slug and name:
            slug = slugify(name)

        qs = Product.objects.filter(slug=slug)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            slug = f"{slug}-{Product.objects.count() + 1}"

        return slug

    def save(self, commit=True):
        product = super().save(commit=False)

        ram = self.cleaned_data.get('ram_option')
        storage = self.cleaned_data.get('storage_option')
        screen = self.cleaned_data.get('screen_option')
        processor = self.cleaned_data.get('processor_option')

        specs = {}
        if ram:
            specs['RAM'] = ram
        if storage:
            specs['Storage'] = storage
        if screen:
            specs['Screen'] = screen
        if processor:
            specs['Processor'] = processor

        product.specifications = specs

        if commit:
            product.save()
        return product
