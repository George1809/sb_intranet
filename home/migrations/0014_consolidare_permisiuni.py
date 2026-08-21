from django.db import migrations

OLD_GROUP_NAMES = [
    "Moderatori Suport",
    "Acces limitat - Suport",
]
OLD_WORKFLOW_NAME = "Aprobare Suport"
NEW_WORKFLOW_NAME = "Aprobare Angajati"


def consolidate(apps, schema_editor):
    from django.contrib.auth.models import Group
    from wagtail.models import GroupApprovalTask, Workflow, WorkflowPage

    from home.models import ErrorIndexPage, FAQIndexPage

    # De la grup separat per user ("Spatiu personal"), plus 2 grupuri fixe legate doar de Suport acum e un singur grup (de la "Angajati" la "Users" cum e acum).
    Group.objects.filter(name__startswith="Spatiu personal - ").delete()
    Group.objects.filter(name__in=OLD_GROUP_NAMES).delete()

    # Sters workflow-ul vechi (cel de Suport), o pagina poate fi legata doar de un singur workflow o data, nu poti avea 2 in acelasi timp.
    # Pentru a se lega workflow-ul cel corect, trebuie intai scoasa legatura veche, ca sa fie loc pentru cea noua.
    old_workflow = Workflow.objects.filter(name=OLD_WORKFLOW_NAME).first()
    if old_workflow is not None:
        WorkflowPage.objects.filter(workflow=old_workflow).delete()
        for workflow_task in old_workflow.workflow_tasks.all():
            workflow_task.task.delete()
        old_workflow.delete()

    # Paginile Cazuri/Erori si FAQ se leaga de workflow-ul corect ("Aprobare Angajati"), folosit pentru toata lumea.
    new_workflow = Workflow.objects.filter(name=NEW_WORKFLOW_NAME).first()
    error_index = ErrorIndexPage.objects.first()
    faq_index = FAQIndexPage.objects.first()
    if new_workflow is not None:
        for page in (error_index, faq_index):
            if page is not None:
                WorkflowPage.objects.get_or_create(
                    page=page.page_ptr, defaults={"workflow": new_workflow}
                )


def reverse_consolidate(apps, schema_editor):
    # Gol intentionat - daca cineva da reverse, sistemul vechi (sters mai sus) nu se recreeaza, oricum trebuia sa dispara definitiv.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("home", "0013_alter_personalspacesection_body"),
    ]

    operations = [
        migrations.RunPython(consolidate, reverse_consolidate),
    ]
