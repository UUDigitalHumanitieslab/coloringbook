from flask.ext.admin import Admin
from flask.ext.admin.contrib.sqla import ModelView

from ..models import *

def create_admin ( ):
    admin = Admin(name='Coloringbook')
    admin.add_view(FillView(db.session))
    admin.add_view(FinalFillView(db.session))
    return admin

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

class FinalFillView (FillView):
    ''' Custom admin table view of coloring end results. '''
    
    can_edit = False
    column_list = 'survey page area subject latest color numclicks'.split()
    column_sortable_list = (
        ('survey', Survey.name),
        ('page', Page.name),
        ('area', Area.name),
        ('subject', Subject.name),
        'latest',
        ('color', Color.code),
        'numclicks',
    )
    column_filters = column_list
    
    def __init__ (self, session, **kwargs):
        final_fill = Fill.final()
        class FinalFill (db.Model):
            __table__ = final_fill
            __mapper_args__ = {
                'primary_key': [
                    final_fill.c.survey_id,
                    final_fill.c.page_id,
                    final_fill.c.area_id,
                    final_fill.c.subject_id ] }
        super(FillView, self).__init__(
            FinalFill,
            session,
            name='Final data',
            **kwargs )
