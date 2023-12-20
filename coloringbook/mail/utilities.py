from flask import current_app, render_template

from coloringbook.utilities import (
    fills_from_json,
    subject_from_json,
    get_survey_pages,
    is_fill_correct,
)


def send_email(recipients, survey_data, survey):
    current_app.logger.info("Sending email!")

    sender = current_app.config["MAIL_DEFAULT_SENDER"]
    message_subject = "ColoringBook - nieuwe resultaten opgeslagen"

    batch_results = []
    # Every datum is a subject.
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
                        "correct": "Ja" if is_fill_correct(fill) else "Nee",
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

    current_app.logger.info("Html template: {}".format(html_body))

    send_async_email.delay(message_subject, sender, recipients, html_body)
