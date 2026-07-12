from django.conf import settings
from django.db import models
from django.http import Http404
from django.shortcuts import redirect, render
from django.utils import timezone

from modelcluster.fields import ParentalKey

from wagtail import blocks
from wagtail.contrib.routable_page.models import RoutablePageMixin, route
from wagtail.admin.panels import FieldPanel, InlinePanel
from wagtail.documents.models import Document
from wagtail.documents.blocks import DocumentChooserBlock
from wagtail.embeds.blocks import EmbedBlock
from wagtail.fields import StreamField
from wagtail.images import get_image_model_string
from wagtail.images.blocks import ImageChooserBlock
from wagtail.models import Orderable, Page
from wagtail.search import index


# Blocuri StreamField comune, refolosite de paginile manuale, erori,
# intrebari si spatiul personal - un singur loc de intretinut.
STREAM_BODY_BLOCKS = [
    ("heading", blocks.CharBlock(form_classname="title", icon="title")),
    ("paragraph", blocks.RichTextBlock(icon="pilcrow")),
    ("image", ImageChooserBlock(icon="image")),
    (
        "video",
        EmbedBlock(
            icon="media",
            label="Video link",
            help_text="Pentru YouTube, Vimeo sau alte linkuri embed suportate.",
        ),
    ),
    (
        "video_upload",
        DocumentChooserBlock(
            icon="media",
            label="Video upload",
            help_text="Pentru fisiere video incarcate in Documents.",
        ),
    ),
    ("document", DocumentChooserBlock(icon="doc-full")),
    (
        "link",
        blocks.StructBlock(
            [
                ("title", blocks.CharBlock(max_length=255)),
                ("description", blocks.CharBlock(required=False, max_length=255)),
                ("url", blocks.URLBlock()),
            ],
            icon="link",
        ),
    ),
]


class HomePage(Page):
    intro = models.CharField(max_length=255, blank=True)
    dashboard_titles = {
        "Release Notes",
        "Tools",
        "Training",
        "Quick links",
    }

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
    ]

    subpage_types = [
        "home.MenuPage",
        "home.ErrorIndexPage",
        "home.FAQIndexPage",
        "home.PersonalSpaceIndexPage",
    ]

    def get_context(self, request):
        context = super().get_context(request)
        children = self.get_children().live().public().specific()  # type: ignore[attr-defined]
        children = [
            child for child in children if not isinstance(child, PersonalSpaceIndexPage)
        ]
        context["children"] = children
        context["dashboard_pages"] = [
            child for child in children if child.title in self.dashboard_titles
        ]
        return context


class MenuPage(RoutablePageMixin, Page):
    intro = models.CharField(max_length=255, blank=True)
    quick_links_slug = "quick-links"
    cazuri_intrebari_slug = "cazuri-intrebari"

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
        InlinePanel(
            "documents",
            label="Butoane PDF",
            classname="collapsible collapsed",
        ),
        InlinePanel(
            "images",
            label="Butoane imagine",
            classname="collapsible collapsed",
        ),
        InlinePanel(
            "manual_resources",
            label="Butoane pagina manuala",
            classname="collapsible collapsed",
        ),
        InlinePanel(
            "links",
            label="Linkuri",
            classname="collapsible collapsed",
        ),
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
        children = self.get_children().live().public().specific()  # type: ignore[attr-defined]
        resource_query = request.GET.get("q", "").strip()
        resource_items = []
        is_quick_links = self.slug == self.quick_links_slug
        is_cazuri_intrebari = self.slug == self.cazuri_intrebari_slug

        if not is_quick_links:
            for item in self.documents.select_related("document").all():
                if item.document:
                    resource_items.append(
                        {
                            "kind": "document",
                            "title": item.title,
                            "subtitle": item.document.title,
                            "url": item.document.url,
                            "created_at": item.created_at,
                            "new_tab": True,
                        }
                    )

            for item in self.images.select_related("image").all():
                if item.image:
                    resource_items.append(
                        {
                            "kind": "image",
                            "title": item.title,
                            "subtitle": item.image.title,
                            "url": item.image.file.url,
                            "created_at": item.created_at,
                            "new_tab": True,
                        }
                    )

            for item in self.manual_resources.all():
                resource_items.append(
                    {
                        "kind": "manual",
                        "title": item.title,
                        "subtitle": item.description or "Pagina manuala",
                        "url": item.url,
                        "created_at": item.created_at,
                        "new_tab": False,
                    }
                )

        for item in self.links.all():
            if item.url:
                subtitle = item.description
                if not subtitle:
                    subtitle = "Link rapid" if is_quick_links else "Link extern"
                resource_items.append(
                    {
                        "kind": "link",
                        "title": item.title,
                        "subtitle": subtitle,
                        "url": item.url,
                        "created_at": item.created_at,
                        "new_tab": True,
                    }
                )

        if resource_query:
            query = resource_query.casefold()
            resource_items = [
                item
                for item in resource_items
                if query in item["title"].casefold()
                or query in item["subtitle"].casefold()
            ]

        context["children"] = [] if (is_quick_links or is_cazuri_intrebari) else children
        context["is_quick_links"] = is_quick_links
        context["is_cazuri_intrebari"] = is_cazuri_intrebari
        context["resource_query"] = resource_query
        context["resource_items"] = resource_items

        if is_cazuri_intrebari:
            error_index = next(
                (c for c in children if isinstance(c, ErrorIndexPage)), None
            )
            faq_index = next(
                (c for c in children if isinstance(c, FAQIndexPage)), None
            )
            context["error_index"] = error_index
            context["faq_index"] = faq_index
            context["error_categories"] = (
                error_index.get_children().live().public().specific()  # type: ignore[attr-defined]
                if error_index
                else []
            )
            context["faq_categories"] = (
                faq_index.get_children().live().public().specific()  # type: ignore[attr-defined]
                if faq_index
                else []
            )
        if is_quick_links:
            context["has_resources"] = True
        else:
            context["has_resources"] = (
                self.documents.exists()
                or self.images.exists()
                or self.manual_resources.exists()
                or self.links.exists()
            )
        return context

    @route(r"^$")
    def page_view(self, request):
        return Page.serve(self, request)

    @route(r"^manual/(?P<manual_id>\d+)/$")
    def manual_resource(self, request, manual_id):
        try:
            manual_item = self.manual_resources.get(id=manual_id)
        except MenuPageManualResource.DoesNotExist as error:
            raise Http404 from error

        context = self.get_context(request)
        context["manual_item"] = manual_item
        return render(request, "home/manual_resource.html", context)


