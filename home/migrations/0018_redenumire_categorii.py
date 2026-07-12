from django.db import migrations
from django.utils.text import slugify


RENAMES = {
    "SmartBill Gestiune/Facturare Cloud": "Gestiune/Facturare Cloud",
    "SmartBill Conta": "Conta",
}


def rename(apps, schema_editor):
    from home.models import ErrorCategoryPage, FAQCategoryPage

    for model in (ErrorCategoryPage, FAQCategoryPage):
        for old_title, new_title in RENAMES.items():
            category = model.objects.filter(title=old_title).first()
            if category is None:
                continue
            category.title = new_title
            category.slug = slugify(new_title)
            category.save_revision().publish()


def rename_back(apps, schema_editor):
    from home.models import ErrorCategoryPage, FAQCategoryPage

    for model in (ErrorCategoryPage, FAQCategoryPage):
        for old_title, new_title in RENAMES.items():
            category = model.objects.filter(title=new_title).first()
            if category is None:
                continue
            category.title = old_title
            category.slug = slugify(old_title)
            category.save_revision().publish()


class Migration(migrations.Migration):

    dependencies = [
        ("home", "0017_categorii_erori_intrebari"),
    ]

    operations = [
        migrations.RunPython(rename, rename_back),
    ]
