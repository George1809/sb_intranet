from django.db.models import Q
from django.http import HttpResponseForbidden
from django.utils.html import escape

from wagtail import hooks
from wagtail.documents.rich_text import DocumentLinkHandler
from wagtail.models import TaskState, WorkflowState
from wagtail.rich_text import LinkHandler
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


class ExternalLinkInNewTabHandler(LinkHandler):
    """
    Wagtail nu inregistreaza niciun handler implicit pentru linkurile
    "external" din RichText (cele adaugate ca text intr-un paragraf, cu
    butonul de link din editor) - fara asta, ele raman <a href="..."> simplu,
    fara target, deci se deschid in aceeasi pagina. Butoanele de resurse
    (MenuPageLink etc.) au deja new_tab=True cablat separat in template,
    doar linkurile din interiorul unui paragraf treceau pe langa asta.
    """

    identifier = "external"

    @classmethod
    def expand_db_attributes(cls, attrs):
        href = escape(attrs["href"])
        return f'<a href="{href}" target="_blank" rel="noopener noreferrer">'


@hooks.register("register_rich_text_features")
def register_external_link_new_tab(features):
    features.register_link_type(ExternalLinkInNewTabHandler)


class DocumentLinkInNewTabHandler(DocumentLinkHandler):
    """
    La fel ca ExternalLinkInNewTabHandler, dar pentru linkurile catre
    Documente alese din biblioteca (nu URL introdus manual) - handler-ul
    implicit Wagtail (DocumentLinkHandler) rezolva doar href-ul catre fisier,
    fara target, deci se deschideau in aceeasi pagina.
    """

    @classmethod
    def expand_db_attributes_many(cls, attrs_list):
        return [
            tag[:-1] + ' target="_blank" rel="noopener noreferrer">'
            if tag.startswith('<a href=')
            else tag
            for tag in super().expand_db_attributes_many(attrs_list)
        ]


@hooks.register("register_rich_text_features", order=100)
def register_document_link_new_tab(features):
    # order=100: hook-urile ruleaza sortate dupa "order", iar hook-ul propriu
    # al lui wagtail.documents (care inregistreaza handler-ul implicit, fara
    # target) ruleaza dupa "home" la order=0 implicit (INSTALLED_APPS il are
    # dupa "home") si suprascrie orice inregistrare anterioara pe acelasi
    # identifier ("document"). Cu order mare, hook-ul asta ruleaza ultimul si
    # castiga suprascrierea.
    features.register_link_type(DocumentLinkInNewTabHandler)


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


@hooks.register("before_delete_page")
def block_other_users_personal_space_delete(request, page):
    """
    La fel ca block_other_users_personal_space_edit, dar pentru stergere -
    permisiunile Wagtail (change_page + publish_page pe tot subarborele
    "Spatii personale") fac ca can_delete() sa treaca fara nicio verificare
    de proprietar, deci fara acest hook orice Angajat putea sterge spatiul
    personal al oricui altcuiva, stiind doar ID-ul paginii.
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
