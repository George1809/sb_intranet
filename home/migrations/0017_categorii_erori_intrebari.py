from django.db import migrations
from django.utils.text import slugify


GROUP_NAME = "Angajati"

CATEGORY_TITLES = [
    "SmartBill Gestiune/Facturare Cloud",
    "SmartBill POS",
    "SmartBill Conta",
    "Integrari",
]


def create_categories(apps, schema_editor):
    from django.contrib.auth.models import Group, Permission

    from wagtail.models import GroupPagePermission

    from home.models import ErrorCategoryPage, ErrorIndexPage, FAQCategoryPage, FAQIndexPage

    group = Group.objects.filter(name=GROUP_NAME).first()

    add_permission = Permission.objects.get(
        content_type__app_label="wagtailcore", codename="add_page"
    )
    change_permission = Permission.objects.get(
        content_type__app_label="wagtailcore", codename="change_page"
    )

    def revoke(page):
        if group is None or page is None:
            return
        GroupPagePermission.objects.filter(
            group=group,
            page=page.page_ptr if hasattr(page, "page_ptr") else page,
            permission__in=[add_permission, change_permission],
        ).delete()

    def grant(page):
        if group is None or page is None:
            return
        for permission in (add_permission, change_permission):
            GroupPagePermission.objects.get_or_create(
                group=group,
                page=page.page_ptr if hasattr(page, "page_ptr") else page,
                permission=permission,
            )

    error_index = ErrorIndexPage.objects.first()
    faq_index = FAQIndexPage.objects.first()

    # Angajatii nu mai primesc "add/change" direct pe index-uri - de acum
    # incolo primesc doar pe fiecare categorie in parte (varianta A: pot
    # adauga intrari, nu pot crea categorii noi).
    revoke(error_index)
    revoke(faq_index)

    if error_index is not None:
        for title in CATEGORY_TITLES:
            slug = slugify(title)
            category = ErrorCategoryPage.objects.filter(slug=slug).first()
            if category is None:
                category = ErrorCategoryPage(title=title, slug=slug, show_in_menus=False)
                error_index.add_child(instance=category)
                category.save_revision().publish()
            grant(category)

    if faq_index is not None:
        for title in CATEGORY_TITLES:
            slug = slugify(title)
            category = FAQCategoryPage.objects.filter(slug=slug).first()
            if category is None:
                category = FAQCategoryPage(title=title, slug=slug, show_in_menus=False)
                faq_index.add_child(instance=category)
                category.save_revision().publish()
            grant(category)


def remove_categories(apps, schema_editor):
    from django.contrib.auth.models import Group, Permission

    from wagtail.models import GroupPagePermission

    from home.models import ErrorCategoryPage, ErrorIndexPage, FAQCategoryPage, FAQIndexPage

    group = Group.objects.filter(name=GROUP_NAME).first()

    add_permission = Permission.objects.get(
        content_type__app_label="wagtailcore", codename="add_page"
    )
    change_permission = Permission.objects.get(
        content_type__app_label="wagtailcore", codename="change_page"
    )

    ErrorCategoryPage.objects.all().delete()
    FAQCategoryPage.objects.all().delete()

    if group is not None:
        error_index = ErrorIndexPage.objects.first()
        faq_index = FAQIndexPage.objects.first()
        for page in (error_index, faq_index):
            if page is None:
                continue
            for permission in (add_permission, change_permission):
                GroupPagePermission.objects.get_or_create(
                    group=group,
                    page=page.page_ptr if hasattr(page, "page_ptr") else page,
                    permission=permission,
                )


class Migration(migrations.Migration):

    dependencies = [
        ("home", "0016_errorcategorypage_faqcategorypage"),
        # Publicarea categoriilor declanseaza indexarea in cautare (add_child
        # -> save -> semnal modelsearch) - fara aceasta dependenta explicita,
        # migratia poate rula inaintea crearii tabelei wagtailsearch_indexentry
        # pe o baza de date noua (ex. la teste).
        ("wagtailsearch", "0010_add_text_fields"),
    ]

    operations = [
        migrations.RunPython(create_categories, remove_categories),
    ]
