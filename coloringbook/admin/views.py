from flask.ext.admin import expose, form
from flask.ext.admin.contrib.sqla import ModelView, ajax

from ..models import *

from .utilities import csvdownload

class SurveyView (ModelView):
    ''' Custom admin table view of Survey objects. '''
    
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
        'page_list': form.Select2Field('Pages', choices = db.session.query(Page.id, Page.name).order_by(Page.name).all(), coerce = int)
    }
    form_widget_args = {
        'page_list': { 'multiple': True },
    }
#     form_ajax_refs = {
#         'pages': ajax.QueryAjaxModelLoader('Pages', db.session, Page, fields=['name'])
#     }
    
    def __init__ (self, session, **kwargs):
        super(SurveyView, self).__init__(Survey, session, name='Surveys', **kwargs)
#         self.form_extra_fields['pages'].

class FillView (ModelView):
    ''' Custom admin table view of Fill objects. '''
    
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
    column_filters = column_list
#    column_default_sort = 'survey'  # doesn't work for some reason
    page_size = 100
    column_display_all_relations = True
    
    def __init__ (self, session, **kwargs):
        super(FillView, self).__init__(Fill, session, name='Data', **kwargs)
    
    @expose('/csv/raw')
    @csvdownload('filldata_raw.csv')
    def export_raw (self):
        ''' Render a CSV, similar in operation to BaseModelView.index_view. '''
        
        return self.render(
            'admin/list.csv',
            data = self.full_query().all(),
            list_columns = self._list_columns,
            get_value = self.get_list_value )
    
    @expose('/csv/final')
    @csvdownload('filldata_final.csv')
    def export_final (self):
        ''' Render a CSV with only the final color of each area. '''
        
        full = self.model
        fnl = self.get_final_q().subquery('final')
        
        print self.full_query().statement

        merged = (
            self.session.query(full)
            .join(
                fnl,
                db.and_(
                    full.survey_id == fnl.c.survey_id,
                    full.page_id == fnl.c.page_id,
                    full.area_id == fnl.c.area_id,
                    full.subject_id == fnl.c.subject_id,
                    full.time == fnl.c.time ) )
        )
        
        print '-----'
        print merged.statement
        
#         survey_1 = db.aliased(Survey, name = 'survey_1')
#         page_1 = db.aliased(Page, name = 'page_1')
#         area_1 = db.aliased(Area, name = 'area_1')
#         subject_1 = db.aliased(Subject, name = 'subject_1')
#         color_1 = db.aliased(Color, name = 'color_1')
#         
#         next_step = (
#             merged.outerjoin(survey_1, page_1, area_1, subject_1, color_1)
#             .add_entity(survey_1)
#             .add_entity(page_1)
#             .add_entity(area_1)
#             .add_entity(subject_1)
#             .add_entity(color_1)
#         )
        
        next_step = (
            self.full_query()
            .reset_joinpoint()
            .select_entity_from(merged.subquery('fill'))
        )
        
        print '-----'
        print next_step.statement
        
        return self.render(
            'admin/list.csv',
            data = next_step.all(),
            list_columns = self._list_columns,
            get_value = self.get_list_value )
    
    def full_query (self):
        ''' Get the un-paged query for the currently displayed data. '''
        
        page, sort_idx, sort_desc, search, filters = self._get_list_extra_args()
        
        # Map column index to column name
        sort_column = self._get_column_by_idx(sort_idx)
        if sort_column is not None:
            sort_column = sort_column[0]

        # Get count and query
        count, query = self.get_list(
            None,
            sort_column,
            sort_desc,
            search,
            filters,
            False )
        return query.limit(None)
    
    def get_final_q (self):
        ''' Get the query for the final Color of each Area. '''
        
        return (
            self.session
            .query(
                self.model.survey_id,
                self.model.page_id,
                self.model.area_id,
                self.model.subject_id,
                db.func.max(self.model.time).label('time') )
            .group_by(
                self.model.survey_id,
                self.model.page_id,
                self.model.area_id,
                self.model.subject_id )
        )
