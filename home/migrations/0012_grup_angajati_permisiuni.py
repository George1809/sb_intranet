from django.db import migrations


GROUP_NAME = "Angajati"
FAQ_ERROR_COLLECTION_NAME = "Cazuri & intrebari"
PERSONAL_SPACE_COLLECTION_NAME = "Spatii personale"
WORKFLOW_NAME = "Aprobare Angajati"


def create_permissions(apps, schema_editor):
    from django.contrib.auth.models import Group, Permission

    from wagtail.models import (
        Collection,
        GroupApprovalTask,
        GroupCollectionPermission,
        GroupPagePermission,
        Workflow,
        WorkflowPage,
        WorkflowTask,
    )

    from home.models import (
        ErrorIndexPage,
        FAQIndexPage,
        MenuPage,
        PersonalSpaceIndexPage,
    )

    # --- Pagini index FAQ/Erori, daca nu exista deja ---
    cazuri = MenuPage.objects.filter(slug="cazuri-intrebari").first()

    faq_index = FAQIndexPage.objects.first()
    if faq_index is None and cazuri is not None:
        faq_index = FAQIndexPage(title="Intrebari", slug="intrebari", show_in_menus=False)
        cazuri.add_child(instance=faq_index)
        faq_index.save_revision().publish()

    error_index = ErrorIndexPage.objects.first()
    if error_index is None and cazuri is not None:
        error_index = ErrorIndexPage(title="Erori", slug="erori", show_in_menus=False)
        cazuri.add_child(instance=error_index)
        error_index.save_revision().publish()

    personal_index = PersonalSpaceIndexPage.objects.first()

    # --- Grup ---
    group, _ = Group.objects.get_or_create(name=GROUP_NAME)

    access_admin = Permission.objects.get(
        content_type__app_label="wagtailadmin", codename="access_admin"
    )
    group.permissions.add(access_admin)

    def grant_collection_permissions(collection, app_label, codenames):
        if collection is None:
            return
        for codename in codenames:
            permission = Permission.objects.filter(
                content_type__app_label=app_label, codename=codename
            ).first()
            if permission is not None:
                GroupCollectionPermission.objects.get_or_create(
                    group=group, collection=collection, permission=permission
                )

    # --- Poze: doar in Collection-ul "Cazuri & intrebari", nimic altundeva ---
    faq_collection = Collection.objects.filter(name=FAQ_ERROR_COLLECTION_NAME).first()
    grant_collection_permissions(faq_collection, "wagtailimages", ["add_image", "choose_image"])

    # --- Spatiul personal: poze + video ca fisier (documente), doar in colectia lor ---
    root_collection = Collection.get_first_root_node()
    personal_collection = None
    if root_collection is not None:
        personal_collection = root_collection.get_children().filter(
            name=PERSONAL_SPACE_COLLECTION_NAME
        ).first()
        if personal_collection is None:
            personal_collection = root_collection.add_child(name=PERSONAL_SPACE_COLLECTION_NAME)

    grant_collection_permissions(
        personal_collection, "wagtailimages", ["add_image", "choose_image"]
    )
    grant_collection_permissions(
        personal_collection, "wagtaildocs", ["add_document", "choose_document"]
    )

    # --- Pagini: FAQ/Erori -> pot crea/edita, NU pot publica (merge la aprobare) ---
    def grant_page_permissions(page, codenames):
        if page is None:
            return
        for codename in codenames:
            permission = Permission.objects.get(
                content_type__app_label="wagtailcore", codename=codename
            )
            GroupPagePermission.objects.get_or_create(
                group=group, page=page.page_ptr if hasattr(page, "page_ptr") else page,
                permission=permission,
            )

    grant_page_permissions(faq_index, ["add_page", "change_page"])
    grant_page_permissions(error_index, ["add_page", "change_page"])

    # --- Spatiu personal: pot crea/edita SI publica (al lor, direct) ---
    grant_page_permissions(personal_index, ["add_page", "change_page", "publish_page"])

    # --- Workflow de aprobare pentru FAQ/Erori, aprobat de grupul Moderators ---
    moderators = Group.objects.filter(name="Moderators").first()
    if moderators is not None and faq_index is not None and error_index is not None:
        workflow, created = Workflow.objects.get_or_create(name=WORKFLOW_NAME)
        if created:
            task = GroupApprovalTask.objects.create(name=f"{WORKFLOW_NAME} - aprobare")
            task.groups.add(moderators)
            WorkflowTask.objects.create(workflow=workflow, task=task, sort_order=0)

        for page in (faq_index, error_index):
            WorkflowPage.objects.get_or_create(
                page=page.page_ptr if hasattr(page, "page_ptr") else page,
                defaults={"workflow": workflow},
            )


def remove_permissions(apps, schema_editor):
    from django.contrib.auth.models import Group
    from wagtail.models import Workflow, WorkflowPage

    workflow = Workflow.objects.filter(name=WORKFLOW_NAME).first()
    if workflow is not None:
        WorkflowPage.objects.filter(workflow=workflow).delete()
        for workflow_task in workflow.workflow_tasks.all():
            workflow_task.task.delete()
        workflow.delete()

    Group.objects.filter(name=GROUP_NAME).delete()
    # Paginile FAQ/Erori si Collection-ul nu se sterg la reverse - sunt continut,
    # nu configurare de permisiuni.


class Migration(migrations.Migration):

    dependencies = [
        ("home", "0011_remove_personalspacepage_body_personalspacesection"),
    ]

    operations = [
        migrations.RunPython(create_permissions, remove_permissions),
    ]
