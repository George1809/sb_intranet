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

    # --- Sterge grupurile "per-user" ramase de la sistemul vechi (orice
    # grup care incepe cu "Spatiu personal - ") si cele 2 fixe ---
    Group.objects.filter(name__startswith="Spatiu personal - ").delete()
    Group.objects.filter(name__in=OLD_GROUP_NAMES).delete()

    # --- Sterge workflow-ul vechi (elibereaza legatura OneToOne cu paginile,
    # ca sa poata fi preluata de workflow-ul corect de mai jos) ---
    old_workflow = Workflow.objects.filter(name=OLD_WORKFLOW_NAME).first()
    if old_workflow is not None:
        WorkflowPage.objects.filter(workflow=old_workflow).delete()
        for workflow_task in old_workflow.workflow_tasks.all():
            workflow_task.task.delete()
        old_workflow.delete()

    # --- Leaga corect workflow-ul "Aprobare Angajati" de paginile Erori/FAQ,
    # acum ca sloturile OneToOne sunt libere ---
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
    # Ireversibil intentionat - sistemul vechi (grupuri/workflow ad-hoc) nu
    # se recreeaza la reverse, era oricum destinat sa fie inlocuit.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("home", "0013_alter_personalspacesection_body"),
    ]

    operations = [
        migrations.RunPython(consolidate, reverse_consolidate),
    ]
