# (c) 2014-2023 Research Software Lab, Centre for Digital Humanities, Utrecht University
# Licensed under the EUPL-1.2 or later. You may obtain a copy of the license at
# https://joinup.ec.europa.eu/collection/eupl/eupl-text-eupl-12.

"""
    Object relational model and database schema.

    An organogram will be provided as external documentation of the
    database structure.
"""

import flask.ext.sqlalchemy as fsqla
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.declarative import declared_attr


PAGE_NAME_CHAR_LIMIT = 100  # maximum length of a Page name
SURVEY_NAME_CHAR_LIMIT = 100 # maximum length of a Survey name

def TableArgsMeta(parent_class, table_args):
    """
        Metaclass generator to set global defaults for __table_args__.

        See
        http://stackoverflow.com/questions/25770701/how-to-tell-sqlalchemy-once-that-i-want-innodb-for-the-entire-database
        for an explanation.
    """

    class _TableArgsMeta(parent_class):

        def __init__(cls, name, bases, dict_):
            if (    # Do not extend base class
                    '_decl_class_registry' not in cls.__dict__ and
                    # Missing __tablename_ or equal to None means single table
                    # inheritance -- no table for it (columns go to table of
                    # base class)
                    cls.__dict__.get('__tablename__') and
                    # Abstract class -- no table for it (columns go to table[s]
                    # of subclass[es]
                    not cls.__dict__.get('__abstract__', False)):
                ta = getattr(cls, '__table_args__', {})
                if isinstance(ta, dict):
                    ta = dict(table_args, **ta)
                    cls.__table_args__ = ta
                else:
                    assert isinstance(ta, tuple)
                    if ta and isinstance(ta[-1], dict):
                        tad = dict(table_args, **ta[-1])
                        ta = ta[:-1]
                    else:
                        tad = dict(table_args)
                    cls.__table_args__ = ta + (tad,)
            super(_TableArgsMeta, cls).__init__(name, bases, dict_)

    return _TableArgsMeta


class InnoDBSQLAlchemy(fsqla.SQLAlchemy):
    """ Subclass in order to enable TableArgsMeta. """
    def make_declarative_base(self, metadata=None):
        """Creates the declarative base."""
        base = fsqla.declarative_base(
            cls = fsqla.Model,
            name = 'Model',
            metadata = metadata,
            metaclass = TableArgsMeta(
                fsqla._BoundDeclarativeMeta,
                {'mysql_engine': 'InnoDB'} ) )
        base.query = fsqla._QueryProperty(self)
        return base

db = InnoDBSQLAlchemy()  # actual database connection is done in __init__.py


class Subject(db.Model):
    """ Personal information of a test person. """

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    numeral = db.Column(db.Integer)  # such as student ID
    birth = db.Column(db.DateTime, nullable=False)
    eyesight = db.Column(db.String(100))  # medical conditions

    languages = association_proxy('subject_languages', 'language')  # many-many
    surveys = association_proxy('subject_surveys', 'survey')  # many-many

    def __str__(self):
        return str(self.id)


class SubjectLanguage(db.Model):
    """ Association between a Subject and a Language they speak. """

    language_id = db.Column(
        db.Integer,
        db.ForeignKey('language.id'),
        primary_key=True,
        nullable=False )
    subject_id = db.Column(
        db.Integer,
        db.ForeignKey('subject.id'),
        primary_key=True,
        nullable=False )
    level = db.Column(db.Integer)  # language skill 1--10 where 10 is native

    subject = db.relationship(  # many-one (facilitates many-many)
        'Subject',
        backref=db.backref(
            'subject_languages',
            cascade='all, delete-orphan'))
    language = db.relationship(  # many-one (facilitates many-many)
        'Language',
        backref=db.backref(
            'language_subjects',
            cascade='all, delete-orphan'))


class Language(db.Model):
    """ Language that may be associated with a Subject, Survey or Page. """

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), nullable=False, unique=True)

    subjects = association_proxy('language_subjects', 'subject')  # many-many

    def __str__(self):
        return self.name


