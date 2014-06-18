from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy.ext.associationproxy import association_proxy

db = SQLAlchemy()

class Subject (db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(100))
    numeral = db.Column(db.Integer)
    birth = db.Column(db.DateTime)
    eyesight = db.Column(db.String(100))
    
    languages = association_proxy('subject_languages', 'language')
    
    def __repr__ (self):
        return '<Subject {0} born {1}>'.format(self.name, self.birth_date)

class SubjectLanguage (db.Model):
    language_id = db.Column(
        db.Integer,
        db.ForeignKey('language.id'),
        primary_key = True
    )
    subject_id = db.Column(
        db.Integer,
        db.ForeignKey('subject.id'),
        primary_key = True
    )
    level = db.Column(db.Integer)
    
    subject = db.relationship(
        'Subject',
        backref = db.backref(
            'subject_languages',
            cascade = 'all, delete-orphan'
        )
    )
    language = db.relationship(
        'Language',
        backref = db.backref(
            'language_subjects',
            cascade = 'all, delete-orphan'
        )
    )

class Language (db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(30))
    
    def __repr__ (self):
        return '<Language {}>'.format(self.name)

class Drawing (db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(30))
    
    areas = db.relationship('Area', backref = 'drawing', lazy = 'dynamic')
    
    def __repr__ (self):
        return '<Drawing {}>'.format(self.name)

class Area (db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(20))
    drawing_id = db.Column(db.Integer, db.ForeignKey('drawing.id'))
    
    def __repr__ (self):
        return '<Area {0} in {1}>'.format(self.name, self.drawing)

class Page (db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(30))
    language_id = db.Column(db.Integer, db.ForeignKey('language.id'))
    text = db.Column(db.String(200))
    sound = db.Column(db.String(30))
    drawing_id = db.Column(db.Integer, db.ForeignKey('drawing.id'))
    
    language = db.relationship(
        'Language',
        backref = db.backref(
            'pages',
            lazy = 'dynamic'))
    drawing = db.relationship(
        'Drawing',
        backref = db.backref(
            'pages',
            lazy = 'dynamic'))
    expectations = db.relationship('Expectation', backref = 'page')
    
    def __repr__ (self):
        return '<Page {0} with {1}, {2}>'.format(
            self.name,
            self.drawing,
            self.language)

class Color (db.Model):
    id = db.Column(db.Integer, primary_key = True)
    code = db.Column(db.String(25))
    name = db.Column(db.String(20))
    
    def __repr__ (self):
        return '<Color {0} "{1}">'.format(self.code, self.name)
