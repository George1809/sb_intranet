from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Q
from django.template.response import TemplateResponse

from wagtail.models import Page

from home.models import (
    MenuPageDocument,
    MenuPageImage,
    MenuPageLink,
    MenuPageManualResource,
    PersonalSpaceIndexPage,
    PersonalSpacePage,
)

# To enable logging of search queries for use with the "Promoted search results" module
# <https://docs.wagtail.org/en/stable/reference/contrib/searchpromotions.html>
# uncomment the following line and the lines indicated in the search function
# (after adding wagtail.contrib.search_promotions to INSTALLED_APPS):

# from wagtail.contrib.search_promotions.models import Query


def _page_results(search_query):
    # Spatiile personale sunt private (fiecare user le vede doar pe ale lui
    # in admin) - nu trebuie sa apara nici in cautarea globala, altfel un
    # user ar putea gasi titlul spatiului altcuiva doar cautand un nume.
    pages = (
        Page.objects.live()
        .public()
        .not_type(PersonalSpacePage, PersonalSpaceIndexPage)
        .search(search_query)
    )
    return [
        {
            "kind": "page",
            "title": result.title,
            "subtitle": "Sectiune intranet",
            "url": result.url,
            "new_tab": False,
        }
        for result in pages
        if result.url
    ]


def _resource_results(search_query):
    results = []

    documents = MenuPageDocument.objects.filter(
        title__icontains=search_query, page__live=True
    ).select_related("page", "document")
    for item in documents:
        if item.document:
            results.append(
                {
                    "kind": "document",
                    "title": item.title,
                    "subtitle": item.page.title,
                    "url": item.document.url,
                    "new_tab": True,
                }
            )

    images = MenuPageImage.objects.filter(
        title__icontains=search_query, page__live=True
    ).select_related("page", "image")
    for item in images:
        if item.image:
            results.append(
                {
                    "kind": "image",
                    "title": item.title,
                    "subtitle": item.page.title,
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
        results.append(
            {
                "kind": "manual",
                "title": item.title,
                "subtitle": item.page.title,
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
        results.append(
            {
                "kind": "link",
                "title": item.title,
                "subtitle": item.page.title,
                "url": item.url,
                "new_tab": True,
            }
        )

    return results


def search(request):
    search_query = request.GET.get("query", "").strip()
    page = request.GET.get("page", 1)

    all_results = []
    if search_query:
        all_results = _page_results(search_query) + _resource_results(search_query)

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
        },
    )
