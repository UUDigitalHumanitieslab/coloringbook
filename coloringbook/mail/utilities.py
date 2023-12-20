from celery import shared_task
from flask import current_app, render_template
from coloringbook.mail import mail_client
from flask_mail import Message

from coloringbook.utilities import (
    fills_from_json,
    subject_from_json,
    get_survey_pages,
    is_fill_correct,
)


def send_email(recipient, survey_data, survey):
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

    send_async_email.delay(message_subject, recipient, html_body)


@shared_task
def send_async_email(subject, recipient, html_body):
    message = Message(
        subject=subject,
        recipients=[recipient],
        html=html_body,
    )

    mail_client.send(message)
