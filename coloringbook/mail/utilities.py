import csv
import StringIO
from celery import shared_task
from flask import render_template
from coloringbook.mail import mail_client
from flask_mail import Message
import datetime as dt

from coloringbook.utilities import (
    fills_from_json,
    subject_from_json,
    get_survey_pages,
    is_fill_correct,
)

def compose_survey_results_csv(survey_results):
    """
    Compose a CSV file with survey results, to be sent as an email attachment.

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
    ...         "total_fills": 2,
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
    ...         "total_fills": 2,
    ...         "total_correct": 2,
    ...         "percentage_correct": 100
    ...     }
    ... ]

    >>> with testapp.test_request_context():
    ...     csv_file = compose_survey_results_csv(survey_results)
    >>> csv_reader = csv.reader(StringIO.StringIO(csv_file), delimiter=";")
    >>> headers = next(csv_reader)
    >>> headers
    ['Survey', 'Subject', 'Birthdate', 'Page', 'Target', 'Color', 'Correct', 'Total fills', 'Total correct', 'Percentage correct']
    >>> rows = [row for row in csv_reader]
    >>> rows[0]
    ['Test Survey 1', 'Bob', '2000-01-01', 'Test page 1', 'Car', 'black', '0', '2', '1', '50']
    >>> rows[1]
    ['Test Survey 1', 'Bob', '2000-01-01', 'Test page 2', 'Boat', 'white', '1', '2', '1', '50']
    >>> rows[2]
    ['Test Survey 1', 'Alice', '2000-01-01', 'Test page 1', 'Car', 'green', '1', '2', '2', '100']
    >>> rows[3]
    ['Test Survey 1', 'Alice', '2000-01-01', 'Test page 2', 'Boat', 'white', '1', '2', '2', '100']
    """
    headers = ["Survey", "Subject", "Birthdate", "Page", "Target", "Color", "Correct", "Total fills", "Total correct", "Percentage correct"]
    buffer = StringIO.StringIO(b"")
    writer = csv.writer(buffer, delimiter=";")
    writer.writerow(headers)

    for survey_result in survey_results:
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
                        survey_result["total_fills"],
                        survey_result["total_correct"],
                        survey_result["percentage_correct"],
                    ]
                )

    return buffer.getvalue()


def send_email(recipient, survey_data, survey, immediate=False):
    """
    Send an email to the given recipient with the given survey data.

    :param recipient: The email address of the recipient.
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
    ...         recipient="test.recipient@colbook.com",
    ...         survey_data=survey_data,
    ...         survey=testsurvey,
    ...         immediate=True,
    ...     )
    ...     outbox_length = len(outbox)
    ...     first_message = outbox[0]

    >>> outbox_length
    1

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

    message_subject = "ColoringBook - nieuwe resultaten opgeslagen"

    batch_results = []
    # Every datum corresponds to a subject.
    for datum in survey_data:
        subject = subject_from_json(datum["subject"])
        pages = get_survey_pages(survey)

        # Every subject has a list of results, one for each page.
        results = datum["results"]
        evaluations = []
        for page, result in zip(pages, results):
            fills = fills_from_json(survey, page, subject, result)
            for fill in fills:
                evaluations.append(
                    {
                        "page": page.name,
                        "target": fill.area,
                        "color": fill.color,
                        "correct": 1 if is_fill_correct(fill) else 0,
                    }
                )

        total_fills = len(fills)
        total_correct = sum([evaluation["correct"] for evaluation in evaluations])
        percentage_correct = (total_correct / total_fills * 100) if total_fills > 0 else 0

        batch_results.append(
            {
                "survey_name": survey.name,
                "subject_name": datum["subject"]["name"],
                "subject_dob": datum["subject"]["birth"],
                "evaluations": evaluations,
                "total_fills": total_fills,
                "total_correct": total_correct,
                "percentage_correct": percentage_correct,
            }
        )

    template_context = {"survey_name": survey.name, "number_of_participants": len(survey_data)}
    html_body = render_template("email/email.html", context=template_context)

    csv_file = compose_survey_results_csv(batch_results)

    # Only for testing purposes.
    if immediate is True:
        send_async_email(message_subject, recipient, html_body, csv_file)

    send_async_email.delay(message_subject, recipient, html_body, csv_file)


@shared_task(bind=True, max_retries=3)
def send_async_email(self, subject, recipient, html, attachment):
    message = Message(subject=subject, recipients=[recipient], html=html)

    attachment_file_name = "{}_{}.csv".format(
        dt.datetime.now().strftime("%y%m%d%H%M"), 'survey_results'
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
