from flask import make_response

from flask.ext.admin import Admin, expose
from flask.ext.admin.contrib.sqla import ModelView

from ..models import *

admin = Admin(name='Coloringbook')

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
#    column_default_sort = 'survey'
    page_size = 100
    column_display_all_relations = True
    
    def __init__ (self, session, **kwargs):
        super(FillView, self).__init__(Fill, session, name='Data', **kwargs)
    
    @expose('/csv')
    def export (self):
        ''' Render a CSV, similar in operation to BaseModelView.index_view. '''
        
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
        data = query.limit(None).all()
        
        response = make_response(self.render(
            'admin/list.csv',
            data=data,
            list_columns=self._list_columns,
            get_value=self.get_list_value ))
        response.headers['Cache-Control'] = 'max-age=600'
        response.headers['Content-Disposition'] = 'attachment; filename="raw.csv"'
        response.headers['Content-Type'] = 'text/csv; charset=utf-8'
        return response

admin.add_view(FillView(db.session))
