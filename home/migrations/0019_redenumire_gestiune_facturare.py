from django.db import migrations
from django.utils.text import slugify


OLD_TITLE = "Gestiune/Facturare Cloud"
NEW_TITLE = "Gestiune-Facturare Cloud"


def rename(apps, schema_editor):
    from home.models import ErrorCategoryPage, FAQCategoryPage

    for model in (ErrorCategoryPage, FAQCategoryPage):
        category = model.objects.filter(title=OLD_TITLE).first()
        if category is None:
            continue
        category.title = NEW_TITLE
        category.slug = slugify(NEW_TITLE)
        category.save_revision().publish()


def rename_back(apps, schema_editor):
    from home.models import ErrorCategoryPage, FAQCategoryPage

    for model in (ErrorCategoryPage, FAQCategoryPage):
        category = model.objects.filter(title=NEW_TITLE).first()
        if category is None:
            continue
        category.title = OLD_TITLE
        category.slug = slugify(OLD_TITLE)
        category.save_revision().publish()


class Migration(migrations.Migration):

    dependencies = [
        ("home", "0018_redenumire_categorii"),
    ]

    operations = [
        migrations.RunPython(rename, rename_back),
    ]
