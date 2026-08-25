from .models import UserProfile


def user_profile(request):
    """Expose a profile safely: administrator accounts may not have one."""
    if not request.user.is_authenticated:
        return {'user_profile': None}
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        profile = None
    return {'user_profile': profile}
