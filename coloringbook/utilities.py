from datetime import date
from flask import current_app
from .models import *


MAX_AGE_TOLERANCE = 36524  # approx. number of days in 100 years


def get_survey_pages(survey):
    """Returns all pages that are associated with a survey."""
    return (
        Page.query.join(*Page.surveys.attr)
        .filter(Survey.id == survey.id)
        .order_by(SurveyPage.ordering)
        .all()
    )


def subject_from_json(data):
    """
    Take personal information from JSON and put into relational object.

    `data` contains the object from the 'subject' key in the
    request data sent from the JavaScript frontend. The return
    value is a Subject as defined in .models. The subject is not
    yet added to the database. Consider the following example code:

    >>> import coloringbook.testing as t
    >>> import json
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
    >>> testoutput.birth
    datetime.date(2000, 1, 1)
    >>> testoutput.name
    u'Bob'
    >>> len(testoutput.languages)
    2
    >>> testoutput.subject_languages[0].language.name
    u'German'
    >>> testoutput.subject_languages[1].level
    1
    """

    if not data["name"]:
        raise ValueError("Name must be non-empty")
    if not data["birth"]:
        raise ValueError("Birth date must be non-empty")
    if not data["languages"]:
        raise ValueError("Native language must be set")
    birth_date = date(*map(int, data["birth"].split("-")))
    today = date.today()
    current_age = today - birth_date
    if current_age.days > MAX_AGE_TOLERANCE:
        raise ValueError("Age greater than maximum tolerance")
    if current_age.days < 0:
        raise ValueError("Negative age")

    subject = Subject(
        name=data["name"],
        numeral=int(data["numeral"]) if "numeral" in data and data["numeral"] else None,
        birth=birth_date,
        eyesight=data["eyesight"],
    )

    for name, level in data["languages"]:
        if not name:
            raise ValueError("Incomplete language data")
        language = Language.query.filter_by(name=name).first()
        if language == None:
            language = Language(name=name)
        SubjectLanguage(subject=subject, language=language, level=level)

    return subject


def actions_from_json(survey, page, subject, data):
    """
    Take actions from JSON and put into [relational object].

    `survey`, `page` and `subject` must be pre-instantiated
    objects of the respective models. `data` is a parsed JSON
    object containing one item from the 'results' key in the
    request data sent from the JavaScript frontend. The Colors and
    Areas referred to from the `data` must already exist in the
    database, otherwise a NoResultFound exception will be thrown.
    Example:

    >>> import coloringbook as cb, flask, datetime, coloringbook.testing
    >>> import coloringbook.models as m
    >>> app = coloringbook.testing.get_fixture_app()
    >>> # some trivial contents for the database
    >>> testdrawing = cb.models.Drawing(name='picture')
    >>> testdrawing.areas.append(cb.models.Area(name='left door'))
    >>> testdrawing.areas.append(cb.models.Area(name='right door'))
    >>> testpage = cb.models.Page(name='page1', drawing=testdrawing, text='test 123')
    >>> testwelcome = m.WelcomeText(name='a', content='a')
    >>> testprivacy = m.PrivacyText(name='a', content='a')
    >>> testsuccess = m.SuccessText(name='a', content='a')
    >>> testinstruction = m.InstructionText(name='a', content='a')
    >>> teststartform = m.StartingForm(name='a', name_label='a', birth_label='a', eyesight_label='a', language_label='a')
    >>> testendform = m.EndingForm(name='a', introduction='a', difficulty_label='a', topic_label='a', comments_label='a')
    >>> testbuttonset = m.ButtonSet(name='a', post_instruction_button='a', post_page_button='a', post_survey_button='a', page_back_button='a')
    >>> testsurvey = cb.models.Survey(name='test', simultaneous=False, welcome_text=testwelcome, privacy_text=testprivacy, success_text=testsuccess, instruction_text=testinstruction, starting_form=teststartform, ending_form=testendform, button_set=testbuttonset)
    >>> testsubject = cb.models.Subject(name='Bob', birth=datetime.date(2000, 1, 1))
    >>> # the to be added new contents for the database
    >>> testdata = '''[
    ...     {
    ...         "action": "fill",
    ...         "color": "#000",
    ...         "target": "left door",
    ...         "time": 1000
    ...     },
    ...     {
    ...         "action": "fill",
    ...         "color": "#fff",
    ...         "target": "left door",
    ...         "time": 2000
    ...     },
    ...     {
    ...         "action": "fill",
    ...         "color": "#000",
    ...         "target": "right door",
    ...         "time": 3000
    ...     },
    ...     {
    ...         "action": "resume",
    ...         "time": 4000
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
    ...     testoutput = actions_from_json(testsurvey, testpage, testsubject, testinput)
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
    >>> testoutput[3].action == 'resume'
    True
    >>> testoutput[4]
    Traceback (most recent call last):
    ...
    IndexError: list index out of range
    """

    colors = Color.query
    areas = Area.query.filter_by(drawing=page.drawing)
    actions = []
    for actnum, datum in enumerate(data):
        try:
            if datum["action"] == "fill":
                actions.append(
                    Fill(
                        survey=survey,
                        page=page,
                        area=areas.filter_by(name=datum["target"]).one(),
                        subject=subject,
                        time=int(datum["time"]),
                        color=colors.filter_by(code=datum["color"]).one(),
                    )
                )
            else:
                actions.append(
                    Action(
                        survey=survey,
                        page=page,
                        subject=subject,
                        time=int(datum["time"]),
                        action=datum["action"],
                    )
                )
        except:
            current_app.logger.error(
                "Next exception thrown in action {} of the current page".format(
                    actnum,
                ),
            )
            raise
    return actions


