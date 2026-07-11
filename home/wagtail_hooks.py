from django.db.models import Q
from django.http import HttpResponseForbidden

from wagtail import hooks
from wagtail.models import TaskState, WorkflowState
from wagtail.signals import (
    task_submitted,
    workflow_approved,
    workflow_rejected,
    workflow_submitted,
)

from home.models import PersonalSpaceIndexPage, PersonalSpacePage

# Oprite temporar notificarile automate prin email la submit/aprobare/
# respingere in workflow, cat timp testam manual fluxul de moderare.
# De reactivat cand implementam corect linkurile din emailuri
# (WAGTAILADMIN_BASE_URL) si continutul notificarilor.
# Trebuie sa ruleze dupa ce wagtail.admin isi conecteaza propriile semnale
# (se intampla la ready()); wagtail_hooks.py e importat mai tarziu, la prima
# cautare de hook-uri, deci ordinea e garantata corecta.
task_submitted.disconnect(
    sender=TaskState,
    dispatch_uid="group_approval_task_submitted_email_notification",
)
workflow_submitted.disconnect(
    sender=WorkflowState,
    dispatch_uid="workflow_state_submitted_email_notification",
)
workflow_rejected.disconnect(
    sender=WorkflowState,
    dispatch_uid="workflow_state_rejected_email_notification",
)
workflow_approved.disconnect(
    sender=WorkflowState,
    dispatch_uid="workflow_state_approved_email_notification",
)


@hooks.register("construct_reports_menu")
def hide_reports_for_limited_users(request, menu_items):
    """
    Rapoartele (Workflows, Site history, Aging pages etc.) sunt utile doar
    pentru administratorii cu acces total - userii cu acces limitat nu au
    nevoie de ele, deci le ascundem complet (meniul Reports dispare singur
    daca ramane fara elemente).
    """
    if not request.user.is_superuser:
        menu_items.clear()


@hooks.register("construct_explorer_page_queryset")
def hide_other_users_personal_spaces(parent_page, pages, request):
    """
    In lista de pagini din admin, un user obisnuit trebuie sa vada doar
    propriul spatiu personal, nu si pe ale colegilor - desi toate stau in
    acelasi subarbore (Spatii personale), la care grupul "Angajati" are
    acces. Superuserii vad tot, ca de obicei.
    """
    if request.user.is_superuser:
        return pages

    if isinstance(parent_page.specific, PersonalSpaceIndexPage):
        # Pagina personala se crea pana acum doar la prima vizita pe site
        # (/spatiul-meu/) - daca userul intra direct in admin (fara sa fi
        # trecut pe site), nu avea inca nicio pagina de editat. O cream aici,
        # la prima navigare in aceasta sectiune din admin, ca sa existe
        # mereu, indiferent pe unde intra primul.
        PersonalSpacePage.get_or_create_for_user(request.user)

    return pages.filter(
        Q(personalspacepage__isnull=True) | Q(personalspacepage__owner_user=request.user)
    )


@hooks.register("before_edit_page")
def block_other_users_personal_space_edit(request, page):
    """
    A doua linie de aparare, in caz ca cineva acceseaza direct URL-ul de
    editare al spatiului personal al altcuiva (nu doar prin listare) -
    blocheaza accesul daca nu e proprietarul paginii sau superuser.
    """
    specific = page.specific
    if not isinstance(specific, PersonalSpacePage):
        return None

    if request.user.is_superuser or specific.owner_user_id == request.user.id:
        return None

    return HttpResponseForbidden("Nu ai acces la spatiul personal al altui utilizator.")


@hooks.register("construct_main_menu")
def hide_media_library_for_angajati(request, menu_items):
    """
    Angajatii pot tot adauga imagini/documente direct din blocurile de
    continut (upload nou, la editarea unei pagini) - dar nu are sens sa
    poata rasfoi din meniul principal toata biblioteca de imagini/documente,
    unde ar vedea si fisierele incarcate de colegi. Moderators pastreaza
    accesul complet la meniu, ca de obicei.
    """
    if request.user.is_superuser or not request.user.groups.filter(name="Angajati").exists():
        return

    menu_items[:] = [item for item in menu_items if item.name not in ("images", "documents")]
