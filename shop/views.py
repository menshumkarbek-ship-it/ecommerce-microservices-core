from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.cache import cache
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from .models import Product, Category, ProductImage, ContactSettings, AboutPageContent
from .forms import ProductCreateForm, CategoryCreateForm, ContactSettingsForm, AboutPageContentForm

# Rotating accent colors for the per-category homepage rows, so each
# category's "Newest In" slideshow gets a distinct look automatically.
CATEGORY_ACCENT_PALETTE = ['indigo', 'cyan', 'emerald', 'purple', 'amber', 'rose', 'sky', 'teal']


# ==========================================
# 🏠 HOME PAGE CONTROLLER
# ==========================================

def home_page(request):
    categories = cache.get('global_store_categories')
    if not categories:
        categories = Category.objects.all()
        cache.set('global_store_categories', categories, 60 * 15)

    # 🆕 Hero announcement slides: an admin marks a category as "featured in
    # hero" (from the Categories management page) and its newest in-stock
    # product becomes an auto-rotating slide here. No fixed slide count.
    hero_slides = []
    featured_categories = Category.objects.filter(is_featured_in_hero=True).order_by('name')
    for index, category in enumerate(featured_categories):
        product = Product.objects.filter(
            is_sold=False, category=category
        ).select_related('category').order_by('-created_at', '-id').first()
        if product:
            hero_slides.append({
                'category': category,
                'product': product,
                'accent': CATEGORY_ACCENT_PALETTE[index % len(CATEGORY_ACCENT_PALETTE)],
            })

    # 🆕 Build one "Newest In <Category>" slideshow row per category that has
    # stock AND that an admin has left switched on (Category.show_newest_row,
    # toggled from the Categories management page). New categories default to
    # shown, so this stays fully data-driven unless an admin opts a category out.
    category_sections = []
    for index, category in enumerate(categories):
        if not category.slug or not category.show_newest_row:
            continue
        products = Product.objects.filter(
            is_sold=False, category=category
        ).select_related('category').order_by('-created_at', '-id')[:10]
        if products:
            category_sections.append({
                'category': category,
                'products': products,
                'accent': CATEGORY_ACCENT_PALETTE[index % len(CATEGORY_ACCENT_PALETTE)],
            })

    context = {
        'categories': categories,
        'hero_slides': hero_slides,
        'category_sections': category_sections,
    }
    return render(request, 'shop/home.html', context)


# ==========================================
# 🏪 CATALOG CONTROLLER
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

    # 🔓 Always paginate the full matching catalog (filtered or not) so visitors
    # can scroll through every product instead of being capped to a handful
    # of "top picks" per category. The filter panel above still narrows results.
    paginator = Paginator(products_list.distinct(), 24)
    page_number = request.GET.get('page')

    try:
        products = paginator.page(page_number)
    except (PageNotAnInteger, EmptyPage):
        products = paginator.page(1)

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
    }
    return render(request, 'shop/product/list.html', context)


def product_detail(request, product_slug):
    product = get_object_or_404(
        Product.objects.select_related('category').prefetch_related('gallery_images'),
        slug=product_slug, is_sold=False
    )
    return render(request, 'shop/product/detail.html', {'product': product})


def product_specs(request, product_slug):
    product = get_object_or_404(Product.objects.select_related('category'), slug=product_slug, is_sold=False)
    return render(request, 'shop/product/specs.html', {'product': product})


# ==========================================
# 📄 AUXILIARY PAGES
# ==========================================

def about_us(request):
    return render(request, 'shop/pages/about.html', {'about': AboutPageContent.get_solo()})


def contact_us(request):
    product_slug = request.GET.get('product')
    inquiry_product = None
    if product_slug:
        inquiry_product = Product.objects.filter(slug=product_slug, is_sold=False).select_related('category').first()

    if inquiry_product:
        product_url = request.build_absolute_uri(
            reverse('shop:product_detail', kwargs={'product_slug': inquiry_product.slug})
        )
        inquiry_message = _("Hi! I'm interested in the %(name)s (%(url)s). Is it still available?") % {
            'name': inquiry_product.translated_name, 'url': product_url,
        }
    else:
        product_url = None
        site_name = AboutPageContent.get_solo().translated_site_name
        inquiry_message = _("Hi! I have a question about a product at %(site_name)s.") % {'site_name': site_name}

    context = {
        'inquiry_product': inquiry_product,
        'inquiry_product_url': product_url,
        'inquiry_message': inquiry_message,
    }
    return render(request, 'shop/pages/contact.html', context)


# ==========================================
# 🛠️ CATALOG MANAGEMENT (staff/manager only, via Django admin login)
# ==========================================

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
            product = form.save()

            # Extra gallery photos: a plain <input type="file" name="extra_images"
            # multiple> isn't a ModelForm field (Django forms don't support
            # multi-file fields out of the box), so they're picked up straight
            # from request.FILES and saved as separate ProductImage rows.
            extra_images = request.FILES.getlist('extra_images')
            if extra_images:
                next_order = product.gallery_images.count()
                for offset, image_file in enumerate(extra_images):
                    ProductImage.objects.create(product=product, image=image_file, order=next_order + offset)

            if product_instance:
                messages.success(request, _("Product successfully updated!"))
            else:
                messages.success(request, _("Product successfully cataloged!"))
            return redirect('shop:product_list')
        else:
            messages.error(request, _("Please correct the entry errors down below."))
    else:
        form = ProductCreateForm(instance=product_instance)

    # Grouped by category (then by its per-category #ID) so a seller can find
    # a specific listing quickly instead of hunting through one long list.
    all_products = Product.objects.filter(is_sold=False).select_related('category').order_by(
        'category__name', 'category_number'
    )

    # Search by catalog #ID (to pull up the exact listing to delete once it's
    # sold), or by name/brand as a fallback for a more casual lookup.
    search_query = request.GET.get('q', '').strip()
    if search_query:
        search_filter = Q(name__icontains=search_query) | Q(brand__icontains=search_query)
        if search_query.lstrip('#').isdigit():
            search_filter |= Q(category_number=int(search_query.lstrip('#')))
        all_products = all_products.filter(search_filter)

    known_brands = Product.objects.exclude(brand='').values_list('brand', flat=True).distinct().order_by('brand')
    gallery_images = product_instance.gallery_images.all() if product_instance else []

    context = {
        'form': form,
        'product_instance': product_instance,
        'all_products': all_products,
        'known_brands': known_brands,
        'gallery_images': gallery_images,
        'search_query': search_query,
    }
    return render(request, 'shop/product/create.html', context)


