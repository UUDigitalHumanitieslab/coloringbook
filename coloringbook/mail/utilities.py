import csv
import StringIO
from celery import shared_task
from flask import render_template, current_app
import redis
from coloringbook.mail import mail_client
from flask_mail import Message
import datetime as dt

from coloringbook.utilities import (
    actions_from_json,
    subject_from_json,
    get_survey_pages,
    evaluate_page_actions
)

def create_survey_results_csv(survey_results):
    """
    Compose a list of CSV files with survey results, one for each session, to be sent as email attachments.

    >>> import coloringbook as cb, coloringbook.testing as t
    >>> from coloringbook.admin.views import FillView
    >>> testapp = t.get_fixture_app()
    >>> s = cb.models.db.session

    >>> survey_results = [
    ...     {
    ...         "survey_name": "Test Survey 1",
    ...         "subject_name": "Bob",
    ...         "subject_dob": "2000-01-01",
    ...         "evaluations": [
    ...             {"page": "Test page 1", "target": "Car", "color": "black", "correct": 0},
    ...             {"page": "Test page 2", "target": "Boat", "color": "white", "correct": 1}
    ...         ],
    ...         "total_pages": 2,
    ...         "total_correct": 1,
    ...         "percentage_correct": 50
    ...     },
    ...     {
    ...         "survey_name": "Test Survey 1",
    ...         "subject_name": "Alice",
    ...         "subject_dob": "2000-01-01",
    ...         "evaluations": [
    ...             {"page": "Test page 1", "target": "Car", "color": "green", "correct": 1},
    ...             {"page": "Test page 2", "target": "Boat", "color": "white", "correct": 1}
    ...         ],
    ...         "total_pages": 2,
    ...         "total_correct": 2,
    ...         "percentage_correct": 100
    ...     }
    ... ]

    >>> with testapp.test_request_context():
    ...     csv_files = create_survey_results_csv(survey_results)
    ...     csv_file_1 = csv_files[0]
    ...     csv_file_2 = csv_files[1]

    >>> csv_reader = csv.reader(StringIO.StringIO(csv_file_1), delimiter=";")
    >>> headers = next(csv_reader)
    >>> headers
    ['Survey', 'Subject', 'Birthdate', 'Page', 'Target', 'Color', 'Correct']
    >>> rows = [row for row in csv_reader]
    >>> rows[0]
    ['Test Survey 1', 'Bob', '2000-01-01', 'Test page 1', 'Car', 'black', '0']
    >>> rows[1]
    ['Test Survey 1', 'Bob', '2000-01-01', 'Test page 2', 'Boat', 'white', '1']
    >>> rows[2]
    ['Test Survey 1', 'Bob', '2000-01-01', '2', 'Total', '', '1 (50%)']

    >>> csv_reader = csv.reader(StringIO.StringIO(csv_file_2), delimiter=";")
    >>> headers = next(csv_reader)
    >>> rows = [row for row in csv_reader]
    >>> rows[0]
    ['Test Survey 1', 'Alice', '2000-01-01', 'Test page 1', 'Car', 'green', '1']
    >>> rows[1]
    ['Test Survey 1', 'Alice', '2000-01-01', 'Test page 2', 'Boat', 'white', '1']
    >>> rows[2]
    ['Test Survey 1', 'Alice', '2000-01-01', '2', 'Total', '', '2 (100%)']

    """
    headers = ["Survey", "Subject", "Birthdate", "Page", "Target", "Color", "Correct"]
    csv_files = []

    for survey_result in survey_results:
        buffer = StringIO.StringIO(b"")
        writer = csv.writer(buffer, delimiter=";")
        writer.writerow(headers)
        for evaluation in survey_result["evaluations"]:
            writer.writerow(
                [
                    survey_result["survey_name"],
                    survey_result["subject_name"],
                    survey_result["subject_dob"],
                    evaluation["page"],
                    evaluation["target"],
                    evaluation["color"],
                    evaluation["correct"],
                ]
            )
        writer.writerow([
            survey_result["survey_name"],
            survey_result["subject_name"],
            survey_result["subject_dob"],
            survey_result["total_pages"],
            "Total",
            "",
            "{} ({}%)".format(survey_result["total_correct"], survey_result["percentage_correct"])
        ])
        csv_files.append(buffer.getvalue())
        buffer.close()

    return csv_files

