# (c) 2014-2017 Digital Humanities Lab, Utrecht University
# Author: Julian Gonggrijp, j.gonggrijp@uu.nl

"""
    Model view classes for some of the tables in the database.
    
    Note that "views" here means something subtly different from the
    "views" in coloringbook/views.py. Please refer to the
    flask.ext.admin documentation for details.
"""

import os, os.path as op

from sqlalchemy.event import listens_for
from jinja2 import Markup
from wtforms import fields, validators
from flask import request, url_for, redirect, flash, json, current_app
from flask.ext.admin import expose, form
from flask.ext.admin.contrib.sqla import ModelView
import flask.ext.admin.contrib.sqla.filters as filters
from flask.ext.admin.helpers import validate_form_on_submit, get_redirect_target
from flask.ext.admin.form import FormOpts, rules
from flask.ext.admin.model.helpers import get_mdict_item_or_list
from flask.ext.admin.babel import gettext

from ..models import *

from .utilities import csvdownload
from .forms import Select2MultipleField, FileNameLength


class FillView(ModelView):
    """ Custom admin table view of Fill objects. """
    
    list_template = 'admin/fill_list.html'
    can_create = False
    can_edit = False
    can_delete = False
    column_list = 'survey page area subject time color'.split()
    column_sortable_list = (
        ('survey', 'survey.name'),
        ('page', 'page.name'),
        ('area', 'area.name'),
        ('subject', 'subject.id'),
        'time',
        ('color', 'color.code'),
    )
    column_filters = (
        'survey',
        'page',
        'area',
        filters.FilterEqual(Fill.subject_id, 'Subject / ID'),
        filters.FilterNotEqual(Fill.subject_id, 'Subject / ID'),
        'subject',
    )
#    column_default_sort = 'survey'  # doesn't work for some reason
    page_size = 100
    column_display_all_relations = True
    
    def __init__(self, session, **kwargs):
        super(FillView, self).__init__(Fill, session, name='Data', **kwargs)
    
    @expose('/csv/raw')
    @csvdownload
    def export_raw(self):
        """ Render a CSV, similar in operation to BaseModelView.index_view. """
        
        query = (
            self.session.query(
                Survey.name,
                Page.name,
                Area.name,
                Subject.id,
                Fill.time,
                Color.name )
            .select_from(Fill)
            .join(Fill.survey, Fill.page, Fill.area, Fill.subject, Fill.color)
        )
        return query, self.column_list, 'filldata_raw'
    
    @expose('/csv/final')
    @csvdownload
    def export_final(self):
        """ Render a CSV with only the final color of each area. """
        color_bis = db.aliased(Color)
        subquery = self.get_core_query()
        query = (
            self.session.query(
                Survey.name,
                Page.name,
                Area.name,
                Subject.id,
                subquery.c.time,
                subquery.c.clicks,
                Color.name,
                color_bis.name,
                Expectation.here,
                db.case(
                    [
                        (
                            Color.id == Expectation.color_id,
                            db.case(
                                [(Expectation.here, 'expected')],
                                else_='misplaced' ),
                        ),
                        (Expectation.here == True, 'miscolored'),
                        (Expectation.here == False, 'compatible')
                    ],
                    else_ = 'unspecified' ) )  # Expectation.here == None
            .select_from(subquery)
            .outerjoin(Expectation, db.and_(
                subquery.c.page_id == Expectation.page_id,
                subquery.c.area_id == Expectation.area_id ))
            .join(Fill, db.and_(
                subquery.c.survey_id == Fill.survey_id,
                subquery.c.page_id == Fill.page_id,
                subquery.c.area_id == Fill.area_id,
                subquery.c.subject_id == Fill.subject_id,
                subquery.c.time == Fill.time ))
            .join(Fill.survey, Fill.page, Fill.area, Fill.subject, Fill.color)
            .outerjoin(color_bis, color_bis.id == Expectation.color_id)
        )
        headers = [ 'survey', 'page', 'area', 'subject', 'time', 'clicks',
                    'color', 'expected', 'here', 'category',
                    ]
        return query, headers, 'filldata_final'
    
    @expose('/csv/comparison')
    @csvdownload
    def export_comparison(self):
        """ Render a CSV with expected colors compared to actual final data. """
        color_bis = db.aliased(Color)
        subquery = self.get_core_query()
        query = (
            self.session.query(
                Survey.name,
                Page.name,
                Area.name,
                Subject.id,
                subquery.c.time,
                subquery.c.clicks,
                color_bis.name,
                Expectation.here,
                Color.name,
                db.case(
                    [
                        (
                            Color.id == Expectation.color_id,
                            db.case(
                                [(Expectation.here, 'expected')],
                                else_='misplaced' ),
                        ),
                        (
                            Color.id == None,
                            db.case(
                                [(Expectation.here, 'not_expected')],
                                else_='empty' ),
                        ),
                        (Expectation.here, 'miscolored'),
                    ],
                    else_='compatible' ) )
            .select_from(Expectation)
            .join(color_bis, color_bis.id == Expectation.color_id)
            .join(Expectation.page, Expectation.area)
            .outerjoin(subquery, db.and_(
                subquery.c.page_id == Expectation.page_id,
                subquery.c.area_id == Expectation.area_id ))
            .outerjoin(Fill, db.and_(
                subquery.c.survey_id == Fill.survey_id,
                subquery.c.page_id == Fill.page_id,
                subquery.c.area_id == Fill.area_id,
                subquery.c.subject_id == Fill.subject_id,
                subquery.c.time == Fill.time ))
            .outerjoin(
                Fill.survey,
                Fill.subject,
                Fill.color )
        )
        headers = [ 'survey', 'page', 'area', 'subject', 'time', 'clicks',
                    'expected', 'here', 'color', 'category',
                    ]
        return query, headers, 'filldata_comparison'
    
    def get_core_query(self):
        return (
            self.session.query(
                Fill.survey_id.label('survey_id'),
                Fill.page_id.label('page_id'),
                Fill.area_id.label('area_id'),
                Fill.subject_id.label('subject_id'),
                db.func.max(Fill.time).label('time'),
                db.func.count().label('clicks') )
            .group_by(
                Fill.survey_id,
                Fill.page_id,
                Fill.area_id,
                Fill.subject_id )
            .subquery('sub')
        )


