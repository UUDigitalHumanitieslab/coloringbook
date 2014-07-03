from flask.ext.admin import Admin
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
    
    def __init__(self, session, **kwargs):
        super(FillView, self).__init__(Fill, session, name='Data', **kwargs)

admin.add_view(FillView(db.session))
