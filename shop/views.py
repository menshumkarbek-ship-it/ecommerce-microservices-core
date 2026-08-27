import os
import secrets
import requests
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm, SetPasswordForm
from django.views.decorators.http import require_POST
from django.core.cache import cache
from django.core.mail import send_mail
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.db import transaction
from django.utils import timezone
from datetime import timedelta

from .models import Product, Category, Order, OrderItem, UserProfile
from .forms import UserSettingsForm, ProductCreateForm, CustomerRegistrationForm
from .cart import Cart

FLASK_PDF_SERVICE_URL = os.getenv('FLASK_PDF_SERVICE_URL', 'http://127.0.0.1:8002')


# ==========================================
# 🏠 HOME PAGE CONTROLLER
# ==========================================

def home_page(request):
    categories = cache.get('global_store_categories')
    if not categories:
        categories = Category.objects.all()
        cache.set('global_store_categories', categories, 60 * 15)

    hero_product = Product.objects.filter(
        is_sold=False
    ).filter(
        Q(category__slug__icontains='phone') |
        Q(category__name__icontains='phone') |
        Q(category__name__icontains='mobile')
    ).select_related('category').order_by('-created_at', '-id').first()

    laptop_promo = Product.objects.filter(
        is_sold=False,
        category__name__icontains='laptop'
    ).select_related('category').order_by('-id').first()

    tablet_promo = Product.objects.filter(
        is_sold=False,
        category__name__icontains='tablet'
    ).select_related('category').order_by('-id').first()

    phones_top_picks = Product.objects.filter(
        is_sold=False
    ).filter(
        Q(category__slug__icontains='phone') | Q(category__name__icontains='phone') | Q(category__name__icontains='mobile')
    ).select_related('category').order_by('-id')[:5]

    laptops_top_picks = Product.objects.filter(
        is_sold=False
    ).filter(
        Q(category__slug__icontains='laptop') | Q(category__name__icontains='laptop')
    ).select_related('category').order_by('-id')[:5]

    tablets_top_picks = Product.objects.filter(
        is_sold=False
    ).filter(
        Q(category__slug__icontains='tablet') | Q(category__name__icontains='tablet') | Q(category__name__icontains='ipad') | Q(category__name__icontains='pad')
    ).select_related('category').order_by('-id')[:5]

    context = {
        'categories': categories,
        'hero_product': hero_product,
        'laptop_promo': laptop_promo,
        'tablet_promo': tablet_promo,
        'phones_top_picks': phones_top_picks,
        'laptops_top_picks': laptops_top_picks,
        'tablets_top_picks': tablets_top_picks,
    }
    return render(request, 'shop/home.html', context)


# ==========================================
# 🏪 CATALOG CONTROLLERS
# ==========================================