class SubjectView (ModelView):
    """ Custom admin table view of Subject data. """
    can_edit = False
    can_create = False
    list_template = 'admin/subject_list.html'
    column_display_pk = True
    column_auto_select_related = True
    column_labels = {'id': 'ID'}
    column_filters = (
        filters.FilterEqual(Subject.id, 'ID'),
        filters.FilterNotEqual(Subject.id, 'ID'),
        'name',
        'birth',
        'eyesight',
    )
    page_size = 100
    
    def __init__(self, session, **kwargs):
        super(SubjectView, self).__init__(Subject, session, name='Subjects', **kwargs)
    
    @expose('/csv/subjects')
    @csvdownload
    def export_subjects(self):
        """ Export personals, language summary and survey evaluation. """
        
        language_primary = db.aliased(SubjectLanguage)
        query = (
            self.session.query(
                Subject.id,
                Subject.name,
                Subject.numeral,
                Subject.birth,
                Subject.eyesight,
                db.func.count(SubjectLanguage.language_id),
                db.func.concat(Language.name, ','),
                Survey.name,
                SurveySubject.difficulty,
                SurveySubject.topic,
                SurveySubject.comments )
            .select_from(SurveySubject)
            .join(SurveySubject.subject)
            .join(SurveySubject.survey)
            .join(Subject.subject_languages)
            .group_by(Subject.id, Survey.id)
            .join(language_primary, Subject.id == language_primary.subject_id)
            .filter(language_primary.level == 10)
            .join(language_primary.language)
            .group_by(Subject.id, Survey.id)
        )
        headers = (
            'id', 'name', 'numeral', 'birth', 'eyesight',
            '#lang', 'nativelang', 'survey', 'difficulty', 'topic', 'comments',
        )
        return query, headers, 'subjectdata'
    
    @expose('/csv/languages')
    @csvdownload
    def export_languages(self):
        """ Export complete language data from the database. """
        query = (
            self.session.query(
                SubjectLanguage.subject_id,
                Language.name,
                SubjectLanguage.level )
            .select_from(SubjectLanguage)
            .join(SubjectLanguage.language)
        )
        headers = 'id language level'.split()
        return query, headers, 'subject-languagedata'