def evaluate_page_actions(actions, page):
    """
    Evaluates the actions on a page.

    Expects a list of fills (which may be empty) and returns a dictionary containing `page_name`, `target`, `color` and a `correct` score. These values are determined as follows.

    - If the page is skipped (no fills), the correct score is `0`.
    - If the page has a single fill, a correct score of `1` is returned if the target of the fill is the same as the expected target. (The color does not matter.) Else, the correct score will be `0`.
    - If the page has multiple fills, a correct score of `1` is returned if one of them has a target that is identical to the expected target. Else, this function returns a correct score of `0`.

    >>> import coloringbook as cb, flask, datetime, coloringbook.testing
    >>> import coloringbook.models as m
    >>> app = coloringbook.testing.get_fixture_app()

    # Areas
    >>> correct_area = m.Area(name='elephant')
    >>> incorrect_area = m.Area(name='dog')
    >>> extra_area = m.Area(name='fish')

    # Drawing and page
    >>> test_drawing = m.Drawing(name='picture')
    >>> test_drawing.areas.append(correct_area)
    >>> test_drawing.areas.append(incorrect_area)
    >>> test_drawing.areas.append(extra_area)

    >>> test_page_1 = m.Page(name='page1', drawing=test_drawing, text='test page 1')
    >>> test_page_2 = m.Page(name='page2', drawing=test_drawing, text='test page 2')

    # Colors
    >>> correct_color = m.Color(code='#000', name='black')
    >>> incorrect_color = m.Color(code='#fff', name='white')

    # Expectations (in practice there is only one expectation per page; we test multiple for the sake of completeness.)
    >>> test_exp_1 = m.Expectation(area=correct_area, here=True, page=test_page_1, color=correct_color)
    >>> test_exp_2 = m.Expectation(area=correct_area, here=True, page=test_page_2, color=correct_color)

    # Survey
    >>> testwelcome = m.WelcomeText(name='a', content='a')
    >>> testprivacy = m.PrivacyText(name='a', content='a')
    >>> testsuccess = m.SuccessText(name='a', content='a')
    >>> testinstruction = m.InstructionText(name='a', content='a')
    >>> teststartform = m.StartingForm(name='a', name_label='a', birth_label='a', eyesight_label='a', language_label='a')
    >>> testendform = m.EndingForm(name='a', introduction='a', difficulty_label='a', topic_label='a', comments_label='a')
    >>> testbuttonset = m.ButtonSet(name='a', post_instruction_button='a', post_page_button='a', post_survey_button='a', page_back_button='a')
    >>> testsurvey = cb.models.Survey(name='test', simultaneous=False, welcome_text=testwelcome, privacy_text=testprivacy, success_text=testsuccess, instruction_text=testinstruction, starting_form=teststartform, ending_form=testendform, button_set=testbuttonset)

    # Subject
    >>> testsubject = cb.models.Subject(name='Bob', birth=datetime.date(2000, 1, 1))

    # Fills
    >>> correct_area_correct_color = m.Fill(area=correct_area, color=correct_color, survey=testsurvey, page=test_page_1, subject=testsubject, time=1000)
    >>> incorrect_area_correct_color_1 = m.Fill(area=incorrect_area, color=correct_color, survey=testsurvey, page=test_page_1, subject=testsubject, time=1000)
    >>> incorrect_area_correct_color_2 = m.Fill(area=extra_area, color=correct_color, survey=testsurvey, page=test_page_2, subject=testsubject, time=1000)
    >>> incorrect_area_incorrect_color = m.Fill(area=incorrect_area, color=incorrect_color, survey=testsurvey, page=test_page_2, subject=testsubject, time=1000)

    # Non-fill action (resume)
    >>> resume_action = m.Action(action='resume', survey=testsurvey, page=test_page_1, subject=testsubject, time=5000)

    >>> with app.app_context():
    ...     # make sure the pre-existing data are persistent
    ...     s = cb.models.db.session
    ...     s.add(correct_area)
    ...     s.add(incorrect_area)
    ...     s.add(extra_area)
    ...     s.add(test_exp_1)
    ...     s.add(test_exp_2)
    ...     s.commit()
    ...     s.flush()
    ...     no_fills = evaluate_page_actions([], test_page_1)
    ...     one_fill_correct = evaluate_page_actions([correct_area_correct_color], test_page_1)
    ...     one_fill_incorrect = evaluate_page_actions([incorrect_area_correct_color_1], test_page_1)
    ...     multiple_fills_incorrect = evaluate_page_actions([incorrect_area_correct_color_1, incorrect_area_correct_color_2], test_page_2)
    ...     multiple_fills_mixed_correct = evaluate_page_actions([correct_area_correct_color, incorrect_area_incorrect_color], test_page_1)
    ...     correct_and_non_fills = evaluate_page_actions([correct_area_correct_color, resume_action], test_page_1)
    ...     incorrect_and_non_fills = evaluate_page_actions([incorrect_area_correct_color_1, resume_action], test_page_1)

    >>> no_fills['correct']
    0
    >>> no_fills['page']
    u'page1'
    >>> no_fills['target']
    '-'
    >>> no_fills['color']
    '-'

    >>> one_fill_correct['correct']
    1
    >>> one_fill_correct['page']
    u'page1'
    >>> one_fill_correct['target']
    u'elephant'
    >>> one_fill_correct['color']
    u'black'

    >>> one_fill_incorrect['correct']
    0
    >>> one_fill_incorrect['page']
    u'page1'
    >>> one_fill_incorrect['target']
    u'dog'
    >>> one_fill_incorrect['color']
    u'black'

    >>> multiple_fills_incorrect['correct']
    0
    >>> multiple_fills_incorrect['page']
    u'page2'
    >>> multiple_fills_incorrect['target']
    u'dog, fish'
    >>> multiple_fills_incorrect['color']
    u'black, black'

    >>> multiple_fills_mixed_correct['correct']
    1
    >>> multiple_fills_mixed_correct['page']
    u'page1'
    >>> multiple_fills_mixed_correct['target']
    u'elephant'
    >>> multiple_fills_mixed_correct['color']
    u'black'

    >>> correct_and_non_fills['correct']
    1
    >>> correct_and_non_fills['page']
    u'page1'
    >>> correct_and_non_fills['target']
    u'elephant'
    >>> correct_and_non_fills['color']
    u'black'

    >>> incorrect_and_non_fills['correct']
    0
    >>> incorrect_and_non_fills['page']
    u'page1'
    >>> incorrect_and_non_fills['target']
    u'dog'
    >>> incorrect_and_non_fills['color']
    u'black'
    """

    # User skipped the page.
    if len(actions) == 0:
        return {
            "page": page.name,
            "target": "-",
            "color": "-",
            "correct": 0,
        }

    for action in actions:
        # If the action does not have an area property, it is not a fill.
        # We skip it.
        if not hasattr(action, "area"):
            continue
        for expectation in page.expectations:
            if action.area.id == expectation.area.id:
                return {
                    "page": page.name,
                    "target": action.area.name,
                    "color": action.color.name,
                    "correct": 1,
                }

    # User filled in the wrong area, or there are only non-fill actions.
    targets = []
    colors = []
    for action in actions:
        if hasattr(action, "area"):
            targets.append(action.area.name)
            colors.append(action.color.name)
    return {
        "page": page.name,
        "target": ', '.join(targets),
        "color": ', '.join(colors),
        "correct": 0,
    }