@login_required
@user_passes_test(is_admin_or_manager, login_url='shop:product_list', redirect_field_name=None)
@require_POST
def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product_name = product.name
    product.delete()
    messages.success(request, _('"%(name)s" was removed from the catalog.') % {'name': product_name})
    return redirect('shop:create_product')


@login_required
@user_passes_test(is_admin_or_manager, login_url='shop:product_list', redirect_field_name=None)
@require_POST
def delete_product_image(request, image_id):
    gallery_image = get_object_or_404(ProductImage, id=image_id)
    product_id = gallery_image.product_id
    gallery_image.image.delete(save=False)
    gallery_image.delete()
    messages.success(request, _("Photo removed from the gallery."))
    return redirect('shop:update_product', product_id=product_id)


@login_required
@user_passes_test(is_admin_or_manager, login_url='shop:product_list', redirect_field_name=None)
def create_category(request):
    if request.method == 'POST':
        form = CategoryCreateForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _("Category created! It now appears in the catalog filter and will get its own homepage row once it has products."))
            return redirect('shop:create_category')
        else:
            messages.error(request, _("Please correct the entry errors down below."))
    else:
        form = CategoryCreateForm()

    all_categories = Category.objects.all().order_by('name')

    context = {
        'form': form,
        'all_categories': all_categories,
    }
    return render(request, 'shop/product/category_create.html', context)


@login_required
@user_passes_test(is_admin_or_manager, login_url='shop:product_list', redirect_field_name=None)
@require_POST
def toggle_category_hero(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    category.is_featured_in_hero = not category.is_featured_in_hero
    category.save(update_fields=['is_featured_in_hero'])

    if category.is_featured_in_hero:
        messages.success(request, _('"%(name)s" added to the homepage announcement slideshow.') % {'name': category.name})
    else:
        messages.success(request, _('"%(name)s" removed from the homepage announcement slideshow.') % {'name': category.name})

    return redirect('shop:create_category')


@login_required
@user_passes_test(is_admin_or_manager, login_url='shop:product_list', redirect_field_name=None)
@require_POST
def toggle_category_newest(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    category.show_newest_row = not category.show_newest_row
    category.save(update_fields=['show_newest_row'])

    if category.show_newest_row:
        messages.success(request, _('"%(name)s" now has a "Newest In" row on the homepage.') % {'name': category.name})
    else:
        messages.success(request, _('"%(name)s"\'s "Newest In" row is hidden from the homepage.') % {'name': category.name})

    return redirect('shop:create_category')


@login_required
@user_passes_test(is_admin_or_manager, login_url='shop:product_list', redirect_field_name=None)
def manage_contacts(request):
    """
    Lets staff/managers edit the store's WhatsApp, Telegram, Instagram,
    phone, and email contact channels from inside the app itself, so this
    everyday task no longer needs the separate Django admin panel.
    """
    settings_obj = ContactSettings.get_solo()

    if request.method == 'POST':
        form = ContactSettingsForm(request.POST, instance=settings_obj)
        if form.is_valid():
            form.save()
            messages.success(request, _("Contact channels updated!"))
            return redirect('shop:manage_contacts')
        else:
            messages.error(request, _("Please correct the entry errors below."))
    else:
        form = ContactSettingsForm(instance=settings_obj)

    return render(request, 'shop/product/contact_settings.html', {'form': form})


@login_required
@user_passes_test(is_admin_or_manager, login_url='shop:product_list', redirect_field_name=None)
def manage_about(request):
    """
    Lets staff/managers write the About Us page copy — the shop's story,
    market, visit-us details, and address — from inside the app itself.
    """
    content_obj = AboutPageContent.get_solo()

    if request.method == 'POST':
        form = AboutPageContentForm(request.POST, request.FILES, instance=content_obj)
        if form.is_valid():
            form.save()
            messages.success(request, _("About page updated!"))
            return redirect('shop:manage_about')
        else:
            messages.error(request, _("Please correct the entry errors below."))
    else:
        form = AboutPageContentForm(instance=content_obj)

    # One row per language, each holding that language's variant of every
    # translatable field in a fixed order the template loops over — lets the
    # template render one shared block per language instead of tripling the
    # markup for English/Russian/Kyrgyz by hand.
    about_lang_fields = [
        (
            lang,
            form[f'site_name{suffix}'], form[f'badge_text{suffix}'], form[f'heading{suffix}'],
            form[f'intro_text{suffix}'], form[f'visit_heading{suffix}'], form[f'visit_text{suffix}'],
            form[f'store_address_line1{suffix}'], form[f'store_address_line2{suffix}'],
            form[f'cta_heading{suffix}'], form[f'cta_text{suffix}'],
        )
        for lang, suffix in [('en', ''), ('ru', '_ru'), ('ky', '_ky')]
    ]

    return render(request, 'shop/product/about_settings.html', {'form': form, 'about_lang_fields': about_lang_fields})
