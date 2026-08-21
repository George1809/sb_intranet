import re

from django.conf import settings
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.urls import reverse


# Cele 3 clase de mai jos sunt inregistrate in sb_intranet/settings/base.py (lista MIDDLEWARE). 
# Fiecare rezolva ceva ce Wagtail nu acopera din start.
class IntranetLoginRequiredMiddleware:
    """
    Un vizitator neautentificat nu trebuie sa poata ajunge la nimic din intranet, 
    nici pagini, nici cautare, nici documente sau media incarcata.
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
    Cautarea globala de pagini din admin foloseste intern explorable_instances() din Wagtail, care nu stie de izolarea spatiilor personale 
    (hook-urile din home/wagtail_hooks.py), un user ar putea gasi titlul spatiului personal al unui coleg acolo. 
    Se blocheaza direct la nivel de URL pentru "Moderators" si "Users", nefiind disponibil un hook dedicat pentru asta.
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
    Spre deosebire de edit/delete/unpublish/copy/move, blocate deja in home/wagtail_hooks.py prin hook-urile before_*_page, 
    Wagtail nu ruleaza niciun hook pentru istoric, workflow history sau revizii, verificandu-se doar can_edit()/can_publish().
    Fara verificarea asta, orice user care ghiceste ID-ul paginii unui coleg ar putea vedea jurnalul de modificari (istoric/workflow),
    dar ar putea vedea si continutul integral al unei versiuni vechi, prin "View this revision".
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
