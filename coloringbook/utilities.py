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


def is_fill_correct(fill):
    actual_color = fill.color
    expectation = Expectation.query.filter_by(
        page=fill.page,
        area=fill.area,
    )
    if expectation.count() == 0:
        return False
    expected_color = expectation.one().color
    return actual_color == expected_color
