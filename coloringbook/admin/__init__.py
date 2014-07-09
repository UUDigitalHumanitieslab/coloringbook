from flask import make_response

from flask.ext.admin import Admin, expose
from flask.ext.admin.contrib.sqla import ModelView

from ..models import *

admin = Admin(name='Coloringbook')

def csvdownload (filename):
    ''' View decorator adding suitable response headers for CSV downloads. '''

    def decorate (view):
        def wrap (self):
            response = make_response(view(self))
            response.headers['Cache-Control'] = 'max-age=600'
            response.headers['Content-Disposition'] = 'attachment; filename="{}"'.format(filename)
            response.headers['Content-Type'] = 'text/csv; charset=utf-8'
            return response
        return wrap

    return decorate

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
    
    @expose('/csv')
    @csvdownload('filldata_raw.csv')
    def export (self):
        ''' Render a CSV, similar in operation to BaseModelView.index_view. '''
        
        return self.render(
            'admin/list.csv',
            data = self.full_query().all(),
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

admin.add_view(FillView(db.session))
