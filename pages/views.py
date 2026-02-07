from django.shortcuts import render
from django.contrib.auth.decorators import login_required

def public_dashboard(request):
    """Landing page / public dashboard"""
    return render(request, 'dashboard/public_dashboard.html')


@login_required
def dashboard(request):
    """Role-based dashboard after login"""
    user = request.user
    if user.is_staff:
        template = 'dashboard/admin_dashboard.html'
    elif hasattr(user, 'user_type'):
        if user.user_type == 'executive':
            template = 'dashboard/executive_dashboard.html'
        elif user.user_type == 'member':
            template = 'dashboard/member_dashboard.html'
        else:
            template = 'dashboard/public_dashboard.html'
    else:
        template = 'dashboard/public_dashboard.html'
    return render(request, template)
