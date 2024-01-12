from celery import shared_task
from celery.exceptions import OperationalError
from flask import render_template
from coloringbook.mail import mail_client
from flask_mail import Message

from coloringbook.utilities import (
    fills_from_json,
    subject_from_json,
    get_survey_pages,
    is_fill_correct,
)


def send_email(recipient, survey_data, survey, immediate=False):
    """
    Send an email to the given recipient with the given survey data.

    :param recipient: The email address of the recipient.
    :param survey_data: The survey data to send.
    :param survey: The survey that the data belongs to.
    :param immediate: If False (default), send the asynchronously via Celery. If True, send the email immediately (for testing purposes).

    # Create test survey

    >>> import coloringbook as cb, flask, datetime, coloringbook.testing
    >>> import coloringbook.models as m
    >>> from flask_mail import Mail

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

    >>> first_message.html
    u'<p>Hallo,</p>\\n\\n<p>Dit is een automatisch gegenereerde e-mail van Coloring Book.</p>\\n\\n<p>De vragenlijst test is ingevuld door 1 deelnemer(s).</p>\\n    \\n<p>De resultaten zijn als volgt:</p>\\n\\n\\n<table>\\n    <caption>Bob (2000-01-01)</caption>\\n    <thead>\\n        <tr>\\n            <th>Pagina</th>\\n            <th>Doel</th>\\n            <th>Kleur</th>\\n            <th>Goed/fout</th>\\n        </tr>\\n    </thead>\\n    <tbody>\\n        \\n        <tr>\\n            <td>testpage</td>\\n            <td>left door</td>\\n            <td>black</td>\\n            <td>Fout</td>\\n        </tr>\\n        \\n        <tr>\\n            <td>testpage</td>\\n            <td>left door</td>\\n            <td>white</td>\\n            <td>Fout</td>\\n        </tr>\\n        \\n    </tbody>\\n</table>\\n\\n\\n<p>Hartelijke groeten,</p>\\n\\n<p>Het Coloring Bookteam</p>'

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
                        "correct": "Goed" if is_fill_correct(fill) else "Fout",
                    }
                )

        batch_results.append(
            {
                "subject_name": datum["subject"]["name"],
                "subject_dob": datum["subject"]["birth"],
                "evaluations": evaluations,
            }
        )

    template_context = {"survey_name": survey.name, "batch_results": batch_results}

    html_body = render_template("email/email.html", context=template_context)

    # Only for testing purposes.
    if immediate is True:
        send_async_email(message_subject, recipient, html_body)

    send_async_email.delay(message_subject, recipient, html_body)


@shared_task(bind=True, max_retries=3)
def send_async_email(self, subject, recipient, html):
    message = Message(subject=subject, recipients=[recipient], html=html)

    try:
        mail_client.send(message)
    except OperationalError as exc:
        raise self.retry(exc=exc)
