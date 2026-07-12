from django.templatetags.static import static

from home.models import PersonalSpaceIndexPage

from wagtail.models import Site


DASHBOARD_MENU_TITLES = {
    "Release Notes",
    "Tools",
    "Training",
    "Quick links",
}


def main_menu(request):
    fallback_avatar_url = static("img/favi.png")
    user_avatar_url = fallback_avatar_url
    can_access_admin = False

    if request.user.is_authenticated:
        userprofile = getattr(request.user, "wagtail_userprofile", None)
        if userprofile and userprofile.avatar:
            user_avatar_url = userprofile.avatar.url
        can_access_admin = request.user.has_perm("wagtailadmin.access_admin")

    site = Site.find_for_request(request)
    if site:
        root_page = site.root_page.specific
        pages = [
            page
            for page in root_page.get_children().live().specific()
            if page.title not in DASHBOARD_MENU_TITLES
            and not isinstance(page, PersonalSpaceIndexPage)
        ]
    else:
        pages = []

    return {
        "main_menu_pages": pages,
        "user_avatar_url": user_avatar_url,
        "can_access_admin": can_access_admin,
    }