class SurveyView (ModelView):
    """ Custom admin table view of Survey objects. """
    
    edit_template = 'admin/augmented_edit.html'
    create_template = 'admin/augmented_create.html'
    column_list = ('name', 'language', 'begin', 'end', 'duration', 'simultaneous', 'information')
    column_descriptions = {
        'begin': 'First date of availability (immediate if empty)',
        'end': 'Last date of availability (forever if empty)',
        'duration': 'Duration of sentence display in milliseconds before the drawing is shown (1000 ms = 1 s)',
        'simultaneous': 'Whether the sentence is presented at the same time as the drawing',
    }
    column_sortable_list = (
        ('name', 'survey.name'),
        ('language', 'language.name'),
        'begin',
        'end',
        'simultaneous',
    )
    column_auto_select_related = True
    column_searchable_list = ('information',)
    column_default_sort = ('begin', True)
    column_display_all_relations = True
    form_columns = (
        'name', 'title', 'language', 'begin', 'end', 'duration',
        'simultaneous', 'information', 'page_list',
        'welcome_text', 'starting_form', 'privacy_text', 'instruction_text',
        'ending_form', 'success_text', 'button_set',
    )
    form_extra_fields = {
        'page_list': Select2MultipleField('Pages', coerce=int),
    }
    form_args = {
        'duration': {
            'validators': [validators.NumberRange(min=0, max=60000)],
        },
    }
    column_descriptions = {
        'name': 'Used for your reference and for generating the survey URL.',
        'title': 'Shown on the first page of the survey and in the window title.',
    }
    
    def create_form(self, obj=None):
        form = super(SurveyView, self).create_form(obj)
        form.page_list.choices = db.session.query(Page.id, Page.name).order_by(Page.name).all()
        return form
    
    def edit_form(self, obj=None):
        form = super(SurveyView, self).edit_form(obj)
        form.page_list.choices = db.session.query(Page.id, Page.name).order_by(Page.name).all()
        return form
    
    def on_model_change(self, form, model, is_created=False):
        if not is_created:
            self.session.query(SurveyPage).filter_by(survey=model).delete()
        for index, id in enumerate(form.page_list.data):
            SurveyPage(survey=model, page_id=id, ordering=index)
    
    def on_form_prefill(self, form, id):
        form.page_list.process_data(
            self.session.query(SurveyPage.page_id)
            .filter(SurveyPage.survey_id == id)
            .order_by(SurveyPage.ordering)
            .all()
        )
    
    def __init__(self, session, **kwargs):
        super(SurveyView, self).__init__(Survey, session, name='Surveys', **kwargs)


class PageView(ModelView):
    """
        Custom admin table view of Page objects with associated Expectations.
    """
    
    edit_template = 'admin/augmented_edit.html'
    column_list = 'name drawing language text sound'.split()
    column_sortable_list = (
        'name',
        ('drawing', 'drawing.name'),
        ('language', 'language.name'),
        ('sound', 'sound.name'),
    )
    column_auto_select_related = True
    column_searchable_list = ('name', 'text',)
    column_default_sort = 'name'
    column_display_all_relations = True
    form_columns = 'name drawing language text sound expect_list fname'.split()
    form_overrides = {
        'text': fields.TextAreaField,
    }
    form_extra_fields = {
        'expect_list': fields.HiddenField(),
        'fname': fields.HiddenField(),
    }
    form_create_rules = form_columns[:5]  # up to sound
    form_edit_rules = (
        'name',
        rules.Container('forms.hide', rules.Field('drawing')),
        'language',
        'text',
        'sound',
        rules.Container('forms.hide', rules.Field('fname')),
        rules.Container('forms.hide', rules.Field('expect_list')),
        rules.Macro('drawing.edit_expectations'),
    )
    
    def on_model_change(self, form, model, is_created=False):
        if not is_created:
            Expectation.query.filter_by(page=model).delete()
            new_expectations = json.loads(form.expect_list.data)
            for area_name, settings in new_expectations.iteritems():
                color = Color.query.filter_by(code=settings['color']).one()
                area = (
                    Area.query
                    .filter_by(name=area_name, drawing=model.drawing)
                    .one()
                )
                model.expectations.append(Expectation(
                    area=area,
                    color=color,
                    here=settings['here'] ))
    
    def on_form_prefill(self, form, id):
        form.fname.process_data(
            self.session.query(Drawing.name)
            .join(Drawing.pages)
            .filter(Page.id == id)
            .one()[0]
        )
        form.expect_list.process_data(json.dumps(
            {
                area_name: {'color': color_code, 'here': expt.here}
                for expt, area_name, color_code in (
                    self.session.query(Expectation, Area.name, Color.code)
                    .join(Expectation.area)
                    .join(Expectation.color)
                    .filter(Expectation.page_id == id)
                    .all()
                )
            } ))
    
    def __init__(self, session, **kwargs):
        super(PageView, self).__init__(Page, session, name='Pages', **kwargs)


