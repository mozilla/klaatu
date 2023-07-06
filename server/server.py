# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import subprocess
from pathlib import Path
from urllib.parse import urlparse

from flask import Flask, request, send_from_directory
from flask.json import jsonify
from werkzeug.utils import secure_filename


URLS = []
ALLOWED_EXTENSIONS = set(["html"])

path = Path("files")
path.mkdir(exist_ok=True)

app = Flask("klaatu_server")
app.secret_key = "secret key"
app.config["UPLOAD_FOLDER"] = path.absolute()
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024
app.config["SERVER_TYPE"] = os.getenv("KLAATU_SERVER_TYPE", "client")


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/test_results", methods=["POST", "GET"])
def test_results():
    filename = "index.html"
    request_file = request.files["file"]
    if request.method == "POST":
        if request_file and allowed_file(request_file.filename):
            filename = secure_filename(request_file.filename)
            request_file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            resp = jsonify({"message": "File successfully uploaded"})
            resp.status_code = 201
    elif request.method == "GET":
        item = send_from_directory(os.path.join(app.config["UPLOAD_FOLDER"]), filename)

        return item
    return resp


@app.route(
    "/experiment",
    methods=["POST", "GET", "DELETE", "PUT"],
)
def submit():
    if request.method == "POST":
        request_data = request.get_json()
        url = urlparse(request_data["experiment_url"])
        # build url
        experiment_name = request_data["experiment_url"].split("/")[-2]
        URLS.append(f"{url.scheme}://{url.netloc}/api/v6/experiments/{experiment_name}")
        resp = jsonify("")
        resp.status_code = 201
    if request.method == "PUT":
        request_data = request.get_json()
        experiment_name = request_data["url"].split("/")[-2]
        for count, item in enumerate(URLS):
            if experiment_name in item:
                URLS[count] = {item: "tested"}
        resp = jsonify("Success")
        resp.status_code = 200
    if request.method == "GET":
        resp = jsonify(URLS)
        resp.status_code = 200
    if request.method == "DELETE":
        URLS.clear()
        resp = jsonify("URLS cleared")
        resp.status_code = 200
    return resp


@app.route(
    "/run",
    methods=["POST"],
)
def run():
    test_location = os.getenv("TESTS_DIR")
    os.chdir(test_location)
    command = "pipenv run pytest"
    subprocess.Popen(
        command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT
    )
    resp = jsonify("Success")
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
