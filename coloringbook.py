from flask import Flask, render_template, request, json
from flask.ext.sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://coloringbook@localhost/coloringbook'
db = SQLAlchemy(app)

class Subject (db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(100))
    numeral = db.Column(db.Integer)
    birth = db.Column(db.DateTime)
    eyesight = db.Column(db.String(100))
    
    languages = db.relationship(
        'Language',
        secondary = 'lang_bindings',
        backref = db.backref('subjects')
    )
    
    def __repr__ (self):
        return '<Subject {0} born {1}>'.format(self.name, self.birth_date)

@app.route('/')
def index():
    return render_template('coloringbook.html')

@app.route('/submit', methods=['POST'])
def submit():
    return json.dumps(request.get_json())

if __name__ == '__main__':
    app.run(debug=True)
