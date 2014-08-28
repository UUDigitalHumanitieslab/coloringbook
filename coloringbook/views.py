# (c) 2014 Digital Humanities Lab, Faculty of Humanities, Utrecht University
# Author: Julian Gonggrijp, j.gonggrijp@uu.nl

"""
    Views for the public frontend of the website, with auxiliary functions.
    
    The views are added to a flask.Blueprint, `site`, which is later
    registered on the application in __init__.create_app. This avoids
    the cyclical import hack demonstrated on
    http://flask.pocoo.org/docs/0.10/patterns/packages/.
"""

from datetime import date

from flask import Blueprint, render_template, request, json

from .models import *

MAX_AGE_TOLERANCE = 36524  # approx. number of days in 100 years

site = Blueprint('site', __name__)

@site.route('/')
def index():
    return render_template('coloringbook.html')

@site.route('/submit', methods=['POST'])
def submit():
    """ Parse and store data sent by the test subject, all in one go. """
    
    s = db.session
    try:
        data = request.get_json()
        subject = subject_from_json(data['subject'])
        s.add(subject)
        survey = Survey.query.filter_by(name = data['survey']).one()
        survey.subjects.append(subject)
        pages = (
            Page.query
            .join(*Page.surveys.attr)
            .filter(Survey.id == survey.id)
            .order_by(SurveyPage.ordering)
            .all()
        )
        results = data['results']
        assert len(pages) == len(results)
        for page, result in zip(pages, results):
            s.add_all(fills_from_json(survey, page, subject, result))
        s.commit()
        return 'Success'
    except:
        return 'Error'
    
def subject_from_json (data):
    """
        Take personal information from JSON and put into relational object.
        
        `data` contains the object from the 'subject' key in the
        request data sent from the JavaScript frontend. The return
        value is a Subject as defined in .models. The subject is not
        yet added to the database. Consider the following example code:
        
        >>> # preparations
        >>> import coloringbook as cb
        >>> class config:
        ...     SQLALCHEMY_DATABASE_URI = 'sqlite://'
        >>> app = cb.create_app(config)
        >>> testdata = '''{
        ...     "name": "Bob",
        ...     "birth": "2000-01-01",
        ...     "languages": [["German", 10], ["Swahili", 1]],
        ...     "numeral": "",
        ...     "eyesight": ""
        ... }'''
        >>> testinput = json.loads(testdata)
        >>> # using the function
        >>> with app.app_context():
        ...     testoutput = subject_from_json(testinput)
        >>> # inspecting the result
        >>> testoutput
        <coloringbook.models.Subject object at 0x...>
        >>> testoutput.birth
        datetime.date(2000, 1, 1)
        >>> testoutput.name
        u'Bob'
        >>> testoutput.languages
        [<coloringbook.models.Language object at 0x...>, <coloringbook.models.Language object at 0x...>]
        >>> testoutput.subject_languages[0].language.name
        u'German'
        >>> testoutput.subject_languages[1].level
        1
    """
    
    if not data['name']:
        raise ValueError('Name must be non-empty')
    if not data['birth']:
        raise ValueError('Birth date must be non-empty')
    if not data['languages']:
        raise ValueError('Native language must be set')
    birth_date = date(*map(int, data['birth'].split('-')))
    today = date.today()
    current_age = today - birth_date
    if current_age.days > MAX_AGE_TOLERANCE:
        raise ValueError('Age greater than maximum tolerance')
    if current_age.days < 0:
        raise ValueError('Negative age')
    
    subject = Subject(
        name = data['name'],
        numeral = int(data['numeral']) if data['numeral'] else None,
        birth = birth_date,
        eyesight = data['eyesight'] )
    
    for name, level in data['languages']:
        if not name:
            raise ValueError('Incomplete language data')
        language = Language.query.filter_by(name = name).first()
        if language == None:
            language = Language(name = name)
        SubjectLanguage(subject = subject, language = language, level = level)
    
    return subject
    
def fills_from_json (survey, page, subject, data):
    """
        Take fill actions from JSON and put into [relational object].
        
        `survey`, `page` and `subject` must be pre-instantiated
        objects of the respective models. `data` is a parsed JSON
        object containing one item from the 'results' key in the
        request data sent from the JavaScript frontend. The Colors and
        Areas referred to from the `data` must already exist in the
        database, otherwise a NoResultFound exception will be thrown.
        Example:
        
        >>> # general preparations
        >>> import coloringbook as cb, flask, datetime
        >>> class config:
        ...     SQLALCHEMY_DATABASE_URI = 'sqlite://'
        >>> app = cb.create_app(config)
        >>> # some trivial contents for the database
        >>> testdrawing = cb.models.Drawing(name='picture')
        >>> testdrawing.areas.append(cb.models.Area(name='left door'))
        >>> testdrawing.areas.append(cb.models.Area(name='right door'))
        >>> testpage = cb.models.Page(name='page1', drawing=testdrawing, text='test 123')
        >>> testsurvey = cb.models.Survey(name='test')
        >>> testsubject = cb.models.Subject(name='Bob', birth=datetime.date(2000, 1, 1))
        >>> # the to be added new contents for the database
        >>> testdata = '''[
        ...     {
        ...         "color": "#000",
        ...         "target": "left door",
        ...         "time": 1000
        ...     },
        ...     {
        ...         "color": "#fff",
        ...         "target": "left door",
        ...         "time": 2000
        ...     },
        ...     {
        ...         "color": "#000",
        ...         "target": "right door",
        ...         "time": 3000
        ...     }
        ... ]'''
        >>> testinput = flask.json.loads(testdata)
        >>> with app.app_context():
        ...     # make sure the pre-existing data are persistent
        ...     s = cb.models.db.session
        ...     s.add(testpage)
        ...     s.add(cb.models.Color(code='#000', name='black'))
        ...     s.add(cb.models.Color(code='#fff', name='white'))
        ...     s.flush()
        ...     # using the function
        ...     testoutput = fills_from_json(testsurvey, testpage, testsubject, testinput)
        >>> # inspecting the outcome
        >>> testoutput[0].survey == testsurvey
        True
        >>> testoutput[0].page == testpage
        True
        >>> testoutput[1].area.name == 'left door'
        True
        >>> testoutput[1].subject == testsubject
        True
        >>> testoutput[2].time == 3000
        True
        >>> testoutput[2].color.name == 'black'
        True
        >>> testoutput[3]
        Traceback (most recent call last):
          ...
        IndexError: list index out of range
    """
    
    colors = Color.query
    areas = Area.query.filter_by(drawing = page.drawing)
    fills = []
    for datum in data:
        fills.append(Fill(
            survey = survey,
            page = page,
            area = areas.filter_by(name = datum['target']).one(),
            subject = subject,
            time = int(datum['time']),
            color = colors.filter_by(code = datum['color']).one() ))
    return fills