class File(object):
    """ Common members for Drawing and Sound. """

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
                                    # filename *without* extension
                                    # database is path-agnostic

    def __str__(self):
        return self.name


class Drawing(File, db.Model):
    """ Proxy to a colorable SVG. """
    __tablename__ = 'drawing'


class Area(db.Model):
    """ Colorable part of a Drawing. """

    __tablename__ = 'area'
    __table_args__ = (
        db.UniqueConstraint('name', 'drawing_id'),
    )

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(40), nullable=False)
                                        # id of the <path> element in the SVG
    drawing_id = db.Column(
        db.Integer,
        db.ForeignKey('drawing.id'),
        nullable=False )

    drawing = db.relationship(
        'Drawing',
        backref=db.backref('areas', cascade='all, delete-orphan') )
        # many-one

    def __str__(self):
        return self.name


class Sound(File, db.Model):
    """ Proxy to a MP3 file. """
    __tablename__ = 'sound'


class Page(db.Model):
    """ Combination of a sentence and a Drawing. """

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(PAGE_NAME_CHAR_LIMIT), nullable=False)
    language_id = db.Column(db.Integer, db.ForeignKey('language.id'))
    text = db.Column(db.String(200))  # sentence
    sound_id = db.Column(db.Integer, db.ForeignKey('sound.id'))
    drawing_id = db.Column(db.Integer,
        db.ForeignKey('drawing.id'),
        nullable=False )

    language = db.relationship(  # many-one
        'Language',
        backref=db.backref(
            'pages',
            lazy='dynamic'))
    sound = db.relationship(  # many-one
        'Sound',
        backref=db.backref(
            'pages',
            lazy='dynamic'))
    drawing = db.relationship(  # many-one
        'Drawing',
        backref=db.backref(
            'pages',
            lazy='dynamic'))
    expectations = db.relationship('Expectation', backref='page')  # one-many
    surveys = association_proxy('page_surveys', 'survey')  # many-many

    def __str__(self):
        return self.name


class Color(db.Model):
    """ Color that may be associated with a Fill or Expectation. """

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(25), nullable=False)
                                        # RGB code as used at the client side
    name = db.Column(db.String(20), nullable=False)  # mnemonic

    def __str__(self):
        return self.name


class Expectation(db.Model):
    """ Expected Color for a particular Area on a particular Page. """

    page_id = db.Column(
        db.Integer,
        db.ForeignKey('page.id'),
        primary_key=True,
        nullable=False )
    area_id = db.Column(
        db.Integer,
        db.ForeignKey('area.id'),
        primary_key=True,
        nullable=False )
    color_id = db.Column(
        db.Integer,
        db.ForeignKey('color.id'),
        nullable=False )
    here = db.Column(db.Boolean, nullable=False)
                                # if False, color is expected in another area
    motivation = db.Column(db.String(200))

    area = db.relationship('Area', backref='expectations')  # many-one
    color = db.relationship('Color')  # many-one, no backref

    def __repr__(self):
        return '<Expectation {0} {3}in {1}, {2}>'.format(
            self.color,
            self.area,
            self.page,
            '' if self.here else 'not ' )


class Text(object):
    """ Common fields for WelcomeText, PrivacyText, etcetera. """

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), nullable=False, unique=True)
    content = db.Column(db.Text, nullable=False)

    def __str__(self):
        return self.name


class WelcomeText(Text, db.Model):
    """ The welcome message above the subscription form. """
    __tablename__ = 'welcome_text'


class PrivacyText(Text, db.Model):
    """ The privacy statement below the subscription form. """
    __tablename__ = 'privacy_text'


class InstructionText(Text, db.Model):
    """ The instruction text that is shown after subscription. """
    __tablename__ = 'instruction_text'


class SuccessText(Text, db.Model):
    """ The message shown after successful data submission. """
    __tablename__ = 'success_text'


