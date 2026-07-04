from wagtail.models import Site


def main_menu(request):
    try:
        site = Site.find_for_request(request)
        root_page = site.root_page.specific
        pages = root_page.get_children().live().specific()
    except Exception:
        pages = []

    return {
        "main_menu_pages": pages,
    }
