def is_admin(request):
    """Expose whether the current visitor is staff/manager, for nav rendering."""
    if not request.user.is_authenticated:
        return {'is_admin_user': False}
    is_admin_user = request.user.is_staff or request.user.is_superuser or request.user.groups.filter(
        name__in=['Admins', 'Managers']
    ).exists()
    return {'is_admin_user': is_admin_user}


def contact_settings(request):
    """Expose the store's admin-managed contact channels to every template."""
    from .models import ContactSettings
    return {'contact_settings': ContactSettings.get_solo()}


def site_identity(request):
    """Expose the admin-editable store/market name to every template (navbar,
    browser tab titles, footer).

    Named `store_name` (not `site_name`) deliberately: Django's own
    django.contrib.auth.views.LoginView — used by the admin login page —
    unconditionally injects its own `site_name` context variable sourced
    from django.contrib.sites (defaults to "example.com"), which would
    silently shadow ours on that page if we reused the same key.
    """
    from .models import AboutPageContent
    return {'store_name': AboutPageContent.get_solo().translated_site_name}
