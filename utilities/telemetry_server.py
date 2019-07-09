import json
import logging
import os

from aiohttp import web


# Disable logging by default as it is noisy, but can be helpful
# Use env variable TELEMETRY_LOGGING to re-enable.
if os.getenv("TELEMETRY_LOGGING"):
    logging.basicConfig(level=logging.DEBUG)


class Ping_Manager(object):
    def __init__(self):
        self.all_pings = {}
        self.current_ping_list = []

    async def pings(self, request):

        if request.method == "POST":
            async for data in request.content.iter_any():
                self.current_ping_list.append(json.loads(data))

            self.all_pings = {"pings": self.current_ping_list}

        if request.method == "GET":
            return web.json_response(self.current_ping_list)

        if request.method == "DELETE":
            self.all_pings = {}
            self.current_ping_list = []

        return web.Response()


ping_manager = Ping_Manager()
app = web.Application()
runner = web.AppRunner(app)
app.add_routes(
    [
        web.post("/submit/{telemetry:.*}", ping_manager.pings),
        web.get("/pings", ping_manager.pings),
        web.delete("/pings", ping_manager.pings),
    ]
)

web.run_app(app)
