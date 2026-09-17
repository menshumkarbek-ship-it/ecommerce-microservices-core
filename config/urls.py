from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
from django.contrib.sitemaps.views import sitemap
from shop.sitemaps import StaticViewSitemap

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
    # 🔒 Django admin, mounted at settings.ADMIN_URL rather than /admin/, so
    # the default path scanners probe simply 404s. Day-to-day product/
    # category/contact edits go through the in-app management panel instead;
    # this route stays for user/group management and superuser use.
    #
    # There used to be a decoy on /admin/ pointing at the management panel.
    # It defeated itself: that view is @login_required, so probing /admin/
    # redirected straight to ADMIN_URL's login page and handed over the very
    # path it was hiding. Note this is obscurity, not a control — every
    # protected view still redirects to the real login URL. Treat the admin
    # as publicly known and put real controls (strong passwords, 2FA) on it.
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