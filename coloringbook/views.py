# (c) 2014, 2016 Digital Humanities Lab, Utrecht University
# Author: Julian Gonggrijp, j.gonggrijp@uu.nl

"""
    Views for the public frontend of the website, with auxiliary functions.
    
    The views are added to a flask.Blueprint, `site`, which is later
    registered on the application in __init__.create_app. This avoids
    the cyclical import hack demonstrated on
    http://flask.pocoo.org/docs/0.10/patterns/packages/.
"""

from datetime import date, datetime

from flask import Blueprint, render_template, request, json, abort, jsonify, send_from_directory, current_app

from .models import *


MAX_AGE_TOLERANCE = 36524  # approx. number of days in 100 years

site = Blueprint('site', __name__)


@site.route('/')
def index():
    return 'Welkom bij Coloringbook.'


@site.route('/media/<file_name>')
def fetch_media(file_name):
    return send_from_directory(current_app.instance_path, file_name)


def get_survey_pages(survey):
    """ Returns all pages that are associated with a survey. """
    return (
        Page.query
        .join(*Page.surveys.attr)
        .filter(Survey.id == survey.id)
        .order_by(SurveyPage.ordering)
        .all()
    )


@site.route('/book/<survey_name>')
def fetch_coloringbook(survey_name):
    """
        Depending on whether the current request is XHR, either render
        the coloringbook HTML backbone (if not XHR) or render the
        pages associated with the current survey in JSON format (if
        XHR).
    """
    try:
        survey = Survey.query.filter_by(name=survey_name).one()
        today = datetime.today()
        if (survey.end and survey.end < today or
                survey.begin and survey.begin > today):
            raise RuntimeError('Survey not available at this time.')
        if request.is_xhr:
            pages = get_survey_pages(survey)
            page_list = []
            audio_set = set()
            image_set = set()
            for p in pages:
                image = p.drawing.name + '.svg'
                image_set.add(image)
                page = {'image': image}
                if p.sound:
                    sound = p.sound.name
                    audio_set.add(sound)
                    page['audio'] = sound
                if p.text:
                    page['text'] = p.text
                else:
                    page['text'] = ''
                page_list.append(page)
            return jsonify(
                simultaneous=survey.simultaneous,
                duration=survey.duration,
                images=[i for i in image_set],
                sounds=[s for s in audio_set],
                pages=page_list )
        else:
            return render_template('coloringbook.html')
    except Exception as e:
        abort(404)


@site.route('/book/<survey_name>/submit', methods=['POST'])
def submit(survey_name):
    """ Parse and store data sent by the test subject, all in one go. """
    
    s = db.session
    try:
        survey = Survey.query.filter_by(name = survey_name).one()
        data = request.get_json()
        subject = subject_from_json(data['subject'])
        s.add(subject)
        bind_survey_subject(survey, subject, data['evaluation'])
        pages = get_survey_pages(survey)
        results = data['results']
        assert len(pages) == len(results)
        for page, result in zip(pages, results):
            s.add_all(fills_from_json(survey, page, subject, result))
        s.commit()
        return 'Success'
    except:
        return 'Error'


def subject_from_json(data):
    """
        Take personal information from JSON and put into relational object.
        
        `data` contains the object from the 'subject' key in the
        request data sent from the JavaScript frontend. The return
        value is a Subject as defined in .models. The subject is not
        yet added to the database. Consider the following example code:
        
        >>> import coloringbook.testing as t
        >>> app = t.get_fixture_app()
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
        name=data['name'],
        numeral=int(data['numeral']) if data['numeral'] else None,
        birth=birth_date,
        eyesight=data['eyesight'] )
    
    for name, level in data['languages']:
        if not name:
            raise ValueError('Incomplete language data')
        language = Language.query.filter_by(name=name).first()
        if language == None:
            language = Language(name=name)
        SubjectLanguage(subject=subject, language=language, level=level)
    
    return subject


def bind_survey_subject(survey, subject, evaluation):
    """
        Create the association between a Survey and a Subject, with associated evaluation data from a parsed JSON dictionary.
        
        Example of usage:
        
        >>> import coloringbook.models as m, coloringbook.testing as t
        >>> from flask import jsonify
        >>> from datetime import datetime
        >>> app = t.get_fixture_app()
        >>> testsurvey = m.Survey(name='test')
        >>> testsubject = m.Subject(name='Koos', birth=datetime.now())
        >>> testevaluation = {
        ...     'difficulty': 5,
        ...     'topic': 'was this about anything?',
        ...     'comments': 'no comment.',
        ... }
        >>> with app.app_context():
        ...     bind_survey_subject(testsurvey, testsubject, testevaluation)
        
        >>> testsurvey.subjects[0].name
        'Koos'
        >>> testsurvey.survey_subjects[0].difficulty
        5
        >>> testsurvey.survey_subjects[0].topic
        'was this about anything?'
        >>> testsurvey.survey_subjects[0].comments
        'no comment.'
        >>> testsubject.surveys[0].name
        'test'
        >>> testsubject.subject_surveys[0].difficulty
        5
    """
    binding = SurveySubject(survey=survey, subject=subject)
    if 'difficulty' in evaluation:
        binding.difficulty = evaluation['difficulty']
    if 'topic' in evaluation:
        binding.topic = evaluation['topic']
    if 'comments' in evaluation:
        binding.comments = evaluation['comments']


def fills_from_json(survey, page, subject, data):
    """
        Take fill actions from JSON and put into [relational object].
        
        `survey`, `page` and `subject` must be pre-instantiated
        objects of the respective models. `data` is a parsed JSON
        object containing one item from the 'results' key in the
        request data sent from the JavaScript frontend. The Colors and
        Areas referred to from the `data` must already exist in the
        database, otherwise a NoResultFound exception will be thrown.
        Example:
        
        >>> import coloringbook as cb, flask, datetime, coloringbook.testing
        >>> app = coloringbook.testing.get_fixture_app()
        >>> # some trivial contents for the database
        >>> testdrawing = cb.models.Drawing(name='picture')
        >>> testdrawing.areas.append(cb.models.Area(name='left door'))
        >>> testdrawing.areas.append(cb.models.Area(name='right door'))
        >>> testpage = cb.models.Page(name='page1', drawing=testdrawing, text='test 123')
        >>> testsurvey = cb.models.Survey(name='test', simultaneous=False)
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
    areas = Area.query.filter_by(drawing=page.drawing)
    fills = []
    for datum in data:
        fills.append(Fill(
            survey=survey,
            page=page,
            area=areas.filter_by(name=datum['target']).one(),
            subject=subject,
            time=int(datum['time']),
            color=colors.filter_by(code=datum['color']).one() ))
    return fills
