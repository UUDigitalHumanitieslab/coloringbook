from datetime import date

from flask import Blueprint, render_template, request, json

from .models import *

site = Blueprint('site', __name__)

@site.route('/')
def index():
    return render_template('coloringbook.html')

@site.route('/submit', methods=['POST'])
def submit():
    ''' Parse and store data sent by the test subject, all in one go. '''
    
    s = db.session
    data = request.get_json()
    subject = subject_from_json(data['subject'])
    s.add(subject)  # TODO: add uniqueness constraint and conflict handling
    survey = Survey.query().filter_by(name = data['survey']).one()
    pages = (
        Page.query()
        .join(*Page.surveys.attr)
        .filter(Survey.id == survey.id)
        .order_by(SurveyPage.order)
        .all()
    )
    results = data['results']
    assert len(pages) == len(results)  # TODO: handle errors rather than crashing hard
    for page, result in zip(pages, results):
        s.add_all(fills_from_json(survey, page, subject, result))
    s.commit()
    return 'Success'
    
def subject_from_json (data):
    ''' Take personal information from JSON and put into relational object. '''
    
    subject = Subject(
        name = data['name'],
        numeral = data['numeral'],
        birth = date(*map(int, data['birth'].split('-'))),  # TODO: enforce format
        eyesight = data['eyesight'] )
    
    for name, level in data['languages']:
        language = Language.query().filter_by(name = name).first()
        if language == None:
            language = Language(name = name)
        SubjectLanguage(subject = subject, language = language, level = level)
    
    return subject
    
def fills_from_json (survey, page, subject, data):
    ''' Take fill actions from JSON and put into [relational object]. '''
    
    colors = Color.query()
    areas = Area.query().filter_by(drawing = page.drawing)
    fills = []
    for datum in data:
        fills.append(Fill(
            survey = survey,
            page = page,
            area = areas.filter_by(name = datum['target']).one(),  # TODO: handle errors
            subject = subject,
            time = datum['time'],
            color = colors.filter_by(code = datum['color']).one() ))  # as above
    return fills
