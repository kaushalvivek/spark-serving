'''
What this app does:
- accepts models as tar/gz files from webserver
- upzips models
- converts models to PMML using JPMML
- serves models on openscoring
- provides REST API URL
'''
import os
import tarfile
import zipfile
from flask import Flask,flash, render_template,abort, url_for, redirect, request, jsonify
from werkzeug.utils import secure_filename
from flask import send_from_directory

CLIENT_EXECUTABLE_PATH = "openscoring/openscoring-client/target/openscoring-client-executable-2.0-SNAPSHOT.jar"
JPMML_PATH = "jpmml/target/jpmml-sparkml-executable-1.6-SNAPSHOT.jar"
PMML_OUTPUT_PATH = "converted_models/"
ALLOWED_EXTENSIONS = {'tar', 'gz'}
UPLOAD_FOLDER="./models_archive"
UNZIP_FOLDER="./temp"
SERVER_ADDRESS = "http://localhost:8080/openscoring/model/"

# initializing the App and database
app = Flask(__name__)
app.secret_key = b'_5#y2L"FfasfsdQ8z\n\xec]/'

app.config.from_object(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['ALLOWED_EXTENSIONS'] = ALLOWED_EXTENSIONS
app.config['CLIENT_EXECUTABLE_PATH'] = CLIENT_EXECUTABLE_PATH
app.config['UNZIP_FOLDER'] = UNZIP_FOLDER
app.config['SERVER_ADDRESS'] = SERVER_ADDRESS
app.config['JPMML_PATH'] = JPMML_PATH
app.config['PMML_OUTPUT_PATH'] = PMML_OUTPUT_PATH

# check extension
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# extract model
def extract_file(fname):
    if fname.endswith("tar.gz"):
        tar = tarfile.open(fname, "r:gz")
        tar.extractall(app.config['UNZIP_FOLDER'])
        tar.close()
    elif fname.endswith("tar"):
        tar = tarfile.open(fname, "r:")
        tar.extractall(app.config['UNZIP_FOLDER'])
        tar.close()

# convert extracted model to PMML
def create_PMML():
    # os.system("java -cp " + CLIENT_EXECUTABLE_PATH + " org.openscoring.client.Deployer -- " + app.config['MODEL_NAME'])
    files = os.listdir("temp")
    for i in files:
        if ".json" in i:
            schema = i
        else:
            pipeline = i
    command = "spark-submit --master local --class org.jpmml.sparkml.Main "+ \
            app.config['JPMML_PATH']+ " --schema-input "+"temp/"+schema +" --pipeline-input "+\
            "temp/"+pipeline+" --pmml-output "+ app.config['PMML_OUTPUT_PATH'] + app.config['MODEL_NAME']+".pmml"
    try:
        os.system(command)
    except:
        print("pmml conversion failed")
        return
    print("Model successfully extracted")
    return

# after PMML file is created, deploy model to openscoring
def deploy_model():
    pass

@app.route('/')
def index():
    return ("service is successfully hosted")

# route to upload model -- will be called by webserver
@app.route('/model_upload/<filename>', methods=['POST'])
def model_upload(filename):
    # filter out server code injection attempts
    filename = secure_filename(filename)
    # if request not empty
    if request.data != "" and allowed_file(filename):
        # write ziped model to disk
        with open(os.path.join(UPLOAD_FOLDER, filename), "wb") as fp:
            fp.write(request.data)
        # set model name
        model_name = filename.split('.')[0]
        app.config['MODEL_NAME'] = model_name
        # unzip model
        extract_file(UPLOAD_FOLDER+'/'+filename)
        # create PMML
        create_PMML()
        # deploy_model
        deploy_model()
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