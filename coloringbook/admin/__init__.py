from flask.ext.admin import Admin, BaseView, expose
from flask.ext.admin.contrib.sqla import ModelView

from ..models import *

admin = Admin(name='Coloringbook')

class FillView (ModelView):
    ''' Custom admin table view of Fill objects. '''
    
    can_create = False
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

class FillViewReplica (BaseView):
    ''' Attempt at mimicking Fill table view from scratch. '''
    
    @expose('/')
    def index (self):
        self.data = Fill.query.subquery()
        return self.render('admin/fill_imitation.html')

admin.add_view(FillView(db.session))
admin.add_view(FillViewReplica(name = 'Replica'))
