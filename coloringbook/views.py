from flask import Blueprint, render_template, request, json

from .models import db

site = Blueprint('site', __name__)

@site.route('/')
def index():
    return render_template('coloringbook.html')

@site.route('/submit', methods=['POST'])
def submit():
    return json.dumps(request.get_json())