class StartingForm(db.Model):
    """ Customization parameters for display of the initial form. """

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), nullable=False, unique=True)
    name_label = db.Column(db.String(30), nullable=False)
    numeral_label = db.Column(db.String(30))
    birth_label = db.Column(db.String(30), nullable=False)
    birth_placeholder = db.Column(db.String(10), nullable=False, default='yyyy-mm-dd')
    eyesight_label = db.Column(db.String(30), nullable=False)
    eyesight_label_2 = db.Column(db.Text)
    language_label = db.Column(db.String(30), nullable=False)
    language_label_2 = db.Column(db.Text)
    extra_language_label = db.Column(db.String(20))
    extra_language_level_label = db.Column(db.String(20))

    def __str__(self):
        return self.name


class EndingForm(db.Model):
    """ Customization parameters for display of the final form. """

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), nullable=False, unique=True)
    introduction = db.Column(db.Text, nullable=False)
    difficulty_label = db.Column(db.Text, nullable=False)
    topic_label = db.Column(db.Text, nullable=False)
    comments_label = db.Column(db.Text, nullable=False)

    def __str__(self):
        return self.name


class ButtonSet(db.Model):
    """ Customization parameters for the text in some of the buttons. """

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), nullable=False, unique=True)
    post_instruction_button = db.Column(db.String(30), nullable=False)
    post_page_button = db.Column(db.String(30), nullable=False)
    page_back_button = db.Column(db.String(30), nullable=False)
    post_survey_button = db.Column(db.String(40), nullable=False)

    def __str__(self):
        return self.name


class Survey(db.Model):
    """ Prepared series of Pages that is presented to Subjects. """

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(SURVEY_NAME_CHAR_LIMIT), nullable=False, unique=True)
    language_id = db.Column(db.Integer, db.ForeignKey('language.id'))
    begin = db.Column(db.DateTime)
    end = db.Column(db.DateTime)
    duration = db.Column(db.Integer, nullable=False, default=6000)
    simultaneous = db.Column(db.Boolean, nullable=False)
    information = db.Column(db.Text)
    email_address = db.Column(db.String(60))
    language = db.relationship('Language', backref='surveys')  # many-one
    pages = association_proxy('survey_pages', 'page')  # many-many
    subjects = association_proxy('survey_subjects', 'subject')  # many-many

    # Customizable text and forms
    title = db.Column(db.String(100), nullable=False, default='Coloring Book')
    welcome_text_id = db.Column(
        db.Integer,
        db.ForeignKey('welcome_text.id'),
        nullable=False )
    starting_form_id = db.Column(
        db.Integer,
        db.ForeignKey('starting_form.id'),
        nullable=False )
    privacy_text_id = db.Column(
        db.Integer,
        db.ForeignKey('privacy_text.id'),
        nullable=False )
    instruction_text_id = db.Column(
        db.Integer,
        db.ForeignKey('instruction_text.id'),
        nullable=False )
    ending_form_id = db.Column(
        db.Integer,
        db.ForeignKey('ending_form.id'),
        nullable=False )
    success_text_id = db.Column(
        db.Integer,
        db.ForeignKey('success_text.id'),
        nullable=False )
    button_set_id = db.Column(
        db.Integer,
        db.ForeignKey('button_set.id'),
        nullable=False )

    welcome_text = db.relationship('WelcomeText')
    starting_form = db.relationship('StartingForm')
    privacy_text = db.relationship('PrivacyText')
    instruction_text = db.relationship('InstructionText')
    ending_form = db.relationship('EndingForm')
    success_text = db.relationship('SuccessText')
    button_set = db.relationship('ButtonSet')

    def __str__(self):
        return self.name


