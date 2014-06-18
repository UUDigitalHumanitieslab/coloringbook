from flask import Flask, render_template, request, json
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy.ext.associationproxy import association_proxy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://coloringbook@localhost/coloringbook'
db = SQLAlchemy(app)


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
    name = db.Column(db.String(15))
    
    def __repr__ (self):
        return '<Language {}>'.format(self.name)


@app.route('/')
def index():
    return render_template('coloringbook.html')

@app.route('/submit', methods=['POST'])
def submit():
    return json.dumps(request.get_json())

if __name__ == '__main__':
    app.run(debug=True)