def product_list(request, category_slug=None):
    category = None
    categories = cache.get('global_store_categories')
    if not categories:
        categories = Category.objects.all()
        cache.set('global_store_categories', categories, 60 * 15)

    products_list = Product.objects.filter(is_sold=False).select_related('category').order_by('-id')
    type_filter = request.GET.get('type') or category_slug

    if type_filter == 'phones':
        type_filter = 'phone'
    elif type_filter == 'laptops':
        type_filter = 'laptop'
    elif type_filter == 'tablets':
        type_filter = 'tablet'

    brand_filter = request.GET.get('brand')
    search_query = request.GET.get('search')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')

    has_active_filters = bool(type_filter or brand_filter or search_query or min_price or max_price)

    if type_filter:
        products_list = products_list.filter(
            Q(category__slug__iexact=type_filter) | Q(category__name__icontains=type_filter)
        )

    if brand_filter:
        products_list = products_list.filter(brand__iexact=brand_filter)

    if search_query:
        products_list = products_list.filter(
            Q(name__icontains=search_query) |
            Q(brand__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    if min_price:
        try:
            products_list = products_list.filter(price__gte=float(min_price))
        except ValueError:
            pass

    if max_price:
        try:
            products_list = products_list.filter(price__lte=float(max_price))
        except ValueError:
            pass

    available_brands = Product.objects.filter(is_sold=False).values_list('brand', flat=True).distinct()

    paginator = Paginator(products_list.distinct(), 15)
    page_number = request.GET.get('page')

    try:
        products = paginator.page(page_number)
    except (PageNotAnInteger, EmptyPage):
        products = paginator.page(1)

    grouped_sections = {}
    if not has_active_filters:
        grouped_sections = {
            'phones': Product.objects.filter(is_sold=False, category__name__icontains='phone').select_related('category').order_by('-id')[:5],
            'laptops': Product.objects.filter(is_sold=False, category__name__icontains='laptop').select_related('category').order_by('-id')[:5],
            'tablets': Product.objects.filter(is_sold=False, category__name__icontains='tablet').select_related('category').order_by('-id')[:5],
        }

    context = {
        'category': category,
        'categories': categories,
        'products': products,
        'available_brands': available_brands,
        'selected_type': type_filter or '',
        'selected_brand': brand_filter or '',
        'min_price': min_price or '',
        'max_price': max_price or '',
        'search_query': search_query or '',
        'has_active_filters': has_active_filters,
        'grouped_sections': grouped_sections,
    }
    return render(request, 'shop/product/list.html', context)


def product_detail(request, product_slug):
    product = get_object_or_404(Product.objects.select_related('category'), slug=product_slug, is_sold=False)
    return render(request, 'shop/product/detail.html', {'product': product})


def product_specs(request, product_slug):
    product = get_object_or_404(Product.objects.select_related('category'), slug=product_slug, is_sold=False)
    return render(request, 'shop/product/specs.html', {'product': product})


# ==========================================
# 🔐 AUTHENTICATION & CUSTOMER REGISTRATION
# ==========================================

def register_customer(request):
    if request.method == 'POST':
        form = CustomerRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.email = form.cleaned_data.get('email', '')
            user.save()

            otp_code = f'{secrets.randbelow(900000) + 100000:06d}'

            profile = UserProfile.objects.create(
                user=user,
                verification_method='email',
                email_otp=otp_code,
            )

            send_mail(
                subject='TechVault Verification Code',
                message=f'Your activation code is: {otp_code}',
                from_email=None,
                recipient_list=[user.email],
                fail_silently=False,
            )

            login(request, user)
            messages.info(request, "Please verify the code sent to your email address.")
            return redirect('shop:verify_otp')
        else:
            messages.error(request, "Please correct the highlighted errors below.")
    else:
        form = CustomerRegistrationForm()

    return render(request, 'shop/auth/register.html', {'form': form})


@login_required
def verify_otp(request):
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        messages.error(request, 'Your account profile is incomplete. Please contact support.')
        return redirect('shop:home')

    if profile.kyc_status == 'verified':
        return redirect('shop:home')

    if request.method == 'POST':
        entered_code = request.POST.get('otp_code', '').strip()

        if entered_code == profile.email_otp:
            profile.is_email_verified = True
            profile.kyc_status = 'verified'
            profile.email_otp = None
            profile.save()
            messages.success(request, "Email verified successfully! Account fully activated.")
            return redirect('shop:home')
        else:
            messages.error(request, "Invalid verification code. Please check and try again.")

    return render(request, 'shop/auth/verify_otp.html', {'profile': profile})


def login_customer(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name}!")
            return redirect('shop:home')
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()

    return render(request, 'shop/auth/login.html', {'form': form})


def logout_customer(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('shop:home')


# ==========================================
# 🛒 SHOPPING CART SYSTEM MANAGEMENT
# ==========================================

@require_POST
def cart_add(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id, is_sold=False)

    added = cart.add(product=product, quantity=1)
    if added:
        messages.success(request, f"{product.name} added to cart!")
    else:
        messages.warning(request, f"{product.name} is already in your cart!")

    return redirect('shop:cart_detail')


@require_POST
def cart_remove(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
    return redirect('shop:cart_detail')


def cart_detail(request):
    cart = Cart(request)
    return render(request, 'shop/cart/detail.html', {'cart': cart})


# ==========================================
# 💎 PROFILE SETTINGS
# ==========================================

@login_required
def account_settings(request):
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        messages.error(request, 'Your account profile is incomplete. Please contact support.')
        return redirect('shop:home')

    if request.method == 'POST':
        form = UserSettingsForm(request.POST, request.FILES, instance=request.user, profile_instance=profile)
        if form.is_valid():
            updated_user = form.save()
            update_session_auth_hash(request, updated_user)
            messages.success(request, "Your account settings have been updated successfully.")
            return redirect('shop:account_settings')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = UserSettingsForm(instance=request.user, profile_instance=profile)

    return render(request, 'shop/auth/settings.html', {'form': form})


@login_required
def change_password(request):
    if request.method == 'POST':
        profile = request.user.profile
        if request.POST.get('action') == 'send_code':
            profile.password_change_otp = f'{secrets.randbelow(900000) + 100000:06d}'
            profile.password_change_otp_created_at = timezone.now()
            profile.save(update_fields=['password_change_otp', 'password_change_otp_created_at'])
            send_mail(
                subject='TechVault Password Change Code',
                message=f'Your password change code is: {profile.password_change_otp}',
                from_email=None,
                recipient_list=[request.user.email],
                fail_silently=False,
            )
            messages.success(request, "A password change code was sent to your email.")
        else:
            form = SetPasswordForm(request.user, request.POST)
            code = request.POST.get('otp_code', '').strip()
            code_created_at = profile.password_change_otp_created_at
            code_is_valid = (
                code == profile.password_change_otp and
                code_created_at and
                timezone.now() - code_created_at <= timedelta(minutes=10)
            )
            if form.is_valid() and code_is_valid:
                user = form.save()
                profile.password_change_otp = None
                profile.password_change_otp_created_at = None
                profile.save(update_fields=['password_change_otp', 'password_change_otp_created_at'])
                update_session_auth_hash(request, user)
                messages.success(request, "Your password was successfully updated!")
                return redirect('shop:account_settings')
            if not code_is_valid:
                form.add_error(None, 'Invalid or expired email verification code.')
            messages.error(request, "Please correct the errors down below.")
    else:
        form = SetPasswordForm(request.user)

    if 'form' not in locals():
        form = SetPasswordForm(request.user)

    for field in form.fields.values():
        field.widget.attrs.update({
            'class': 'w-full bg-slate-800/80 border border-slate-700/80 rounded-2xl px-4 py-3 text-sm text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all',
        })
    return render(request, 'shop/auth/change_password.html', {'form': form})


@login_required
def payment_method_settings(request):
    return render(request, 'shop/auth/payment_settings.html')


# ==========================================
# 🧾 CHECKOUT & ORDERS
# ==========================================

@login_required
@require_POST
def checkout_order(request):
    cart = Cart(request)
    cart_items = list(cart)
    if not cart_items:
        messages.error(request, "Your cart is empty.")
        return redirect('shop:product_list')

    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        messages.error(request, 'Complete your account profile before checkout.')
        return redirect('shop:account_settings')
    if profile.kyc_status != 'verified':
        messages.error(request, 'Verify your account before checkout.')
        return redirect('shop:verify_otp')

    product_ids = [item['product'].id for item in cart_items]
    with transaction.atomic():
        products = list(Product.objects.select_for_update().filter(id__in=product_ids, is_sold=False))
        if len(products) != len(product_ids):
            messages.error(request, 'One or more cart items are no longer available.')
            return redirect('shop:cart_detail')

        products_by_id = {product.id: product for product in products}
        total_price = sum((products_by_id[item['product'].id].price for item in cart_items), start=0)
        order = Order.objects.create(user=request.user, total_price=total_price)
        OrderItem.objects.bulk_create([
            OrderItem(order=order, product=products_by_id[item['product'].id], price=products_by_id[item['product'].id].price, quantity=1)
            for item in cart_items
        ])
        Product.objects.filter(id__in=product_ids).update(is_sold=True)
        cart.clear()

    flask_endpoint = f"{FLASK_PDF_SERVICE_URL}/api/v1/generate-invoice"
    payload = {
        "order_id": str(order.id),
        "customer_name": f"{request.user.first_name} {request.user.last_name}" if request.user.first_name else request.user.username,
        "product_name": ', '.join(f"{product.brand} {product.name}" for product in products),
        "price": str(total_price)
    }

    try:
        response = requests.post(flask_endpoint, json=payload, timeout=5)
        if response.status_code == 201:
            messages.success(request, f"Success! Order #{order.id} processed. Your background PDF receipt is ready!")
        else:
            messages.warning(request, f"Order #{order.id} processed, but background invoice worker returned status code {response.status_code}.")
    except requests.exceptions.RequestException:
        messages.warning(request, f"Order #{order.id} logged securely, but the PDF invoice microservice is currently offline.")

    return redirect('shop:product_list')


@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'shop/auth/order_history.html', {'orders': orders})


# ==========================================
# 📄 AUXILIARY PAGES
# ==========================================

def about_us(request):
    return render(request, 'shop/pages/about.html')


def contact_us(request):
    return render(request, 'shop/pages/contact.html')


def is_admin_or_manager(user):
    return user.is_authenticated and (
            user.is_staff or
            user.is_superuser or
            user.groups.filter(name__in=['Admins', 'Managers']).exists()
    )


@login_required
@user_passes_test(is_admin_or_manager, login_url='shop:product_list', redirect_field_name=None)
def create_product(request, product_id=None):
    product_instance = None
    if product_id:
        product_instance = get_object_or_404(Product, id=product_id)

    if request.method == 'POST':
        form = ProductCreateForm(request.POST, request.FILES, instance=product_instance)
        if form.is_valid():
            form.save()
            action_text = "updated" if product_instance else "cataloged"
            messages.success(request, f"Product successfully {action_text}!")
            return redirect('shop:product_list')
        else:
            messages.error(request, "Please correct the entry errors down below.")
    else:
        form = ProductCreateForm(instance=product_instance)

    all_products = Product.objects.filter(is_sold=False).select_related('category').order_by('-id')

    context = {
        'form': form,
        'product_instance': product_instance,
        'all_products': all_products,
    }
    return render(request, 'shop/product/create.html', context)


@login_required
@user_passes_test(is_admin_or_manager, login_url='shop:product_list', redirect_field_name=None)
def admin_purchase_history(request):
    all_purchases = OrderItem.objects.select_related('order__user', 'product').order_by('-order__created_at')

    paginator = Paginator(all_purchases, 25)
    page_number = request.GET.get('page')
    try:
        purchases = paginator.page(page_number)
    except (PageNotAnInteger, EmptyPage):
        purchases = paginator.page(1)

    context = {
        'purchases': purchases,
    }
    return render(request, 'shop/admin/purchase_history.html', context)
