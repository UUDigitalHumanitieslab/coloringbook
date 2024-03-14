# (c) 2014-2023 Research Software Lab, Centre for Digital Humanities, Utrecht University
# Licensed under the EUPL-1.2 or later. You may obtain a copy of the license at
# https://joinup.ec.europa.eu/collection/eupl/eupl-text-eupl-12.

"""
    Views for the public frontend of the website, with auxiliary functions.

    The views are added to a flask.Blueprint, `site`, which is later
    registered on the application in __init__.create_app. This avoids
    the cyclical import hack demonstrated on
    http://flask.pocoo.org/docs/0.10/patterns/packages/.
"""

from datetime import datetime
from functools import partial
import traceback

from flask import Blueprint, render_template, request, json, abort, jsonify, send_from_directory, current_app, redirect

from .models import Survey, SurveySubject, db

from .mail.utilities import send_email
from .utilities import fills_from_json, subject_from_json, get_survey_pages


site = Blueprint('site', __name__)

@site.route('/ping', methods=['HEAD'])
def ping():
    return current_app.response_class()


@site.route('/')
def index():
    return redirect('https://coloringbook.wp.hum.uu.nl/')


@site.route('/media/<file_name>')
def fetch_media(file_name):
    return send_from_directory(current_app.instance_path, file_name)


@site.route('/book/<survey_name>')
def fetch_coloringbook(survey_name):
    """
        Depending on whether the current request is XHR, either render
        the coloring book HTML backbone (if not XHR) or render the
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
            return render_template('coloringbook.html', survey=survey)
    except Exception as e:
        abort(404)


@site.route('/book/<survey_name>/submit', methods=['POST'])
def submit(survey_name):
    """ Parse and store data sent by the test subject, all in one go. """
    try:
        survey = Survey.query.filter_by(name = survey_name).one()
        data = request.get_json()
    except:
        current_app.logger.error(
            'Batch submit failed for survey "{}".\n{}Data:\n{}'.format(
                survey_name,
                traceback.format_exc(),
                request.data,
            )
        )
        return 'Error'
    if all(map(partial(store_subject_data, survey), data)):
        if survey.email_address:
            send_email(
                recipient=survey.email_address,
                survey_data=data,
                survey=survey
            )
        return 'Success'
    else:
        return 'Error'


def store_subject_data(survey, data):
    """ Store complete survey data for a single subject. """
    s = db.session
    try:
        subject = subject_from_json(data['subject'])
        s.add(subject)
        bind_survey_subject(survey, subject, data['evaluation'])
        pages = get_survey_pages(survey)
        results = data['results']
        assert len(pages) == len(results)
        for pagenum, (page, result) in enumerate(zip(pages, results)):
            try:
                s.add_all(fills_from_json(survey, page, subject, result))
            except:
                current_app.logger.error(
                    'Next exception thrown on page {}.'.format(pagenum),
                )
                raise
        s.commit()
        return True
    except:
        current_app.logger.error(
            'Subject store failed for survey "{}".\n{}Data:\n{}'.format(
                survey.name,
                traceback.format_exc(),
                json.dumps(data),
            )
        )
        return False


def bind_survey_subject(survey, subject, evaluation):
    """
        Create the association between a Survey and a Subject, with associated evaluation data from a parsed JSON dictionary.

        Example of usage:

        >>> import coloringbook.models as m, coloringbook.testing as t
        >>> from flask import jsonify
        >>> from datetime import datetime
        >>> app = t.get_fixture_app()
        >>> testwelcome = m.WelcomeText(name='a', content='a')
        >>> testprivacy = m.PrivacyText(name='a', content='a')
        >>> testsuccess = m.SuccessText(name='a', content='a')
        >>> testinstruction = m.InstructionText(name='a', content='a')
        >>> testsurvey = m.Survey(name='test', welcome_text=testwelcome, privacy_text=testprivacy, success_text=testsuccess, instruction_text=testinstruction)
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

        Handle empty inputs correctly:
        >>> testevaluation = {
        ...     'difficulty': '',
        ...     'topic': '',
        ...     'comments': '',
        ... }
        >>> with app.app_context():
        ...     bind_survey_subject(testsurvey, testsubject, testevaluation)
        >>> testsurvey.survey_subjects[1].difficulty
        None
        >>> testsurvey.survey_subjects[1].topic
        ''
        >>> testsurvey.survey_subjects[1].comments
        ''
    """
    binding = SurveySubject(survey=survey, subject=subject)
    if 'difficulty' in evaluation:
        # The DB cannot handle empty strings for integer fields.
        binding.difficulty = evaluation['difficulty'] if evaluation['difficulty'] != '' else None
    if 'topic' in evaluation:
        binding.topic = evaluation['topic']
    if 'comments' in evaluation:
        binding.comments = evaluation['comments']