class SurveySubject(db.Model):
    """ Participation of a Subject in a Survey, with evaluation data. """

    # association
    survey_id = db.Column(db.ForeignKey('survey.id'), primary_key=True)
    subject_id = db.Column(db.ForeignKey('subject.id'), primary_key=True)
    # evaluation
    difficulty = db.Column(db.Integer)
    topic = db.Column(db.String(60))
    comments = db.Column(db.Text)

    # two many-one relationships, both of which facilitate many-many
    survey = db.relationship('Survey', backref=db.backref(
        'survey_subjects',
        cascade='all, delete-orphan' ))
    subject = db.relationship('Subject', backref=db.backref(
        'subject_surveys',
        cascade='all, delete-orphan' ))


class SurveyPage(db.Model):
    """ Association between a Survey and a Page that is part of it. """

    survey_id = db.Column(
        db.Integer,
        db.ForeignKey('survey.id'),
        primary_key=True,
        nullable=False )
    page_id = db.Column(
        db.Integer,
        db.ForeignKey('page.id'),
        primary_key=True,
        nullable=False )
    ordering = db.Column(db.Integer, nullable=False)  # Nth page of a survey

    survey = db.relationship(  # many-one (facilitates many-many)
        'Survey',
        backref=db.backref(
            'survey_pages',
            cascade='all, delete-orphan'))
    page = db.relationship(  # many-one (facilitates many-many)
        'Page',
        backref=db.backref(
            'page_surveys',
            cascade='all, delete-orphan'))


class Action(db.Model):
    """ General container for actions without additional data. """

    survey_id = db.Column(
        db.Integer,
        db.ForeignKey('survey.id'),
        primary_key=True,
        nullable=False,
    )
    page_id = db.Column(
        db.Integer,
        db.ForeignKey('page.id'),
        primary_key=True,
        nullable=False,
    )
    subject_id = db.Column(
        db.Integer,
        db.ForeignKey('subject.id'),
        primary_key=True,
        nullable=False,
    )
    time = db.Column(  # msecs from page start
        db.Integer,
        primary_key=True,
        autoincrement=False,
        nullable=False,
    )
    action = db.Column(db.String(30), nullable=False)

    survey = db.relationship(  # many-one
        'Survey',
        backref=db.backref('actions', lazy='dynamic'),
    )
    page = db.relationship(  # many-one
        'Page',
        backref=db.backref('actions', lazy='dynamic'),
    )
    subject = db.relationship(  # many-one
        'Subject',
        backref=db.backref('actions', lazy='dynamic'),
    )


class Fill(db.Model):
    """ The Color a Subject filled an Area of a Page in a Survey with at #ms."""

    survey_id = db.Column(
        db.Integer,
        db.ForeignKey('survey.id'),
        primary_key=True,
        nullable=False )
    page_id = db.Column(
        db.Integer,
        db.ForeignKey('page.id'),
        primary_key=True,
        nullable=False )
    area_id = db.Column(
        db.Integer,
        db.ForeignKey('area.id'),
        primary_key=True,
        nullable=False )
    subject_id = db.Column(
        db.Integer,
        db.ForeignKey('subject.id'),
        primary_key=True,
        nullable=False )
    time = db.Column(  # msecs from page start
        db.Integer,
        primary_key=True,
        autoincrement=False,
        nullable=False )
    color_id = db.Column(
        db.Integer,
        db.ForeignKey('color.id'),
        nullable=False )

    survey = db.relationship(  # many-one
        'Survey',
        backref=db.backref('fills', lazy='dynamic') )
    page = db.relationship(  # many-one
        'Page',
        backref=db.backref('fills', lazy='dynamic') )
    area = db.relationship(  # many-one
        'Area',
        backref=db.backref('fills', lazy='dynamic') )
    subject = db.relationship(  # many-one
        'Subject',
        backref=db.backref('fills', lazy='dynamic') )
    color = db.relationship('Color')  # many-one, no backref

    def __repr__(self):
        return '<Fill {0} with {1} after {5} ms by {2} at {3} of {4}>'.format(
            self.area,
            self.color,
            self.subject,
            self.page,
            self.survey,
            self.time)