def collect_csv_data(survey, survey_data):
    """
    Reads the survey session results and extracts/aggregates the data needed for the CSV files that are to be sent by email. There should be exactly one line in the CSV file for every page in the survey.

    >>> import coloringbook as cb, flask, datetime, coloringbook.testing
    >>> import coloringbook.models as m
    >>> from flask_mail import Mail
    >>> from HTMLParser import HTMLParser

    >>> app = coloringbook.testing.get_fixture_app()
    >>> mail = Mail(app)

    >>> testwelcome = m.WelcomeText(name='a', content='a')
    >>> testprivacy = m.PrivacyText(name='a', content='a')
    >>> testsuccess = m.SuccessText(name='a', content='a')
    >>> testinstruction = m.InstructionText(name='a', content='a')
    >>> teststartform = m.StartingForm(name='a', name_label='a', birth_label='a', eyesight_label='a', language_label='a')
    >>> testendform = m.EndingForm(name='a', introduction='a', difficulty_label='a', topic_label='a', comments_label='a')
    >>> testbuttonset = m.ButtonSet(name='a', post_instruction_button='a', post_page_button='a', post_survey_button='a', page_back_button='a')
    >>> testsurvey = cb.models.Survey(name='test', simultaneous=False, welcome_text=testwelcome, privacy_text=testprivacy, success_text=testsuccess, instruction_text=testinstruction, starting_form=teststartform, ending_form=testendform, button_set=testbuttonset)

    >>> testdrawing = cb.models.Drawing(name='picture')
    >>> testarealeft = cb.models.Area(name='left door')
    >>> testarearight = cb.models.Area(name='right door')
    >>> testdrawing.areas.append(testarealeft)
    >>> testdrawing.areas.append(testarearight)
    >>> testpage = cb.models.Page(name='testpage', language_id=1, text='test', drawing=testdrawing)
    >>> testsurveypage = cb.models.SurveyPage(survey=testsurvey, page=testpage, ordering=1)

    >>> survey_data = [
    ...     {
    ...         "subject": {
    ...             "name": "Bob",
    ...             "birth": "2000-01-01",
    ...             "languages": [["German", 10], ["Swahili", 1]],
    ...             "numeral": "",
    ...             "eyesight": ""
    ...         },
    ...         "results": [[
    ...             {
    ...                 "action": "fill",
    ...                 "color": "#000",
    ...                 "target": "left door",
    ...                 "time": 1000
    ...             },
    ...             {
    ...                 "action": "fill",
    ...                 "color": "#fff",
    ...                 "target": "right door",
    ...                 "time": 2000
    ...             }
    ...         ]]
    ...     }
    ... ]

    >>> with app.app_context():
    ...     s = cb.models.db.session
    ...     s.add(testsurveypage)
    ...     s.add(cb.models.Color(code='#000', name='black'))
    ...     s.add(cb.models.Color(code='#fff', name='white'))
    ...     s.flush()
    ...     csv_data = collect_csv_data(testsurvey, survey_data)

    >>> csv_data[0]['survey_name']
    'test'

    >>> csv_data[0]['evaluations'][0]['correct']
    0
    >>> csv_data[0]['evaluations'][0]['page']
    'testpage'
    >>> csv_data[0]['evaluations'][0]['target']
    'left door, right door'
    >>> csv_data[0]['evaluations'][0]['color']
    u'black, white'
    """
    batch_results = []
    # Every datum corresponds to a subject.
    for datum in survey_data:
        subject = subject_from_json(datum["subject"])
        pages = get_survey_pages(survey)

        # Every subject has a list of results, one for each page.
        results = datum["results"]
        evaluations = []
        for page, result in zip(pages, results):
            actions = actions_from_json(survey, page, subject, result)
            evaluations.append(evaluate_page_actions(actions, page))

        # The amount of evaluations is equal to the amount of pages in the survey.
        total_pages = len(pages)
        total_correct_evaluations = sum([evaluation["correct"] for evaluation in evaluations])
        # In Python 2, division of integers returns an integer, so we need to cast the total_pages to a float.
        percentage_correct_unrounded = (total_correct_evaluations / float(total_pages) * 100) if total_pages > 0 else 0
        percentage_correct_rounded = int(round(percentage_correct_unrounded))

        batch_results.append(
            {
                "survey_name": survey.name,
                "subject_name": datum["subject"]["name"],
                "subject_dob": datum["subject"]["birth"],
                "evaluations": evaluations,
                "total_pages": total_pages,
                "total_correct": total_correct_evaluations,
                "percentage_correct": percentage_correct_rounded,
            }
        )
    return batch_results

def is_broker_available():
    """
    Checks whether the Redis broker is available.
    """
    try:
        redis_client = redis.StrictRedis.from_url('redis://redis:6379/0')
        redis_client.ping()
        return True
    except redis.exceptions.ConnectionError:
        return False

