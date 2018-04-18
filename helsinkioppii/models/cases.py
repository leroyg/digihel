from django.conf import settings
from django.db import models
from django.forms import model_to_dict
from django.http import HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import render, redirect
from django.utils.translation import ugettext_lazy as _
from modelcluster.contrib.taggit import ClusterTaggableManager
from modelcluster.fields import ParentalKey, ParentalManyToManyField
from taggit.models import TaggedItemBase
from wagtail.contrib.wagtailroutablepage.models import RoutablePageMixin, route
from wagtail.wagtailadmin.edit_handlers import RichTextFieldPanel, FieldPanel, InlinePanel, MultiFieldPanel
from wagtail.wagtailcore.fields import RichTextField
from wagtail.wagtailcore.models import Page, Orderable
from wagtail.wagtaildocs.models import Document
from wagtail.wagtailimages.edit_handlers import ImageChooserPanel
from wagtail.wagtailimages.models import Image
from wagtail.wagtailsnippets.models import register_snippet

from helsinkioppii.utils import get_substrings, humanized_range
from multilang.utils import get_requested_page_language_code


class CaseKeyword(TaggedItemBase):
    content_object = ParentalKey('helsinkioppii.Case', related_name='cases')


@register_snippet
class SchoolSubject(models.Model):
    subject = models.CharField(
        verbose_name=_('School subject'),
        max_length=128,
        blank=True
    )
    language_code = models.CharField(
        verbose_name=_('language code'),
        max_length=10,
        blank=False,
        choices=settings.LANGUAGES,
    )

    class Meta:
        ordering = ['pk']

    def __str__(self):
        """
        Returns textual representation of the subject.

        :return: Name of the subject.
        :rtype: str
        """
        return self.subject


@register_snippet
class SchoolGrade(models.Model):
    grade = models.CharField(
        verbose_name=_('Level of education'),
        max_length=128,
        blank=True
    )
    language_code = models.CharField(
        verbose_name=_('language code'),
        max_length=10,
        blank=False,
        choices = settings.LANGUAGES,
    )

    class Meta:
        ordering = ['pk']

    def __str__(self):
        """
        Returns textual representation of the grade.

        :return: Name of the subject.
        :rtype: str
        """
        return self.grade


@register_snippet
class CaseTheme(models.Model):
    theme = models.CharField(
        verbose_name=_('Theme'),
        max_length=128,
        blank=True
    )
    language_code = models.CharField(
        verbose_name=_('language code'),
        max_length=10,
        blank=False,
        choices=settings.LANGUAGES,
    )

    class Meta:
        ordering = ['pk']

    def __str__(self):
        """
        Returns textual representation of the theme.

        :return: Name of the theme.
        :rtype: str
        """
        return self.theme


class CaseContact(Orderable):
    case = ParentalKey('helsinkioppii.Case', related_name='contacts')
    person = models.ForeignKey('people.Person', related_name='cases')

    def __str__(self):
        return '{person} as the contact of case {case}'.format(
            person=self.person,
            case=self.case
        )


@register_snippet
class CaseGalleryImage(models.Model):
    image = models.ForeignKey(
        'wagtailimages.Image',
        verbose_name=_('Image'),
        null=False,
        blank=False,
        on_delete=models.CASCADE,
        related_name='+'
    )
    slot = models.PositiveSmallIntegerField(
        verbose_name=_('Gallery image ordinal'),
        null=False,
        blank=False,
        help_text=_('One of the eight gallery image slots the images takes up from a Case.')
    )
    case = models.ForeignKey(
        'helsinkioppii.Case',
        verbose_name=_('Case'),
        blank=False,
        null=False,
        on_delete=models.CASCADE,
        related_name='gallery_images',
    )

    class Meta:
        ordering = ['slot']

    def __str__(self):
        return 'Gallery image in slot {slot} for case {case}'.format(
            slot=self.slot,
            case=self.case
        )


@register_snippet
class CaseAttachment(models.Model):
    file = models.ForeignKey(
        'wagtaildocs.Document',
        verbose_name=_('File'),
        null=False,
        blank=False,
        on_delete=models.CASCADE,
        related_name='+'
    )
    slot = models.PositiveSmallIntegerField(
        verbose_name=_('Attachment ordinal'),
        null=False,
        blank=False,
        help_text=_('One of the five document slots the attachment takes up from a Case.')
    )
    case = models.ForeignKey(
        'helsinkioppii.Case',
        verbose_name=_('Case'),
        blank=False,
        null=False,
        on_delete=models.CASCADE,
        related_name='attachments',
    )

    class Meta:
        ordering = ['slot']

    def __str__(self):
        return 'Attachment in slot {slot} for case {case}'.format(
            slot=self.slot,
            case=self.case
        )


