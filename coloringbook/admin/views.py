# (c) 2014 Digital Humanities Lab, Faculty of Humanities, Utrecht University
# Author: Julian Gonggrijp, j.gonggrijp@uu.nl

"""
    Model view classes for some of the tables in the database.
    
    Note that "views" here means something subtly different from the
    "views" in coloringbook/views.py. Please refer to the
    flask.ext.admin documentation for details.
"""

import os, os.path as op, StringIO, csv, datetime as dt

from sqlalchemy.event import listens_for
from jinja2 import Markup
from wtforms import fields
from flask import request, url_for, redirect, flash, json
from flask.ext.admin import expose, form
from flask.ext.admin.contrib import sqla
from flask.ext.admin.helpers import validate_form_on_submit, get_redirect_target
from flask.ext.admin.form import FormOpts, rules
from flask.ext.admin.model.helpers import get_mdict_item_or_list
from flask.ext.admin.babel import gettext

from ..models import *

from .utilities import csvdownload
from .forms import Select2MultipleField

__all__ = [
    'FillView',
    'SurveyView',
    'PageView',
    'DrawingView',
    'SoundView'     ]

file_path = op.join(op.dirname(__file__), '..', 'static')

class ModelView (sqla.ModelView):
    """
        Shallow subclass that provides the on_form_prefill hook.

        This hook attachment code has been submitted as a patch for
        flask.ext.admin.model.base.BaseModelView to Flask-Admin and
        was accepted. When the patched version finds its way to the
        next release version of Flask-Admin, this class becomes
        obsolete and we can switch back to directly using
        sqla.Modelview.
    """
    
    @expose('/edit/', methods=('GET', 'POST'))
    def edit_view(self):
        """
            Edit model view
        """
        return_url = get_redirect_target() or url_for('.index_view')

        if not self.can_edit:
            return redirect(return_url)

        id = get_mdict_item_or_list(request.args, 'id')
        if id is None:
            return redirect(return_url)

        model = self.get_one(id)

        if model is None:
            return redirect(return_url)

        form = self.edit_form(obj=model)

        if validate_form_on_submit(form):
            if self.update_model(form, model):
                if '_continue_editing' in request.form:
                    flash(gettext('Model was successfully saved.'))
                    return redirect(request.url)
                else:
                    return redirect(return_url)
        
        if request.method == 'GET':
            self.on_form_prefill(form, id)
        
        form_opts = FormOpts(widget_args=self.form_widget_args,
                             form_rules=self._form_edit_rules)

        return self.render(self.edit_template,
                           model=model,
                           form=form,
                           form_opts=form_opts,
                           return_url=return_url)
    
    def on_form_prefill (self, form, id):
        """ Perform additional actions to pre-fill the edit form.
        
        You only need to override this if you have added custom fields
        that depend on the database contents in a way that Flask-admin
        can't figure out by itself. Fields that were added by name of
        a normal column or relationship should work out of the box. """
        pass

class FillView (ModelView):
    """ Custom admin table view of Fill objects. """
    
    list_template = 'admin/augmented_list.html'
    can_create = False
    can_edit = False
    can_delete = False
    column_list = 'survey page area subject time color'.split()
    column_sortable_list = (
        ('survey', Survey.name),
        ('page', Page.name),
        ('area', Area.name),
        ('subject', Subject.id),
        'time',
        ('color', Color.code),
    )
    column_filters = column_list[:4]
#    column_default_sort = 'survey'  # doesn't work for some reason
    page_size = 100
    column_display_all_relations = True
    
    def __init__ (self, session, **kwargs):
        super(FillView, self).__init__(Fill, session, name='Data', **kwargs)
    
    @expose('/csv/raw')
    @csvdownload
    def export_raw (self):
        """ Render a CSV, similar in operation to BaseModelView.index_view. """
        
        query = (
            self.session.query(
                Survey.name,
                Page.name,
                Area.name,
                Subject.id,
                Fill.time,
                Color.code )
            .select_from(Fill)
            .join(Fill.survey, Fill.page, Fill.area, Fill.subject, Fill.color)
        )
        filters = self.filters_from_request()
        for f, v in filters:
            query = f.apply(query, v)
        buffer = StringIO.StringIO(b'')
        writer = csv.writer(buffer)
        writer.writerow(self.column_list)
        writer.writerows(query.all())
        return buffer.getvalue(), '{}_filldata_raw_{}.csv'.format(
            dt.datetime.utcnow().strftime('%y%m%d%H%M'),
            request.query_string )
    
    @expose('/csv/final')
    @csvdownload
    def export_final (self):
        """ Render a CSV with only the final color of each area. """
        fill_bis = db.aliased(Fill)
        query = (
            self.session.query(
                Survey.name,
                Page.name,
                Area.name,
                Subject.id,
                db.func.max(Fill.time).label('time'),
                db.func.count().label('clicks'),
                Color.code )
            .select_from(Fill)
            .join(Fill.survey, Fill.page, Fill.area, Fill.subject)
            .group_by(Survey.id, Page.id, Area.id, Subject.id)
            .join(fill_bis, db.and_(
                fill_bis.survey_id == Fill.survey_id,
                fill_bis.page_id == Fill.page_id,
                fill_bis.area_id == Fill.area_id,
                fill_bis.subject_id == Fill.subject_id,
                fill_bis.time == Fill.time ))
            .join(Color, Color.id == fill_bis.color_id)
        )
    
    def filters_from_request (self):
        """
            Parse the request arguments and return flask-admin Filter objects.
            
            This is an extract from flask-admin sqla.ModelView.get_list.
            Example of usage:
            
            >>> import coloringbook as cb, coloringbook.testing as t
            >>> testapp = t.get_fixture_app()
            >>> s = cb.models.db.session
            >>> with testapp.test_request_context('?flt1_22=rode'):
            ...     cb.admin.views.FillView(s).filters_from_request()
            [(<flask_admin.contrib.sqla.filters.FilterLike object at 0x...>, u'rode')]
        """
        
        filters = self._get_list_extra_args()[4]
        applicables = []

        if filters and self._filters:
            for idx, value in filters:
                flt = self._filters[idx]
                applicables.append((flt, value))
        
        return applicables
    
