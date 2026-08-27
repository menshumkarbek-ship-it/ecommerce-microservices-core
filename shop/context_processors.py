from .models import UserProfile


def user_profile(request):
    """Expose a profile safely: administrator accounts may not have one."""
    if not request.user.is_authenticated:
        return {'user_profile': None, 'is_admin_user': False}
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        profile = None
    is_admin_user = request.user.is_staff or request.user.is_superuser or request.user.groups.filter(
        name__in=['Admins', 'Managers']
    ).exists()
    return {'user_profile': profile, 'is_admin_user': is_admin_user}