class MenuPageDocument(Orderable):
    page = ParentalKey(
        "home.MenuPage",
        on_delete=models.CASCADE,
        related_name="documents",
    )

    title = models.CharField(max_length=255)
    created_at = models.DateTimeField(default=timezone.now)

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


class MenuPageImage(Orderable):
    page = ParentalKey(
        "home.MenuPage",
        on_delete=models.CASCADE,
        related_name="images",
    )

    title = models.CharField(max_length=255)
    created_at = models.DateTimeField(default=timezone.now)

    image = models.ForeignKey(
        get_image_model_string(),
        null=True,
        blank=False,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    panels = [
        FieldPanel("title"),
        FieldPanel("image"),
    ]


class MenuPageManualResource(Orderable):
    page = ParentalKey(
        "home.MenuPage",
        on_delete=models.CASCADE,
        related_name="manual_resources",
    )

    title = models.CharField(max_length=255)
    description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    body = StreamField(STREAM_BODY_BLOCKS, blank=True, use_json_field=True)

    panels = [
        FieldPanel("title"),
        FieldPanel("description"),
        FieldPanel("body"),
    ]

    @property
    def url(self):
        return f"{self.page.url}manual/{self.pk}/"


class MenuPageLink(Orderable):
    page = ParentalKey(
        "home.MenuPage",
        on_delete=models.CASCADE,
        related_name="links",
    )

    title = models.CharField(max_length=255)
    description = models.CharField(max_length=255, blank=True)
    url = models.URLField()
    created_at = models.DateTimeField(default=timezone.now)

    panels = [
        FieldPanel("title"),
        FieldPanel("description"),
        FieldPanel("url"),
    ]


class ErrorIndexPage(Page):
    intro = models.CharField(max_length=255, blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
    ]

    parent_page_types = ["home.HomePage"]
    subpage_types = ["home.ErrorCategoryPage"]
    max_count = 1

    def get_context(self, request):
        context = super().get_context(request)
        context["categories"] = (
            self.get_children()
            .type(ErrorCategoryPage)  # type: ignore[attr-defined]
            .live()
            .public()
            .specific()
        )
        return context


class ErrorCategoryPage(Page):
    intro = models.CharField(max_length=255, blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
    ]

    parent_page_types = ["home.ErrorIndexPage"]
    subpage_types = ["home.ErrorReportPage"]

    def get_context(self, request):
        context = super().get_context(request)
        context["entries"] = (
            self.get_children()
            .type(ErrorReportPage)  # type: ignore[attr-defined]
            .live()
            .public()
            .specific()
            .order_by("-first_published_at")
        )
        return context


class ErrorReportPage(Page):
    description = models.CharField(
        max_length=255,
        blank=True,
        help_text="Rezumat scurt al situatiei/erorii.",
    )
    body = StreamField(STREAM_BODY_BLOCKS, blank=True, use_json_field=True)

    content_panels = Page.content_panels + [
        FieldPanel("description"),
        FieldPanel("body"),
    ]

    search_fields = Page.search_fields + [
        index.SearchField("description"),
        index.SearchField("body"),
    ]

    parent_page_types = ["home.ErrorCategoryPage"]
    subpage_types = []


class FAQIndexPage(Page):
    intro = models.CharField(max_length=255, blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
    ]

    parent_page_types = ["home.HomePage"]
    subpage_types = ["home.FAQCategoryPage"]
    max_count = 1

    def get_context(self, request):
        context = super().get_context(request)
        context["categories"] = (
            self.get_children()
            .type(FAQCategoryPage)  # type: ignore[attr-defined]
            .live()
            .public()
            .specific()
        )
        return context


class FAQCategoryPage(Page):
    intro = models.CharField(max_length=255, blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
    ]

    parent_page_types = ["home.FAQIndexPage"]
    subpage_types = ["home.FAQEntryPage"]

    def get_context(self, request):
        context = super().get_context(request)
        context["entries"] = (
            self.get_children()
            .type(FAQEntryPage)  # type: ignore[attr-defined]
            .live()
            .public()
            .specific()
            .order_by("faqentrypage__is_answered", "-first_published_at")
        )
        return context


class FAQEntryPage(Page):
    body = StreamField(STREAM_BODY_BLOCKS, blank=True, use_json_field=True)
    is_answered = models.BooleanField(
        default=False,
        verbose_name="Raspuns oferit",
        help_text="Bifeaza cand intrebarea a primit un raspuns clar.",
    )

    content_panels = Page.content_panels + [
        FieldPanel("body"),
        FieldPanel("is_answered"),
    ]

    search_fields = Page.search_fields + [
        index.SearchField("body"),
    ]

    parent_page_types = ["home.FAQCategoryPage"]
    subpage_types = []


class PersonalSpaceIndexPage(Page):
    """
    Container ascuns pentru spatiile personale ale userilor - nu apare in
    meniul principal (filtrat explicit in context_processors.main_menu).
    """

    parent_page_types = ["home.HomePage"]
    subpage_types = ["home.PersonalSpacePage"]
    max_count = 1

    def serve(self, request, *args, **kwargs):
        # Nu are template propriu - nu e gandita sa fie vizitata direct (doar
        # container pentru paginile individuale). Daca cineva ajunge totusi
        # aici (ex. "View live" din admin), redirectioneaza spre spatiul
        # personal al userului curent, la fel ca /spatiul-meu/.
        page = PersonalSpacePage.get_or_create_for_user(request.user)
        return redirect(page.url)


class PersonalSpacePage(RoutablePageMixin, Page):
    owner_user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="personal_space_page",
    )

    content_panels = Page.content_panels + [
        InlinePanel(
            "sections",
            label="Sectiuni",
            classname="collapsible collapsed",
        ),
    ]

    parent_page_types = ["home.PersonalSpaceIndexPage"]
    subpage_types = []

    # Nu se creeaza manual din admin ("Add child page") - owner_user nu e in
    # formular, deci ar crapa la salvare oricum. Se creeaza automat, o
    # singura data per user, prin PersonalSpacePage.get_or_create_for_user()
    # (apelata din ruta /spatiul-meu/). Asta nu blocheaza editarea/publicarea
    # paginii deja create, doar ascunde butonul de adaugare manuala.
    is_creatable = False

    def get_context(self, request):
        # Hook-urile din wagtail_hooks.py izoleaza doar admin-ul (listare +
        # editare) - randarea publica a paginii (aici) nu era acoperita, deci
        # oricine logat putea citi spatiul altcuiva doar stiind/ghicind URL-ul
        # (slug-ul e previzibil: spatiul-personal-<id>). Verificare directa
        # aici, in loc de nativ Wagtail "Privacy", pentru ca restrictia
        # trebuie sa fie "doar proprietarul", nu un grup fix.
        if request.user != self.owner_user and not request.user.is_superuser:
            raise Http404

        context = super().get_context(request)
        context["sections"] = self.sections.all()
        return context

    @route(r"^$")
    def page_view(self, request):
        return Page.serve(self, request)

    @route(r"^sectiune/(?P<section_id>\d+)/$")
    def section_view(self, request, section_id):
        try:
            section = self.sections.get(id=section_id)
        except PersonalSpaceSection.DoesNotExist as error:
            raise Http404 from error

        context = self.get_context(request)
        context["section"] = section
        return render(request, "home/personal_space_section.html", context)

    @classmethod
    def get_or_create_for_user(cls, user):
        try:
            return cls.objects.get(owner_user=user)
        except cls.DoesNotExist:
            pass

        index_page = PersonalSpaceIndexPage.objects.first()
        if index_page is None:
            home_page = HomePage.objects.first()
            index_page = PersonalSpaceIndexPage(
                title="Spatii personale", slug="spatii-personale", show_in_menus=False
            )
            home_page.add_child(instance=index_page)
            index_page.save_revision().publish()

        display_name = user.get_full_name() or user.username
        page = cls(
            title=f"Spatiul personal - {display_name}",
            slug=f"spatiul-personal-{user.pk}",
            owner_user=user,
            show_in_menus=False,
        )
        index_page.add_child(instance=page)
        page.save_revision().publish()
        return page


class PersonalSpaceSection(Orderable):
    page = ParentalKey(
        "home.PersonalSpacePage",
        on_delete=models.CASCADE,
        related_name="sections",
    )

    title = models.CharField(max_length=255)
    description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    body = StreamField(STREAM_BODY_BLOCKS, blank=True, use_json_field=True)

    panels = [
        FieldPanel("title"),
        FieldPanel("description"),
        FieldPanel("body"),
    ]

    @property
    def url(self):
        return f"{self.page.url}sectiune/{self.pk}/"
