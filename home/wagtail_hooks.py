from wagtail import hooks
from wagtail.models import TaskState, WorkflowState
from wagtail.signals import (
    task_submitted,
    workflow_approved,
    workflow_rejected,
    workflow_submitted,
)

# Oprite temporar notificarile automate prin email la submit/aprobare/
# respingere in workflow, cat timp testam manual fluxul de moderare.
# De reactivat cand implementam corect linkurile din emailuri
# (WAGTAILADMIN_BASE_URL) si continutul notificarilor.
# Trebuie sa ruleze dupa ce wagtail.admin isi conecteaza propriile semnale
# (se intampla la ready()); wagtail_hooks.py e importat mai tarziu, la prima
# cautare de hook-uri, deci ordinea e garantata corecta.
task_submitted.disconnect(
    sender=TaskState,
    dispatch_uid="group_approval_task_submitted_email_notification",
)
workflow_submitted.disconnect(
    sender=WorkflowState,
    dispatch_uid="workflow_state_submitted_email_notification",
)
workflow_rejected.disconnect(
    sender=WorkflowState,
    dispatch_uid="workflow_state_rejected_email_notification",
)
workflow_approved.disconnect(
    sender=WorkflowState,
    dispatch_uid="workflow_state_approved_email_notification",
)


@hooks.register("construct_reports_menu")
def hide_reports_for_limited_users(request, menu_items):
    """
    Rapoartele (Workflows, Site history, Aging pages etc.) sunt utile doar
    pentru administratorii cu acces total - userii cu acces limitat nu au
    nevoie de ele, deci le ascundem complet (meniul Reports dispare singur
    daca ramane fara elemente).
    """
    if not request.user.is_superuser:
        menu_items.clear()
