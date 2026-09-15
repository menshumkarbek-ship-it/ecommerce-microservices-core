from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
from django.contrib.sitemaps.views import sitemap
from shop.sitemaps import StaticViewSitemap
from shop import views as shop_views

sitemaps = {
    'static': StaticViewSitemap,
}

def robots_txt(request):
    lines = [
        "User-agent: *",
        f"Disallow: /{settings.ADMIN_URL}",
        "Disallow: /admin/",
        "Allow: /",
        f"Sitemap: https://{settings.SITE_DOMAIN}/sitemap.xml",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")

urlpatterns = [
    # 🕵️ Decoy: the old, commonly-guessed /admin/ path no longer serves
    # Django's built-in admin — it now opens our own in-app management panel
    # directly (same view as shop:create_product). Anyone/anything probing
    # /admin/ for a recognizable Django login screen won't find one here;
    # the real Django admin lives at settings.ADMIN_URL instead (below).
    path('admin/', shop_views.create_product, name='admin_decoy'),

    # 🔒 Real Django admin, mounted at settings.ADMIN_URL (not /admin/) — see
    # config/settings.py. Day-to-day product/category/contact edits go
    # through the in-app management panel instead; this route stays for
    # user/group management and superuser use.
    path(settings.ADMIN_URL, admin.site.urls),
    path('robots.txt', robots_txt),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),

    # 🌐 Built-in Django route to handle language-switching form submissions
    path('i18n/', include('django.conf.urls.i18n')),

    # 🏪 Shop Application URLs
    path('', include('shop.urls', namespace='shop')),
]

# Serve media files locally during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)