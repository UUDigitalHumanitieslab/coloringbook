from flask.ext.admin import expose
from flask.ext.admin.contrib.sqla import ModelView

from ..models import *

from .utilities import csvdownload

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
        ('subject', Subject.name),
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
        
        full = self.full_query().subquery()
        finals = self.get_final_q().subquery()
        data = (
            self.session
            .query(full, finals)
            .filter(
                full.c.survey_id == finals.c.survey_id,
                full.c.page_id == finals.c.page_id,
                full.c.area_id == finals.c.area_id,
                full.c.subject_id == finals.c.subject_id,
                full.c.time == finals.c.time )
            .all()
        )
        
        return self.render(
            'admin/list.csv',
            data = data,
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
                'survey_id',
                'page_id',
                'area_id',
                'subject_id',
                db.func.max('time').label('time'),
                'color_id' )
            .select_from(self.model)
            .group_by(
                'survey_id',
                'page_id',
                'area_id',
                'subject_id' )
        )
