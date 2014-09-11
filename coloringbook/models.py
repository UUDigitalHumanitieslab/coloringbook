# (c) 2014 Digital Humanities Lab, Faculty of Humanities, Utrecht University
# Author: Julian Gonggrijp, j.gonggrijp@uu.nl

"""
    Object relational model and database schema.
    
    An organogram will be provided as external documentation of the
    database structure.
"""

from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy.ext.associationproxy import association_proxy

__all__ = [
    'db',
    'Subject',
    'SubjectLanguage',
    'Language',
    'Drawing',
    'Area',
    'Page',
    'Color',
    'Expectation',
    'Survey',
    'SurveyPage',
    'Fill'              ]

db = SQLAlchemy()  # actual database connection is done in __init__.py

class Subject (db.Model):
    """ Personal information of a test person. """
    
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(50), nullable = False)
    numeral = db.Column(db.Integer)  # such as student ID
    birth = db.Column(db.DateTime, nullable = False)
    eyesight = db.Column(db.String(100))  # medical conditions
    
    languages = association_proxy('subject_languages', 'language')  # many-many
    
    def __str__ (self):
        return str(self.id)

class SubjectLanguage (db.Model):
    """ Association between a Subject and a Language they speak. """
    
    language_id = db.Column(
        db.Integer,
        db.ForeignKey('language.id'),
        primary_key = True,
        nullable = False )
    subject_id = db.Column(
        db.Integer,
        db.ForeignKey('subject.id'),
        primary_key = True,
        nullable = False )
    level = db.Column(db.Integer)  # language skill 1--10 where 10 is native
    
    subject = db.relationship(  # many-one (facilitates many-many)
        'Subject',
        backref = db.backref(
            'subject_languages',
            cascade = 'all, delete-orphan'))
    language = db.relationship(  # many-one (facilitates many-many)
        'Language',
        backref = db.backref(
            'language_subjects',
            cascade = 'all, delete-orphan'))

class Language (db.Model):
    """ Language that may be associated with a Subject, Survey or Page. """

    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(30), nullable = False, unique = True)
    
    subjects = association_proxy('language_subjects', 'subject')  # many-many
    
    def __str__ (self):
        return self.name

class File (object):
    """ Common members for Drawing and Sound. """
    
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(30), nullable = False, unique = True)
                                     # filename *without* extension
                                     # database is path-agnostic
    
    def __str__ (self):
        return self.name

class Drawing (File, db.Model):
    """ Proxy to a colorable SVG. """
    pass

class Area (db.Model):
    """ Colorable part of a Drawing. """
    
    __tablename__ = 'area'
    __table_args__ = (
        db.UniqueConstraint('name', 'drawing_id'),
    )

    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(20), nullable = False)
                                        # id of the <path> element in the SVG
    drawing_id = db.Column(
        db.Integer,
        db.ForeignKey('drawing.id'),
        nullable = False )
    
    drawing = db.relationship(
        'Drawing',
        backref= db.backref('areas', cascade = 'all, delete-orphan') )
        # many-one
    
    def __str__ (self):
        return self.name

class Sound (File, db.Model):
    """ Proxy to a MP3 file. """
    pass

class Page (db.Model):
    """ Combination of a sentence and a Drawing. """

    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(30), nullable = False)
    language_id = db.Column(db.Integer, db.ForeignKey('language.id'))
    text = db.Column(db.String(200))  # sentence
    sound_id = db.Column(db.Integer, db.ForeignKey('sound.id'))
    drawing_id = db.Column(db.Integer,
        db.ForeignKey('drawing.id'),
        nullable = False )
    
    language = db.relationship(  # many-one
        'Language',
        backref = db.backref(
            'pages',
            lazy = 'dynamic'))
    sound = db.relationship(  # many-one
        'Sound',
        backref = db.backref(
            'pages',
            lazy = 'dynamic'))
    drawing = db.relationship(  # many-one
        'Drawing',
        backref = db.backref(
            'pages',
            lazy = 'dynamic'))
    expectations = db.relationship('Expectation', backref = 'page')  # one-many
    surveys = association_proxy('page_surveys', 'survey')  # many-many
    
    def __str__ (self):
        return self.name

class Color (db.Model):
    """ Color that may be associated with a Fill or Expectation. """

    id = db.Column(db.Integer, primary_key = True)
    code = db.Column(db.String(25), nullable = False)
                                        # RGB code as used at the client side
    name = db.Column(db.String(20), nullable = False)  # mnemonic
    
    def __str__ (self):
        return self.code

