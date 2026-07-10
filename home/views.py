from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from home.models import PersonalSpacePage


@login_required
def personal_space(request):
    page = PersonalSpacePage.get_or_create_for_user(request.user)
    return redirect(page.url)