class DrawingView(ModelView):
    """ Custom admin table view of Drawing objects with associated Areas. """
    
    edit_template = 'admin/augmented_edit.html'
    form_columns = ('file', 'area_list', 'svg_source')
    form_extra_fields = {
        'file': form.FileUploadField(
            'Drawing',
            validators=(FileNameLength(
                max=54, 
                message='File name cannot be longer than %(max)d characters (extension included).'
            ),),
            base_path=current_app.instance_path,
            allowed_extensions=('svg',) ),
        'area_list': fields.HiddenField(),
        'svg_source': fields.HiddenField(),
    }
    form_create_rules = ('file',)
    form_edit_rules = (
        rules.Container('forms.hide', rules.Field('area_list')),
        rules.Container('forms.hide', rules.Field('svg_source')),
        rules.Macro('drawing.edit_areas'),
    )
        
    def on_model_change(self, form, model, is_created=False):
        if is_created:
            model.name = op.splitext(form.file.data.filename)[0]
        else:
            new_area_set = set(form.area_list.data.split(','))
            old_area_set = set(x[0] for x in
                self.session.query(Area.name)
                .filter_by(drawing = model)
                .all()
            )
            removed_areas = old_area_set - new_area_set
            for area in removed_areas:
                Area.query.filter_by(drawing=model, name=area).delete()
            added_areas = new_area_set - old_area_set
            for area in added_areas:
                model.areas.append(Area(name=area))
            current_app.open_instance_resource(model.name + '.svg', 'w').write(
                form.svg_source.data )
    
    def on_form_prefill(self, form, id):
        form.svg_source.process_data(
            current_app.open_instance_resource(
                self.session.query(Drawing.name).filter_by(id=id).scalar()
                + '.svg'
            ).read()
        )
        form.area_list.process_data(','.join(x[0] for x in
            self.session.query(Area.name)
            .filter_by(drawing_id=id)
            .all()
        ))
    
    def __init__(self, session, **kwargs):
        super(DrawingView, self).__init__(Drawing, session, name='Drawings', **kwargs)


@listens_for(Drawing, 'after_delete')
def delete_drawing(mapper, connection, target):
    # Delete image
    try:
        os.remove(op.join(current_app.instance_path, target.name + '.svg'))
    except OSError:
        # Don't care if it was not deleted because it does not exist
        pass


class SoundView(ModelView):
    """ Custom admin table view of Drawing objects with associated Areas. """
    
    can_edit = False
    form_columns = ('file',)
    form_extra_fields = {
        'file': form.FileUploadField(
            'Sound',
            validators=(FileNameLength(
                max=54, 
                message='File name cannot be longer than %(max)d characters (extension included).'
            ),),
            base_path=current_app.instance_path,
            allowed_extensions=('mp3',) ),
    }
    
    def on_model_change(self, form, model, is_created=False):
        if is_created:
            model.name = op.splitext(form.file.data.filename)[0]
        
    def __init__(self, session, **kwargs):
        super(SoundView, self).__init__(Sound, session, name='Sounds', **kwargs)


@listens_for(Sound, 'after_delete')
def delete_sound(mapper, connection, target):
    # Delete image
    try:
        os.remove(op.join(current_app.instance_path, target.name + '.mp3'))
    except OSError:
        # Don't care if it was not deleted because it does not exist
        pass