class Expectation (db.Model):
    """ Expected Color for a particular Area on a particular Page. """

    page_id = db.Column(
        db.Integer,
        db.ForeignKey('page.id'),
        primary_key = True,
        nullable = False )
    area_id = db.Column(
        db.Integer,
        db.ForeignKey('area.id'),
        primary_key = True,
        nullable = False )
    color_id = db.Column(
        db.Integer,
        db.ForeignKey('color.id'),
        nullable = False )
    here = db.Column(db.Boolean, nullable = False)
                                # if False, color is expected in another area
    motivation = db.Column(db.String(200))
    
    area = db.relationship('Area', backref = 'expectations')  # many-one
    color = db.relationship('Color')  # many-one, no backref
    
    def __repr__ (self):
        return '<Expectation {0} {3}in {1}, {2}>'.format(
            self.color,
            self.area,
            self.page,
            '' if self.here else 'not ' )

survey_subject = db.Table(
    'survey_subject',
    db.Column(
        'survey_id',
        db.Integer,
        db.ForeignKey('survey.id'),
        primary_key = True,
        nullable = False ),
    db.Column(
        'subject_id',
        db.Integer,
        db.ForeignKey('subject.id'),
        primary_key = True,
        nullable = False ) )

class Survey (db.Model):
    """ Prepared series of Pages that is presented to Subjects. """
    
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(40), nullable = False, unique = True)
    language_id = db.Column(db.Integer, db.ForeignKey('language.id'))
    begin = db.Column(db.DateTime)
    end = db.Column(db.DateTime)
    information = db.Column(db.String(500))
    
    language = db.relationship('Language', backref = 'surveys')  # many-one
    pages = association_proxy('survey_pages', 'page')  # many-many
    subjects = db.relationship(  # many-many
        'Subject',
        secondary = survey_subject,
        backref = db.backref('surveys', lazy = 'dynamic') )
    
    def __str__ (self):
        return self.name

class SurveyPage (db.Model):
    """ Association between a Survey and a Page that is part of it. """
    
    survey_id = db.Column(
        db.Integer,
        db.ForeignKey('survey.id'),
        primary_key = True,
        nullable = False )
    page_id = db.Column(
        db.Integer,
        db.ForeignKey('page.id'),
        primary_key = True,
        nullable = False )
    ordering = db.Column(db.Integer, nullable = False)  # Nth page of a survey
    
    survey = db.relationship(  # many-one (facilitates many-many)
        'Survey',
        backref = db.backref(
            'survey_pages',
            cascade = 'all, delete-orphan'))
    page = db.relationship(  # many-one (facilitates many-many)
        'Page',
        backref = db.backref(
            'page_surveys',
            cascade = 'all, delete-orphan'))

class Fill (db.Model):
    """ The Color a Subject filled an Area of a Page in a Survey with at #ms."""
    
    survey_id = db.Column(
        db.Integer,
        db.ForeignKey('survey.id'),
        primary_key = True,
        nullable = False )
    page_id = db.Column(
        db.Integer,
        db.ForeignKey('page.id'),
        primary_key = True,
        nullable = False )
    area_id = db.Column(
        db.Integer,
        db.ForeignKey('area.id'),
        primary_key = True,
        nullable = False )
    subject_id = db.Column(
        db.Integer,
        db.ForeignKey('subject.id'),
        primary_key = True,
        nullable = False )
    time = db.Column(  # msecs from page start
        db.Integer,
        primary_key = True,
        autoincrement = False,
        nullable = False )
    color_id = db.Column(
        db.Integer,
        db.ForeignKey('color.id'),
        nullable = False )
    
    survey = db.relationship(  # many-one
        'Survey',
        backref = db.backref('fills', lazy = 'dynamic') )
    page = db.relationship(  # many-one
        'Page',
        backref = db.backref('fills', lazy = 'dynamic') )
    area = db.relationship(  # many-one
        'Area',
        backref = db.backref('fills', lazy = 'dynamic') )
    subject = db.relationship(  # many-one
        'Subject',
        backref = db.backref('fills', lazy = 'dynamic') )
    color = db.relationship('Color')  # many-one, no backref
    
    def __repr__ (self):
        return '<Fill {0} with {1} after {5} ms by {2} at {3} of {4}>'.format(
            self.area,
            self.color,
            self.subject,
            self.page,
            self.survey,
            self.time)
