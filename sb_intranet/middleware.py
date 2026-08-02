from django.conf import settings
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.urls import reverse


class IntranetLoginRequiredMiddleware:
    """
    Keep the public surface small: visitors must authenticate before they can
    reach intranet pages, search, documents, or uploaded media.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated or self._is_exempt(request.path):
            return self.get_response(request)

        login_url = reverse(settings.LOGIN_URL)
        return redirect(f"{login_url}?next={request.get_full_path()}")

    def _is_exempt(self, path):
        exempt_prefixes = (
            reverse(settings.LOGIN_URL),
            "/accounts/",
            "/admin/",
            "/django-admin/",
            settings.STATIC_URL,
        )
        return path.startswith(exempt_prefixes) or path == "/favicon.ico"


class AdminPageSearchRestrictionMiddleware:
    """
    Cautarea globala de pagini din admin (/admin/pages/search/) foloseste
    intern explorable_instances() din Wagtail, care nu stie de izolarea
    spatiilor personale (hook-urile din home/wagtail_hooks.py) - un Angajat
    ar putea gasi titlul spatiului personal al unui coleg acolo. Wagtail nu
    ofera niciun hook/setare pentru a restrictiona vederea asta per grup,
    deci o blocam direct la nivel de URL, doar pentru non-superuseri.
    """

    RESTRICTED_PREFIX = "/admin/pages/search/"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith(self.RESTRICTED_PREFIX) and not request.user.is_superuser:
            return HttpResponseForbidden(
                "Cautarea globala din admin nu este disponibila pentru contul tau."
            )
        return self.get_response(request)