def send_email(survey_data, survey, immediate=False):
    """
    Send an email with a summary of the survey data to the email address(es) attached to a survey.

    :param survey_data: The survey data to send.
    :param survey: The survey that the data belongs to.
    :param immediate: If False (default), send the asynchronously via Celery. If True, send the email immediately (for testing purposes).

    >>> import coloringbook as cb, flask, datetime, coloringbook.testing
    >>> import coloringbook.models as m
    >>> from flask_mail import Mail
    >>> from HTMLParser import HTMLParser

    >>> app = coloringbook.testing.get_fixture_app()
    >>> mail = Mail(app)

    >>> testwelcome = m.WelcomeText(name='a', content='a')
    >>> testprivacy = m.PrivacyText(name='a', content='a')
    >>> testsuccess = m.SuccessText(name='a', content='a')
    >>> testinstruction = m.InstructionText(name='a', content='a')
    >>> teststartform = m.StartingForm(name='a', name_label='a', birth_label='a', eyesight_label='a', language_label='a')
    >>> testendform = m.EndingForm(name='a', introduction='a', difficulty_label='a', topic_label='a', comments_label='a')
    >>> testbuttonset = m.ButtonSet(name='a', post_instruction_button='a', post_page_button='a', post_survey_button='a', page_back_button='a')
    >>> testsurvey = cb.models.Survey(name='test', simultaneous=False, welcome_text=testwelcome, privacy_text=testprivacy, success_text=testsuccess, instruction_text=testinstruction, starting_form=teststartform, ending_form=testendform, button_set=testbuttonset, email_address='test.recipient@colbook.com; test.recipient2@colbook.com')

    >>> testdrawing = cb.models.Drawing(name='picture')
    >>> testarealeft = cb.models.Area(name='left door')
    >>> testarearight = cb.models.Area(name='right door')
    >>> testdrawing.areas.append(testarealeft)
    >>> testdrawing.areas.append(testarearight)
    >>> testpage = cb.models.Page(name='testpage', language_id=1, text='test', drawing=testdrawing)
    >>> testsurveypage = cb.models.SurveyPage(survey=testsurvey, page=testpage, ordering=1)

    >>> survey_data = [
    ...     {
    ...         "subject": {
    ...             "name": "Bob",
    ...             "birth": "2000-01-01",
    ...             "languages": [["German", 10], ["Swahili", 1]],
    ...             "numeral": "",
    ...             "eyesight": ""
    ...         },
    ...         "results": [[
    ...             {
    ...                 "action": "fill",
    ...                 "color": "#000",
    ...                 "target": "left door",
    ...                 "time": 1000
    ...             },
    ...             {
    ...                 "action": "fill",
    ...                 "color": "#fff",
    ...                 "target": "left door",
    ...                 "time": 2000
    ...             }
    ...         ]]
    ...     }
    ... ]

    >>> with app.app_context(), mail.record_messages() as outbox:
    ...     s = cb.models.db.session
    ...     s.add(testsurveypage)
    ...     s.add(cb.models.Color(code='#000', name='black'))
    ...     s.add(cb.models.Color(code='#fff', name='white'))
    ...     s.flush()
    ...     send_email(
    ...         survey_data=survey_data,
    ...         survey=testsurvey,
    ...         immediate=True,
    ...     )
    ...     outbox_length = len(outbox)
    ...     first_message = outbox[0]

    >>> outbox_length
    2

    >>> first_message.subject
    'ColoringBook - nieuwe resultaten opgeslagen'

    >>> class TestHTMLParser(HTMLParser):
    ...     def __init__(self):
    ...         HTMLParser.__init__(self)
    ...         self.data = []
    ...     def handle_data(self, data):
    ...         self.data.append(data.strip())

    >>> parser = TestHTMLParser()
    >>> parser.feed(first_message.html)

    >>> parser.data[0]
    u'Hallo,'

    >>> parser.data[4]
    u'De vragenlijst test is ingevuld door 1 deelnemer(s).'
    """

    recipients = [address.strip() for address in survey.email_address.split(";")]
    if len(recipients) == 0:
        return

    message_subject = "ColoringBook - nieuwe resultaten opgeslagen"

    csv_data = collect_csv_data(survey, survey_data)

    template_context = {"survey_name": survey.name, "number_of_participants": len(survey_data)}
    html_body = render_template("email/email.html", context=template_context)

    csv_files = create_survey_results_csv(csv_data)

    for recipient in recipients:
        # Only for testing purposes.
        if immediate is True:
            send_async_email(message_subject, recipient, html_body, csv_files)

        if is_broker_available():
            send_async_email.delay(message_subject, recipient, html_body, csv_files)
        else:
            current_app.logger.warning('Broker not available. Skipping sending emails...')
            return


@shared_task(bind=True, max_retries=3)
def send_async_email(self, subject, recipient, html, attachments):
    message = Message(subject=subject, recipients=[recipient], html=html)

    for index, attachment in enumerate(attachments):
        attachment_file_name = "{}_{}_{}.csv".format(
            dt.datetime.now().strftime("%y%m%d%H%M"), 'survey_results', index
        )

        message.attach(
            filename=attachment_file_name,
            content_type="text/csv",
            data=attachment,
            disposition="attachment"
        )

    try:
        mail_client.send(message)
    except Exception as exception:
        raise self.retry(exc=exception)
