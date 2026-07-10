from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand, CommandError

from wagtail.documents.models import Document
from wagtail.images.models import Image
from wagtail.models import (
    Collection,
    GroupApprovalTask,
    GroupCollectionPermission,
    GroupPagePermission,
    Page,
    Workflow,
    WorkflowPage,
    WorkflowTask,
)

from home.models import ErrorIndexPage, FAQIndexPage, MenuPage, PersonalSpacePage

MODERATORS_GROUP_NAME = "Moderatori Suport"
LIMITED_GROUP_NAME = "Acces limitat - Suport"
WORKFLOW_NAME = "Aprobare Suport"
APPROVAL_TASK_NAME = "Aprobare moderator suport"


class Command(BaseCommand):
    help = (
        "Configureaza (idempotent) sectiunile Erori comune si Intrebari sub Suport, "
        "grupurile de permisiuni si workflow-ul de moderare. Optional, adauga useri "
        "cu acces limitat (Erori + Intrebari + spatiu personal propriu)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--limited-user",
            action="append",
            default=[],
            metavar="EMAIL_SAU_USERNAME",
            help="User caruia i se acorda acces limitat. Poate fi dat de mai multe ori.",
        )

    def handle(self, *args, **options):
        page_ct = ContentType.objects.get_for_model(Page)
        add_perm = Permission.objects.get(content_type=page_ct, codename="add_page")
        change_perm = Permission.objects.get(content_type=page_ct, codename="change_page")
        publish_perm = Permission.objects.get(content_type=page_ct, codename="publish_page")
        access_admin_perm = Permission.objects.get(
            content_type=ContentType.objects.get(app_label="wagtailadmin", model="admin"),
            codename="access_admin",
        )

        suport = MenuPage.objects.filter(slug="suport").first()
        if suport is None:
            raise CommandError("Nu am gasit meniul 'Suport' - creeaza-l intai din admin.")

        error_index = ErrorIndexPage.objects.first()
        if error_index is None:
            error_index = ErrorIndexPage(title="Erori comune", slug="erori-comune")
            suport.add_child(instance=error_index)
            error_index.save_revision().publish()
            self.stdout.write(self.style.SUCCESS("Creat 'Erori comune' sub Suport."))

        faq_index = FAQIndexPage.objects.first()
        if faq_index is None:
            faq_index = FAQIndexPage(title="Intrebari", slug="intrebari")
            suport.add_child(instance=faq_index)
            faq_index.save_revision().publish()
            self.stdout.write(self.style.SUCCESS("Creat 'Intrebari' sub Suport."))

        moderators_group, _ = Group.objects.get_or_create(name=MODERATORS_GROUP_NAME)
        moderators_group.permissions.add(access_admin_perm)
        for superuser in get_user_model().objects.filter(is_superuser=True):
            superuser.groups.add(moderators_group)

        limited_group, _ = Group.objects.get_or_create(name=LIMITED_GROUP_NAME)
        limited_group.permissions.add(access_admin_perm)
        for page in (error_index, faq_index):
            for perm in (add_perm, change_perm):
                GroupPagePermission.objects.get_or_create(
                    group=limited_group, page=page, permission=perm
                )

        # Fara asta, StreamField-ul (imagini/documente/video) nu are cum sa
        # ofere upload - biblioteca de imagini/documente are propriul sistem
        # de permisiuni, separat de cel al paginilor.
        root_collection = Collection.get_first_root_node()
        for model in (Image, Document):
            model_ct = ContentType.objects.get_for_model(model)
            for codename in (f"add_{model._meta.model_name}", f"choose_{model._meta.model_name}"):
                perm = Permission.objects.get(content_type=model_ct, codename=codename)
                GroupCollectionPermission.objects.get_or_create(
                    group=limited_group, collection=root_collection, permission=perm
                )

        workflow, _ = Workflow.objects.get_or_create(name=WORKFLOW_NAME)
        task, task_created = GroupApprovalTask.objects.get_or_create(name=APPROVAL_TASK_NAME)
        if task_created:
            task.groups.set([moderators_group])
        WorkflowTask.objects.get_or_create(
            workflow=workflow, task=task.task_ptr, defaults={"sort_order": 0}
        )
        for page in (error_index, faq_index):
            WorkflowPage.objects.get_or_create(page=page, defaults={"workflow": workflow})

        self.stdout.write(self.style.SUCCESS("Grupuri, permisiuni si workflow configurate."))

        User = get_user_model()
        for identifier in options["limited_user"]:
            user = (
                User.objects.filter(email=identifier).first()
                or User.objects.filter(username=identifier).first()
            )
            if user is None:
                raise CommandError(f"Nu am gasit userul '{identifier}'")

            user.groups.add(limited_group)

            personal_page = PersonalSpacePage.get_or_create_for_user(user)
            personal_group, _ = Group.objects.get_or_create(
                name=f"Spatiu personal - {user.username}"
            )
            personal_group.permissions.add(access_admin_perm)
            for perm in (change_perm, publish_perm):
                GroupPagePermission.objects.get_or_create(
                    group=personal_group, page=personal_page, permission=perm
                )
            user.groups.add(personal_group)

            self.stdout.write(self.style.SUCCESS(f"Acces limitat configurat pentru {user}."))
