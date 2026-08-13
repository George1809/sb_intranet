import re

from django.conf import settings
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.urls import reverse


# Middleware = mecanism nativ Django, cod care ruleaza pe fiecare cerere,
# inainte sa ajunga la view-ul propriu-zis - util cand vrei o regula
# valabila peste tot, nu doar intr-un loc. Cele 3 clase de mai jos sunt
# inregistrate in sb_intranet/settings/base.py (lista MIDDLEWARE); fiecare
# rezolva ceva ce Wagtail nu acopera din start (vezi docstring-ul fiecareia).
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


class PersonalSpaceHistoryRestrictionMiddleware:
    """
    Spre deosebire de edit/delete/unpublish/copy/move (blocate in
    home/wagtail_hooks.py, via hook-urile before_*_page), Wagtail nu ruleaza
    niciun hook pentru istoric, workflow history sau revizii - view-urile
    alea verifica doar can_edit()/can_publish() generic, permisiune acordata
    pe tot subarborele "Spatii personale". Fara asta, orice Angajat care
    afla/ghiceste ID-ul paginii unui coleg ar putea vedea "View this
    revision" (randeaza continutul integral al acelei versiuni) sau
    diff-ul din "Compare revisions" pentru spatiul personal al altcuiva.
    """

    RESTRICTED_PATH = re.compile(
        r"^/admin/pages/(?P<page_id>\d+)/(history|workflow_history|revisions)(/|$)"
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        match = self.RESTRICTED_PATH.match(request.path)
        if match and not request.user.is_superuser and self._is_other_users_personal_space(
            match.group("page_id"), request.user
        ):
            return HttpResponseForbidden(
                "Nu ai acces la spatiul personal al altui utilizator."
            )
        return self.get_response(request)

    @staticmethod
    def _is_other_users_personal_space(page_id, user):
        from home.models import PersonalSpacePage

        return (
            PersonalSpacePage.objects.filter(id=page_id)
            .exclude(owner_user_id=user.id)
            .exists()
        )
