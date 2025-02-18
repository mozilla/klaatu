# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from http.server import HTTPServer, SimpleHTTPRequestHandler
import os
import ssl


httpd = HTTPServer(('localhost', 8888), SimpleHTTPRequestHandler)

context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
context.load_cert_chain(os.getenv("SSL_CERT"), os.getenv("SSL_KEY"))

# Set the SSL context for the server
httpd.socket = context.wrap_socket(httpd.socket, server_side=True)

httpd.serve_forever()