class TextView(ModelView):
    """ Management view for customizable text models. """
    
    column_descriptions = {
        'content': 'Parsed as HTML. Use &lt;br> for line breaks.',
    }
    form_widget_args = {
        'content': {
            'rows': 15,
            'cols': 70,
            'style': 'width: 70ex;',
        },
    }
    
    def __init__(self, model, session, **kwargs):
        super(TextView, self).__init__(model, session, category='Texts', **kwargs)


class StartingFormView(ModelView):
    """ Management view for customization of the starting form. """
    
    column_list = ('name', 'name_label', 'numeral_label', 'birth_label', 'eyesight_label', 'language_label')
    column_labels = {
        'language_label': 'First Language Label',
        'language_label_2': 'Add Languages Label',
    }
    column_descriptions = {
        'name': 'For your reference (not shown to subjects).',
        'name_label': 'Label for the form field shown to subjects.',
        'numeral_label': 'You can omit the form field entirely by leaving this empty.',
        'eyesight_label_2': 'Optional longer clarification for the eyesight field that will be put below the input. You may use HTML, e.g. &lt;br> for line breaks.',
        'language_label_2': 'Optional text to ask for second languages. If omitted, subjects will not get the option to specify more languages. If specified, you must also specify the Extra Language Label and the Extra Language Level Label. You may use HTML.',
        'extra_language_level_label': 'Label for the form field where subjects can enter their level of skill for a second language. The form field requires that they enter a value between 1 and 10, inclusive.'
    }
    
    def validate_form(self, form):
        """ Add a check that all extra language fields have the same status. """
        if form.language_label_2.data:
            if not form.extra_language_label.data or not form.extra_language_level_label:
                flash('If you set the Add Languages Label, you must also set the Extra Language Label and the Extra Language Level Label.', 'error')
                return False
        return super(StartingFormView, self).validate_form(form)
    
    def __init__(self, session, **kwargs):
        super(StartingFormView, self).__init__(
            StartingForm,
            session,
            name='Starting Form',
            category='Texts',
            **kwargs
        )


class EndingFormView(ModelView):
    """ Management view for customization of the ending form. """
    
    column_list = 'name difficulty_label topic_label comments_label'.split()
    form_columns = (
        'name',
        'introduction',
        'difficulty_label',
        'topic_label',
        'comments_label',
    )
    column_descriptions = {
        'name': 'For your reference (not shown to subjects).',
        'introduction': 'Shown at the top of the evaluation form.',
        'difficulty_label': 'Perceived difficulty of the task on a scale from 1 to 10, where 10 is most difficult.',
        'topic_label': 'What the subject thought the task was about.',
        'comments_label': 'Any comments or suggestions.',
    }
    
    def __init__(self, session, **kwargs):
        super(EndingFormView, self).__init__(
            EndingForm,
            session,
            name='Ending Form',
            category='Texts',
            **kwargs
        )


class ButtonSetView(ModelView):
    """ Management view for customization of the button values. """
    
    column_descriptions = {
        'name': 'For your reference.',
        'post_instruction_button': 'This text appears in the button to confirm the instruction.',
        'post_page_button': 'This text appears in the button to finish a page.',
        'page_back_button': 'To undo a premature press on the post page button. Leave this empty to disable the back button.',
        'post_survey_button': 'This text appears in the button to restart the survey with a new test subject.',
    }
    form_widget_args = {
        'page_back_button': {
            'placeholder': '(empty, disabled)',
        },
    }
    
    def __init__(self, session, **kwargs):
        super(ButtonSetView, self).__init__(
            ButtonSet,
            session,
            name='Button Set',
            category='Texts',
            **kwargs
        )


class ColorView(ModelView):
    """ Lookup table of colors with associated codes. """
    can_edit = False
    can_create = False
    can_delete = False
    column_list = ('name', 'code')
    def __init__ (self, session, **kwargs):
        super(ColorView, self).__init__(Color, session, name='Colors', **kwargs)


class LanguageView(ModelView):
    """ Lookup table of languages that allows edits and additions. """
    can_delete = False  # necessary because this may cause information loss
    def __init__ (self, session, **kwargs):
        super(LanguageView, self).__init__(Language, session, name='Languages', **kwargs)