@register_snippet
class CaseSidebarLink(models.Model):
    url = models.URLField(
        verbose_name=_('Link URL'),
        blank=False,
        null=False,
        max_length=512,
    )
    text = models.CharField(
        verbose_name=_('Link text'),
        blank=False,
        null=False,
        max_length=256,
    )
    slot = models.PositiveSmallIntegerField(
        verbose_name=_('Link ordinal'),
        null=False,
        blank=False,
        help_text=_('One of the five link slots the link takes up from a Case.')
    )
    case = models.ForeignKey(
        'helsinkioppii.Case',
        verbose_name=_('Case'),
        blank=False,
        null=False,
        on_delete=models.CASCADE,
        related_name='sidebar_links',
    )

    class Meta:
        ordering = ['slot']

    def __str__(self):
        return 'Sidebar link in slot {slot} for case {case}'.format(
            slot=self.slot,
            case=self.case
        )


class Case(RoutablePageMixin, Page):
    template = 'helsinkioppii/case.html'

    image = models.ForeignKey(
        'wagtailimages.Image',
        verbose_name=_('image'),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )

    abstract = models.TextField(verbose_name=_('abstract'))

    # Leave this now for legacy. Not shown or used in admin ui
    content = RichTextField(verbose_name=_('content'), blank=True)

    # Content field split in sections to guide consistent formatting
    content_objectives = RichTextField(verbose_name=_('Objectives'), blank=True)
    content_what = RichTextField(verbose_name=_('What was done'), blank=True)
    content_how = RichTextField(verbose_name=_('How it was done'), blank=True)
    content_who = RichTextField(verbose_name=_('Participants'), blank=True)
    content_evaluation = RichTextField(verbose_name=_('Evaluation'), blank=True)
    content_materials = RichTextField(verbose_name=_('Materials'), blank=True)
    content_pros = RichTextField(verbose_name=_('Pros'), blank=True)
    content_cons = RichTextField(verbose_name=_('Cons'), blank=True)

    # Sidebar content
    school = models.CharField(
        verbose_name=_('Educational institution'),
        max_length=128,
        blank=True,
    )
    themes = ParentalManyToManyField(
        'helsinkioppii.CaseTheme',
        verbose_name=_('Themes'),
        blank=True,
        related_name="+"
    )
    keywords = ClusterTaggableManager(through=CaseKeyword, blank=True)
    grades = ParentalManyToManyField(
        'helsinkioppii.SchoolGrade',
        verbose_name=_('Levels of education'),
        blank=True,
        related_name="+"
    )
    subjects = ParentalManyToManyField(
        'helsinkioppii.SchoolSubject',
        verbose_name=_('School subjects'),
        blank=True,
        related_name="+"
    )

    # Deprecated foreign key relationships
    # TODO: Remove after a month or two (around April/May 2018). Check
    #       that `./ manage.py update_case_m2m_with_fk_values` has been
    #       ran in production before removing these fields.
    subject = models.ForeignKey(
        'helsinkioppii.SchoolSubject',
        verbose_name=_('School subject'),
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    grade = models.ForeignKey(
        'helsinkioppii.SchoolGrade',
        verbose_name=_('Level of education'),
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    theme = models.ForeignKey(
        'helsinkioppii.CaseTheme',
        verbose_name=_('Theme'),
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )

    # Legal
    cc_license = models.BooleanField(
        verbose_name=_('Creative Commons license'),
        default=False,
        help_text=_('I am licensing this content under Creative Commons license.')
    )
    photo_permission = models.BooleanField(
        verbose_name=_('Photo permission'),
        default=False,
        help_text=_(
            'I have the permission to publish the images associated to this case. I have the permission to use the '
            'images or I have the copyright to the images. People have given permission to publish the images they '
            'appear in.'
        )
    )

    # Meta
    draft = models.BooleanField(
        verbose_name=_('draft'),
        default=False,
        help_text=_('Hidden draft flag used with frontend editing.')
    )

    # Group separated content fields in admin ui
    case_content_panel = MultiFieldPanel(
        [
            RichTextFieldPanel('content_objectives'),
            RichTextFieldPanel('content_what'),
            RichTextFieldPanel('content_how'),
            RichTextFieldPanel('content_who'),
            RichTextFieldPanel('content_evaluation'),
            RichTextFieldPanel('content_materials'),
            RichTextFieldPanel('content_pros'),
            RichTextFieldPanel('content_cons'),
        ],
        heading=_('Case description'),
        classname="collapsible"
    )

    # Group meta fields in admin ui
    sidebar_content_panel = MultiFieldPanel(
        [
            FieldPanel('school'),
            FieldPanel('subjects', classname='col6'),
            FieldPanel('grades', classname='col6'),
            FieldPanel('themes', classname='col6'),
            FieldPanel('keywords'),
            InlinePanel('contacts', label=_('contacts')),
        ],
        heading=_('Case meta'),
        classname='collapsible collapsed'
    )

    deprecated_relations_panel = MultiFieldPanel(
        [
            FieldPanel('subject', classname='col4'),
            FieldPanel('grade', classname='col4'),
            FieldPanel('theme', classname='col4'),
        ],
        heading=_('Deprecated relationships'),
        classname='collapsible collapsed'
    )

    content_panels = Page.content_panels + [
        ImageChooserPanel('image'),
        FieldPanel('abstract', classname='full'),
        sidebar_content_panel,
        deprecated_relations_panel,
        case_content_panel,
        FieldPanel('draft')
    ]

    @classmethod
    def allowed_parent_page_models(cls):
        from helsinkioppii.models.pages import CaseListPage
        return [CaseListPage]

    @classmethod
    def allowed_subpage_models(cls):
        return []

    @classmethod
    def can_exist_under(cls, parent):
        from helsinkioppii.models.pages import CaseListPage
        return isinstance(parent, CaseListPage)

    def _is_user_action_allowed(self, user):
        """
        Check that current user has permission to access frontend management
        views for Case instance. Original creator (owner) of the Case and staff
        users have permissions.
        """
        return user == self.owner or user.is_staff

    def _get_relative_route_path(self, route):
        """
        Get a relative path of the Case instance and concatenate given route
        to the end of it.

        :param route: Route string.
        :return: Relative path for given route.
        """
        return '{page_url}{route}'.format(
            page_url=self.get_url(),
            route=route
        )

    @property
    def update_view_path(self):
        """
        Return relative path for referring the edit view of this page.
        """
        return self._get_relative_route_path('edit/')

    @property
    def publish_view_path(self):
        """
        Return relative path for referring the publish view of this page.
        """
        return self._get_relative_route_path('publish/')

    @property
    def unpublish_view_path(self):
        """
        Return relative path for referring the unpublish view of this page.
        """
        return self._get_relative_route_path('unpublish/')

    @property
    def delete_view_path(self):
        """
        Return relative path for referring the unpublish view of this page.
        """
        return self._get_relative_route_path('delete/')

    def assign_values_from_form_data(self, form):
        """
        Updates the relevant field values from form data.

        :param form: Validated CaseForm instance.
        """
        # Fields that can be assigned to object without special handling.
        simple_fields = [
            'title', 'school','themes', 'grades', 'subjects', 'abstract', 'content_objectives',
            'content_what', 'content_how', 'content_who', 'content_evaluation', 'content_materials',
            'content_pros', 'content_cons', 'cc_license', 'photo_permission',
        ]

        for field in simple_fields:
            setattr(self, field, form.cleaned_data[field])

        self.keywords.clear()  # Clear old keywords.

        if form.cleaned_data['image'] == False:  # Should be deleted
            self.image.delete()
        if form.cleaned_data['image']:
            image = Image.objects.create(
                file=form.cleaned_data['image'],
                title=form.cleaned_data['image_title']
            )
            self.image = image

        keywords = form.cleaned_data.get('keywords')
        if keywords:
            tag_model = CaseKeyword.tag_model()
            for keyword in get_substrings(keywords):
                keyword_instance, created = tag_model.objects.get_or_create(name=keyword)
                self.keywords.add(keyword_instance)

    def update_gallery_images_from_form_data(self, form):
        """
        Update gallery images from the data on the form.

        :param form:
        :return:
        """
        for image_slot in humanized_range(1, form.GALLERY_IMAGE_COUNT):
            image_field = 'gallery_image_%s' % image_slot
            title_field = 'gallery_image_title_%s' % image_slot
            image = form.cleaned_data.get(image_field)
            previous_image = CaseGalleryImage.objects.filter(slot=image_slot, case=self).first()
            if image == False:  # Delete checkbox is checked
                previous_image.delete()
            elif image:
                if previous_image:
                    previous_image.delete()
                image_object = Image.objects.create(
                    file=image,
                    title=form.cleaned_data[title_field]
                )
                CaseGalleryImage.objects.create(
                    image=image_object,
                    slot=image_slot,
                    case=self,
                )

    def update_attachments_from_form_data(self, form):
        """
        Update attachments from the data on the form.

        :param form:
        :return:
        """
        for document_slot in humanized_range(1, form.ATTACHMENT_COUNT):
            file_field = 'attachment_file_%s' % document_slot
            title_field = 'attachment_title_%s' % document_slot
            file = form.cleaned_data.get(file_field, None)
            previous_attachment = CaseAttachment.objects.filter(slot=document_slot, case=self).first()
            if file == False:  # Delete checkbox is checked
                previous_attachment.delete()
            elif file:
                if previous_attachment:
                    previous_attachment.delete()
                document_object = Document.objects.create(
                    file=file,
                    title=form.cleaned_data[title_field]
                )
                CaseAttachment.objects.create(
                    file=document_object,
                    slot=document_slot,
                    case=self,
                )

    def update_sidebar_links_from_form_data(self, form):
        """
        Update sidebar links from the data on the form.

        :param form:
        :return:
        """
        for link_slot in humanized_range(1, form.LINK_COUNT):
            url_field = 'link_url_%s' % link_slot
            text_field = 'link_text_%s' % link_slot
            delete_field = 'delete_link_%s' % link_slot
            url = form.cleaned_data.get(url_field, None)
            delete = form.cleaned_data.get(delete_field, False)
            previous_link = CaseSidebarLink.objects.filter(slot=link_slot, case=self).first()
            if delete:
                previous_link.delete()
            elif url:
                if previous_link:
                    link = previous_link
                else:
                    link = CaseSidebarLink(
                        slot=link_slot,
                        case=self
                    )
                link.url = url
                link.text = form.cleaned_data[text_field]
                link.save()

    def update_form_initial_values_with_related_model_data(self, initial_values):
        if self.image:
            initial_values['image'] = self.image.file
            initial_values['image_title'] = self.image.title

        for attachment in self.attachments.all():
            file_field = 'attachment_file_%s' % attachment.slot
            title_field = 'attachment_title_%s' % attachment.slot
            initial_values[file_field] = attachment.file.file
            initial_values[title_field] = attachment.file.title

        for gallery_image in self.gallery_images.all():
            image_field = 'gallery_image_%s' % gallery_image.slot
            title_field = 'gallery_image_title_%s' % gallery_image.slot
            initial_values[image_field] = gallery_image.image.file
            initial_values[title_field] = gallery_image.image.title

        for sidebar_link in self.sidebar_links.all():
            url_field = 'link_url_%s' % sidebar_link.slot
            text_field = 'link_text_%s' % sidebar_link.slot
            initial_values[url_field] = sidebar_link.url
            initial_values[text_field] = sidebar_link.text

    @route(r'^edit/$')
    def update_view(self, request):
        if not self._is_user_action_allowed(request.user):
            return HttpResponseForbidden()

        from helsinkioppii.forms import CaseForm

        language_code = get_requested_page_language_code(request)

        if request.method == 'GET':
            initial_values = model_to_dict(self)
            initial_values['keywords'] = str.join('; ', [kw.name for kw in self.keywords.all()])
            self.update_form_initial_values_with_related_model_data(initial_values)
            return render(request, 'helsinkioppii/edit_case.html', {
                'page': self,
                'draft': self.draft,
                'form_action_url': self.update_view_path,
                'form': CaseForm(initial=initial_values, language_code=language_code),
            })

        if request.method == 'POST':
            form = CaseForm(request.POST, request.FILES, language_code=language_code)
            if form.is_valid():
                self.assign_values_from_form_data(form)
                self.save()
                self.update_gallery_images_from_form_data(form)
                self.update_attachments_from_form_data(form)
                self.update_sidebar_links_from_form_data(form)
                return redirect(self.get_url())

            return render(request, 'helsinkioppii/edit_case.html', {
                'page': self,
                'draft': self.draft,
                'form_action_url': self.update_view_path,
                'form': form,
            })

        return HttpResponseBadRequest()

    @route(r'^publish/$')
    def publish_view(self, request):
        if not self._is_user_action_allowed(request.user):
            return HttpResponseForbidden()

        self.draft = False
        self.save()

        return redirect(self.get_url())

    @route(r'^unpublish/$')
    def unpublish_view(self, request):
        if not self._is_user_action_allowed(request.user):
            return HttpResponseForbidden()

        self.draft = True
        self.save()

        return redirect(self.get_url())

    @route(r'^delete/$')
    def delete_view(self, request):
        if not self._is_user_action_allowed(request.user):
            return HttpResponseForbidden()

        case_list_page = self.get_parent()

        self.draft = True  # Flag the Case as draft so it's not published immediately if recovered by admin.
        self.unpublish(commit=True)

        return redirect(case_list_page.get_url())
