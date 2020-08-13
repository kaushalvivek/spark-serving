'''
What this app does:
- accepts models as tar/gz files from webserver
- upzips models
- converts models to PMML using JPMML
- serves models on openscoring
- provides REST API URL
'''
import os
from flask import Flask,flash, render_template,abort, url_for, redirect, request, jsonify
from werkzeug.utils import secure_filename
from flask import send_from_directory


CLIENT_EXECUTABLE_PATH = "openscoring/openscoring-client/target/openscoring-client-executable-2.0-SNAPSHOT.jar"
ALLOWED_EXTENSIONS = {'db', 'zip', 'tar', 'gz'}
UPLOAD_FOLDER="./models"

# initializing the App and database
app = Flask(__name__)
app.secret_key = b'_5#y2L"FfasfsdQ8z\n\xec]/'

app.config.from_object(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['ALLOWED_EXTENSIONS'] = ALLOWED_EXTENSIONS
app.config['CLIENT_EXECUTABLE_PATH'] = CLIENT_EXECUTABLE_PATH
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return ("service is successfully hosted")

@app.route('/model_upload/<filename>', methods=['POST'])
def model_upload(filename):
    # if request not empty
    filename = secure_filename(filename)
    if request.data != "" and allowed_file(filename):
        with open(os.path.join(UPLOAD_FOLDER, filename), "wb") as fp:
            fp.write(request.data)
        # Return 201 CREATED
        return "", 201
    else:
        abort(400, "invalid upload")

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)

if __name__ == "__main__":
    app.run(debug=True)