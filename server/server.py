# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
from pathlib import Path

from flask import Flask, request
from flask.json import jsonify
from werkzeug.utils import secure_filename


URLS = []
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'json'])

Path("files").mkdir(exist_ok=True)
app = Flask("klaatu_server")
app.secret_key = "secret key"
app.config['UPLOAD_FOLDER'] = "files"
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024


def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/test_results", methods=["POST"])
def test_results():
    request_file = request.files["file"]
    if request_file and allowed_file(request_file.filename):
        filename = secure_filename(request_file.filename)
        request_file.save(
            os.path.join(app.config['UPLOAD_FOLDER'], filename)
        )
        resp = jsonify({'message' : 'File successfully uploaded'})
        resp.status_code = 201
    return resp


@app.route(
    "/experiment",
    methods=["POST", "GET", "DELETE"],
)
def submit():
    if request.method == "POST":
        request_data = request.get_json()
        URLS.append(request_data["experiment_url"])
        resp = jsonify("")
        resp.status_code = 201
    if request.method == "GET":
        resp = jsonify(URLS)
        resp.status_code = 200
    if request.method == "DELETE":
        URLS.clear()
        resp = jsonify("URLS cleared")
        resp.status_code = 200
    return resp

@app.route("/", methods=["GET"])
def ping():
    resp = jsonify("Hello")
    resp.status_code = 200
    return resp


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 1378))
    app.run(debug=True, host="0.0.0.0", port=port)