from django.db import models

from modelcluster.fields import ParentalKey

from wagtail.admin.panels import FieldPanel, InlinePanel
from wagtail.documents.models import Document
from wagtail.models import Orderable, Page


class HomePage(Page):
    intro = models.CharField(max_length=255, blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
    ]

    subpage_types = [
        "home.MenuPage",
    ]

    def get_context(self, request):
        context = super().get_context(request)
        context["children"] = self.get_children().live().public()  # type: ignore[attr-defined]
        return context


class MenuPage(Page):
    intro = models.CharField(max_length=255, blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
        InlinePanel("documents", label="Butoane PDF"),
    ]

    parent_page_types = [
        "home.HomePage",
        "home.MenuPage",
    ]

    subpage_types = [
        "home.MenuPage",
    ]

    def get_context(self, request):
        context = super().get_context(request)
        context["children"] = self.get_children().live().public()  # type: ignore[attr-defined]
        return context


class MenuPageDocument(Orderable):
    page = ParentalKey(
        "home.MenuPage",
        on_delete=models.CASCADE,
        related_name="documents",
    )

    title = models.CharField(max_length=255)

    document = models.ForeignKey(
        Document,
        null=True,
        blank=False,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    panels = [
        FieldPanel("title"),
        FieldPanel("document"),
    ]