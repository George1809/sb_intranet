from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Q
from django.template.response import TemplateResponse

from wagtail.models import Page

from home.models import (
    ErrorReportPage,
    FAQEntryPage,
    MenuPageDocument,
    MenuPageImage,
    MenuPageLink,
    MenuPageManualResource,
)

# To enable logging of search queries for use with the "Promoted search results" module
# <https://docs.wagtail.org/en/stable/reference/contrib/searchpromotions.html>
# uncomment the following line and the lines indicated in the search function
# (after adding wagtail.contrib.search_promotions to INSTALLED_APPS):

# from wagtail.contrib.search_promotions.models import Query


# Sectiuni de start (copii directi ai Home) excluse intentionat din cautare -
# nu au butoane finale relevante de gasit prin cautare (Training e cadru de
# curs, Tools sunt utilitare interne cu propria navigare), decizie explicita
# a userului, nu regula generala.
EXCLUDED_TOP_LEVEL_SLUGS = {"training", "tools"}


def _in_excluded_section(page):
    top_level = page.get_ancestors(inclusive=True).filter(depth=3).first()
    return top_level is not None and top_level.slug in EXCLUDED_TOP_LEVEL_SLUGS


def _location(page):
    # Nume de sectiuni se pot repeta in locuri diferite (ex. "Proceduri" sub
    # Vanzari SI sub Suport) - doar numele paginii-parinte nu e suficient ca
    # sa distingi unde e de fapt rezultatul. path_prefix = tot lantul de
    # deasupra (fara Home/root), location = pagina imediata (unde sta itemul).
    ancestors = [
        a.title for a in page.get_ancestors() if not a.is_root() and a.depth > 2
    ]
    return " / ".join(ancestors), page.title


def _knowledge_base_results(search_query):
    # Erorile si intrebarile sunt "butoane finale" din perspectiva userului
    # (continut documentat, nu doar o sectiune de navigare), desi tehnic sunt
    # pagini Wagtail adevarate, nu inregistrari MenuPageX - de aceea folosesc
    # indexul de cautare Wagtail (title + description/body), nu un filtru
    # icontains ca la resurse.
    entries = (
        Page.objects.live()
        .public()
        .type(ErrorReportPage, FAQEntryPage)
        .search(search_query)
    )

    results = []
    for base_result in entries:
        if not base_result.url:
            continue
        result = base_result.specific
        if _in_excluded_section(result):
            continue

        kind = "error" if isinstance(result, ErrorReportPage) else "faq"
        path_prefix, subtitle = _location(result.get_parent())
        results.append(
            {
                "kind": kind,
                "title": result.title,
                "path_prefix": path_prefix,
                "subtitle": subtitle,
                "url": result.url,
                "new_tab": False,
            }
        )

    return results


def _resource_results(search_query):
    results = []

    documents = MenuPageDocument.objects.filter(
        title__icontains=search_query, page__live=True
    ).select_related("page", "document")
    for item in documents:
        if item.document and not _in_excluded_section(item.page):
            path_prefix, subtitle = _location(item.page)
            results.append(
                {
                    "kind": "document",
                    "title": item.title,
                    "path_prefix": path_prefix,
                    "subtitle": subtitle,
                    "url": item.document.url,
                    "new_tab": True,
                }
            )

    images = MenuPageImage.objects.filter(
        title__icontains=search_query, page__live=True
    ).select_related("page", "image")
    for item in images:
        if item.image and not _in_excluded_section(item.page):
            path_prefix, subtitle = _location(item.page)
            results.append(
                {
                    "kind": "image",
                    "title": item.title,
                    "path_prefix": path_prefix,
                    "subtitle": subtitle,
                    "url": item.image.file.url,
                    "new_tab": True,
                }
            )

    manuals = (
        MenuPageManualResource.objects.filter(page__live=True)
        .filter(Q(title__icontains=search_query) | Q(description__icontains=search_query))
        .select_related("page")
    )
    for item in manuals:
        if _in_excluded_section(item.page):
            continue
        path_prefix, subtitle = _location(item.page)
        results.append(
            {
                "kind": "manual",
                "title": item.title,
                "path_prefix": path_prefix,
                "subtitle": subtitle,
                "url": item.url,
                "new_tab": False,
            }
        )

    links = (
        MenuPageLink.objects.filter(page__live=True)
        .filter(Q(title__icontains=search_query) | Q(description__icontains=search_query))
        .select_related("page")
    )
    for item in links:
        if _in_excluded_section(item.page):
            continue
        path_prefix, subtitle = _location(item.page)
        results.append(
            {
                "kind": "link",
                "title": item.title,
                "path_prefix": path_prefix,
                "subtitle": subtitle,
                "url": item.url,
                "new_tab": True,
            }
        )

    return results


def _pagination_window(current, total, neighbors=2):
    """
    Numerele de pagina de aratat explicit (plus None pt "..." intre goluri) -
    fara asta, la multe pagini rezultate, s-ar afisa un buton per pagina
    (ex. 30 de butoane intr-un rand). Pastreaza mereu prima, ultima, pagina
    curenta si cateva vecine - restul se comprima la "...".
    """
    if total <= 7:
        return list(range(1, total + 1))

    pages = {1, total, current}
    for offset in range(1, neighbors + 1):
        pages.add(current - offset)
        pages.add(current + offset)
    pages = sorted(p for p in pages if 1 <= p <= total)

    window = []
    previous = None
    for p in pages:
        if previous is not None and p - previous > 1:
            window.append(None)
        window.append(p)
        previous = p
    return window


def search(request):
    search_query = request.GET.get("query", "").strip()
    page = request.GET.get("page", 1)

    all_results = []
    if search_query:
        all_results = _knowledge_base_results(search_query) + _resource_results(search_query)

    # Pagination
    paginator = Paginator(all_results, 10)
    try:
        search_results = paginator.page(page)
    except PageNotAnInteger:
        search_results = paginator.page(1)
    except EmptyPage:
        search_results = paginator.page(paginator.num_pages)

    return TemplateResponse(
        request,
        "search/search.html",
        {
            "search_query": search_query,
            "search_results": search_results,
            "result_count": len(all_results),
            "pagination_window": _pagination_window(
                search_results.number, paginator.num_pages
            ),
        },
    )
