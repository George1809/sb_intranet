from django.db.models import Q
from django.http import HttpResponseForbidden
from django.utils.html import escape

from wagtail import hooks
from wagtail.documents.rich_text import DocumentLinkHandler
from wagtail.rich_text import LinkHandler

from home.models import PersonalSpaceIndexPage, PersonalSpacePage


# Wagtail cauta automat orice fisier numit wagtail_hooks.py din orice app - nu trebuie inregistrat nicaieri, il gaseste singur la pornire.
# Logica scrisa pentru chestii pe care Wagtail nu le poate face singur (linkuri in tab nou, ascundere meniuri admin dupa grup, izolare spatii personale).


class ExternalLinkInNewTabHandler(LinkHandler):
    """
    Wagtail nu are ceva implicit pentru linkurile "external" din RichText (link-uri manuale din paragrafe), 
    raman <a href="..."> simplu, fara target, deci se deschid tot in pagina curenta. 
    Butoanele dedicate (MenuPageLink si blocuri de link-uri) au target="_blank" pus direct in template, 
    dar linkurile din RichText nu trec prin template-ul ala, le randeaza Wagtail intern si de asta era nevoie de ceva separat pentru asta.
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
    Acelasi lucru ca mai sus, insa doar pentru documente adaugate in RichText. 
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
    """
    order=100 conventie wagtail hooks pentru a se suprascrie metoda si pentru a lua in calcul acest hook pentru deschidere link-uri cu documente in "target = _blank". 
    Cu valoare 0, ar fi rulat ultimul hook-ul implicit wagtail si s-ar fi deschis in aceeasi pagina. Asa, orice e mai mare de 0, ia in calcul acest hook.
    """
    features.register_link_type(DocumentLinkInNewTabHandler)


@hooks.register("construct_reports_menu")
def hide_reports_for_limited_users(request, menu_items):
    """
    Restrictie acces la meniul Reports (Workflows, Site history, Aging pages etc), nerelevant pentru Users si Moderators, 
    doar superuserii il vad.
    """
    if not request.user.is_superuser:
        menu_items.clear()


@hooks.register("construct_explorer_page_queryset")
def hide_other_users_personal_spaces(parent_page, pages, request):
    """
    In lista de pagini din admin un user isi poate vedea doar paginile lui,
    doar spatiul lui personal nu si al altor colegi, chiar daca toate stau
    in acelasi meniu (Spatii personale), unde grupurile "Moderators" si
    "Users" au acces.
    """
    if request.user.is_superuser:
        return pages

    if isinstance(parent_page.specific, PersonalSpaceIndexPage):
        # Pagina personala nu exista deloc in baza de date pana cand cineva nu intra in sectiunea "Spatii personale" din admin. 
        # Se creeaza chiar in acel moment, la prima intrare. 
        # Sectiunile din interior tot userul le adauga manual, separat, ca la orice MenuPage.


        PersonalSpacePage.get_or_create_for_user(request.user)

    return pages.filter(
        Q(personalspacepage__isnull=True) | Q(personalspacepage__owner_user=request.user)
    )


def _forbid_unless_owner_or_superuser(request, page):
    """
    Functie comuna, o folosesc toate hook-urile "before_*_page" de mai jos. Permisiunile din Wagtail (change_page + publish_page) 
    sunt date pe toata sectiunea "Spatii personale", nu pe pagina. Fara ea, orice user ar trece de can_edit()/can_delete()/can_unpublish()/can_copy() 
    pentru spatiul personal al oricui altcuiva, doar stiind ID-ul paginii.
    """


    specific = page.specific
    if not isinstance(specific, PersonalSpacePage):
        return None

    if request.user.is_superuser or specific.owner_user_id == request.user.id:
        return None

    return HttpResponseForbidden("Nu ai acces la spatiul personal al altui utilizator.")


@hooks.register("before_edit_page")
def block_other_users_personal_space_edit(request, page):
    return _forbid_unless_owner_or_superuser(request, page)


@hooks.register("before_delete_page")
def block_other_users_personal_space_delete(request, page):
    return _forbid_unless_owner_or_superuser(request, page)


@hooks.register("before_unpublish_page")
def block_other_users_personal_space_unpublish(request, page):
    return _forbid_unless_owner_or_superuser(request, page)


@hooks.register("before_copy_page")
def block_other_users_personal_space_copy(request, page):
    return _forbid_unless_owner_or_superuser(request, page)


@hooks.register("before_move_page")
def block_other_users_personal_space_move(request, page, destination):
    return _forbid_unless_owner_or_superuser(request, page)


@hooks.register("construct_main_menu")
def hide_media_library_for_users(request, menu_items):
    """
    Userii pot adauga poze/documente noi, direct din blocurile de continut, cand editeaza o pagina, 
    dar ascundem meniul principal din admin dedicat pentru asta, unde ar vedea si fisierele incarcate de colegi. 
    Moderators raman cu acces complet la meniu.
    """

    if request.user.is_superuser or not request.user.groups.filter(name="Users").exists():
        return

    menu_items[:] = [item for item in menu_items if item.name not in ("images", "documents")]
