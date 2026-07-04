from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def personal_space(request):
    return render(request, "home/personal_space.html")
