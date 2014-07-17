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
    ''' Parse and store data sent by the test subject, all in one go. '''
    
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
    ''' Take personal information from JSON and put into relational object. '''
    
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
    ''' Take fill actions from JSON and put into [relational object]. '''
    
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