class SurveyView (ModelView):
    """ Custom admin table view of Survey objects. """
    
    edit_template = 'admin/augmented_edit.html'
    can_delete = False
    column_list = 'name language begin end information'.split()
    column_sortable_list = (
        ('name', Survey.name),
        ('language', Language.name),
        'begin',
        'end',
    )
    column_auto_select_related = True
    column_searchable_list = ('information',)
    column_default_sort = ('begin', True)
    column_display_all_relations = True
    form_columns = ('name', 'language', 'begin', 'end', 'information', 'page_list')
    form_extra_fields = {
        'page_list': Select2MultipleField('Pages', choices = db.session.query(Page.id, Page.name).order_by(Page.name).all(), coerce = int),
    }
        
    def on_model_change (self, form, model, is_created = False):
        if not is_created:
            self.session.query(SurveyPage).filter_by(survey=model).delete()
        for index, id in enumerate(form.page_list.data):
            SurveyPage(survey = model, page_id = id, ordering = index)
    
    def on_form_prefill (self, form, id):
        form.page_list.process_data(
            self.session.query(SurveyPage.page_id)
            .filter(SurveyPage.survey_id == id)
            .order_by(SurveyPage.ordering)
            .all()
        )
    
    def __init__ (self, session, **kwargs):
        super(SurveyView, self).__init__(Survey, session, name='Surveys', **kwargs)

class PageView(ModelView):
    """
        Custom admin table view of Page objects with associated Expectations.
    """
    
    edit_template = 'admin/augmented_edit.html'
    column_list = 'name drawing language text sound'.split()
    column_sortable_list = (
        'name',
        ('drawing', Drawing.name),
        ('language', Language.name),
        ('sound', Sound.name),
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
        rules.Container('hide', rules.Field('drawing')),
        'language',
        'text',
        'sound',
        rules.Container('hide', rules.Field('fname')),
        rules.Container('hide', rules.Field('expect_list')),
        rules.Macro('drawing.edit_expectations'),
    )
    
    def on_model_change (self, form, model, is_created = False):
        if not is_created:
            Expectation.query.filter_by(page = model).delete()
            new_expectations = json.loads(form.expect_list.data)
            for area_name, settings in new_expectations.iteritems():
                color = Color.query.filter_by(code = settings['color']).one()
                area = Area.query.filter_by(name = area_name).one()
                model.expectations.append(Expectation(
                    area = area,
                    color = color,
                    here = settings['here'] ))
    
    def on_form_prefill (self, form, id):
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
    
    def __init__ (self, session, **kwargs):
        super(PageView, self).__init__(Page, session, name='Pages', **kwargs)

class DrawingView(ModelView):
    """ Custom admin table view of Drawing objects with associated Areas. """
    
    edit_template = 'admin/augmented_edit.html'
    form_columns = ('file', 'area_list', 'svg_source')
    form_extra_fields = {
        'file': form.FileUploadField(
            'Drawing',
            base_path = file_path,
            allowed_extensions = ('svg',) ),
        'area_list': fields.HiddenField(),
        'svg_source': fields.HiddenField(),
    }
    form_create_rules = ('file',)
    form_edit_rules = (
        rules.Container('hide', rules.Field('area_list')),
        rules.Container('hide', rules.Field('svg_source')),
        rules.Macro('drawing.edit_areas'),
    )
        
    def on_model_change (self, form, model, is_created = False):
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
                Area.query.filter_by(drawing = model, name = area).delete()
            added_areas = new_area_set - old_area_set
            for area in added_areas:
                model.areas.append(Area(name = area))
            open(op.join(file_path, model.name) + '.svg', 'w').write(
                form.svg_source.data )
    
    def on_form_prefill (self, form, id):
        form.svg_source.process_data(
            open(
                op.join(
                    file_path,
                    self.session.query(Drawing.name).filter_by(id = id).scalar()
                ) + '.svg'
            )
            .read()
        )
        form.area_list.process_data(','.join(x[0] for x in
            self.session.query(Area.name)
            .filter_by(drawing_id = id)
            .all()
        ))
    
    def __init__ (self, session, **kwargs):
        super(DrawingView, self).__init__(Drawing, session, name='Drawings', **kwargs)

@listens_for(Drawing, 'after_delete')
def delete_drawing(mapper, connection, target):
    # Delete image
    try:
        os.remove(op.join(file_path, target.name + '.svg'))
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
            base_path = file_path,
            allowed_extensions = ('mp3',) ),
    }
    
    def on_model_change (self, form, model, is_created = False):
        if is_created:
            model.name = op.splitext(form.file.data.filename)[0]
        
    def __init__ (self, session, **kwargs):
        super(SoundView, self).__init__(Sound, session, name='Sounds', **kwargs)

@listens_for(Sound, 'after_delete')
def delete_sound(mapper, connection, target):
    # Delete image
    try:
        os.remove(op.join(file_path, target.name + '.mp3'))
    except OSError:
        # Don't care if it was not deleted because it does not exist
        pass
