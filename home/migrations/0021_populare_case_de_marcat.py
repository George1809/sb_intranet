from django.db import migrations


PARENT_MENU_SLUG = "suport"

# Date de start, preluate din intranetul vechi - editabile ulterior din admin
# (inclusiv Ghid/Erori comune, care se completeaza manual dupa ce paginile
# corespunzatoare exista).
ROWS = [
    ("Datecs", "DP 150/MX", True, True, True, True),
    ("Datecs", "DP 25/MX", True, True, True, True),
    ("Datecs", "WP50/MX", True, True, True, True),
    ("Datecs", "WP500/MX", True, True, True, True),
    ("Datecs", "Blue Cash 50 - Dispozitiv cu casa de marcat inclusa (Doar Android)", False, False, False, True),
    ("Datecs Imprimante fiscale", "FP650", True, False, True, False),
    ("Datecs Imprimante fiscale", "FP700", True, False, True, False),
    ("Datecs Imprimante fiscale", "FP800", True, False, True, False),
    ("Daisy", "Expert SX", True, False, True, True),
    ("Daisy", "Compact S", True, False, True, True),
    ("Daisy", "Compact M", True, False, True, True),
    ("Daisy", "Perfect M", True, False, True, True),
    ("Tremol/Activa", "Tremol M20 (Seria VF)", True, True, True, True),
    ("Tremol/Activa", "Tremol M20 (Serii EC, AC, DP, etc)", True, True, True, True),
    ("Tremol/Activa", "Activa Galaxy Plus", True, True, True, True),
    ("Tremol/Activa", "Adpos S25 (Tremol S25)", False, False, True, True),
    ("Tremol/Activa", "Tremol M20 Adpos M", True, True, True, True),
    ("Partner", "200", True, False, True, False),
    ("Partner", "300", False, False, True, False),
    ("Partner", "600", True, False, True, False),
    ("Eltrade", "A1", False, True, True, False),
]


def create_page(apps, schema_editor):
    from home.models import CashRegisterCompatibilityPage, CashRegisterModel, MenuPage

    suport = MenuPage.objects.filter(slug=PARENT_MENU_SLUG).first()
    if suport is None:
        return

    # Un MenuPage gol, cu acelasi slug, a fost creat mai devreme ca placeholder
    # pentru aceasta pagina - il inlocuim, nu are continut de pierdut.
    placeholder = MenuPage.objects.filter(
        slug="case-de-marcat", path__startswith=suport.path
    ).exclude(
        documents__isnull=False
    ).exclude(
        images__isnull=False
    ).exclude(
        manual_resources__isnull=False
    ).exclude(
        links__isnull=False
    ).first()
    if placeholder is not None:
        placeholder.delete()

    page = CashRegisterCompatibilityPage.objects.first()
    if page is None:
        page = CashRegisterCompatibilityPage(
            title="Case de marcat", slug="case-de-marcat", show_in_menus=True
        )
        suport.add_child(instance=page)
        page.save_revision().publish()

    if not page.compatibility_rows.exists():
        for order, (brand, model_name, cloud, cloud_android, pos_windows, pos_android) in enumerate(ROWS):
            CashRegisterModel.objects.create(
                page=page,
                sort_order=order,
                brand=brand,
                model_name=model_name,
                compatible_cloud=cloud,
                compatible_cloud_android=cloud_android,
                compatible_pos_windows=pos_windows,
                compatible_pos_android=pos_android,
            )


def remove_page(apps, schema_editor):
    from home.models import CashRegisterCompatibilityPage

    CashRegisterCompatibilityPage.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("home", "0020_cashregistercompatibilitypage_cashregistermodel"),
        ("wagtailsearch", "0010_add_text_fields"),
    ]

    operations = [
        migrations.RunPython(create_page, remove_page),
    ]
