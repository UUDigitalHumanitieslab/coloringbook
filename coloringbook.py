from flask import Flask, render_template, request, json
app = Flask(__name__)

@app.route('/')
def index():
    return render_template('coloringbook.html')

@app.route('/submit', methods=['POST'])
def submit():
    return json.dumps(request.get_json())

if __name__ == '__main__':
    app.run(debug=True)
