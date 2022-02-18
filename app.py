from flask import Flask, render_template, request
from translate.translate import translate

app = Flask(__name__)

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/sql', methods=['POST'])
def sql():
    sql = request.get_json()['sql']
    return {'result': translate(sql)}

if __name__ == '__main__':
    app.debug = True
    app.run()