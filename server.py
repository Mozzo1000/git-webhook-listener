from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from http import HTTPStatus
import json
import signal
import sys
import argparse
from functools import partial
import subprocess

class RequestHandler(BaseHTTPRequestHandler):
    def __init__(self, endpoints, data, *args, **kwargs):
        self.endpoints = endpoints
        self.data = data
        super().__init__(*args, **kwargs)

    def set_headers(self):
        self.send_header("Content-type", "application/json")
        self.end_headers()

    def do_HEAD(self):
        self.set_headers()

    def do_POST(self):
        if self.path in self.endpoints:
            self.data_string = self.rfile.read(int(self.headers['Content-Length']))
            message = json.loads(self.data_string)
            print(message)
            print(self.data[self.path])

            self.send_response(HTTPStatus.OK.value)
            self.set_headers()
            self.wfile.write(json.dumps(message).encode("utf-8"))

            subprocess.run(self.data[self.path][0]["script"])
        else:
            self.error_content_type = "application/json"
            self.error_message_format = '{"status": %(code)d, "message": "%(message)s"}'
            self.send_error(HTTPStatus.NOT_FOUND.value, "Not found")

def main():
    parser = argparse.ArgumentParser("git-webhook-listener")
    parser.add_argument("-a", "--address", type=str, default="localhost", help="Address of http server")
    parser.add_argument("-p", "--port", type=int, default=5280, help="Port of http server")
    parser.add_argument("--hooks", type=str, help="Path to configuration file")

    endpoints = []
    with open(parser.parse_args().hooks, "r") as f:
        data = json.load(f)
        for i in data:
            endpoints.append(i)

    server_address = (parser.parse_args().address, parser.parse_args().port)
    httpd = ThreadingHTTPServer(server_address, partial(RequestHandler, endpoints, data))

    def signal_handler(sig, frame):
        print('Closing server..')
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    print('git-webook-listener serving at %s:%d' % server_address)
    httpd.serve_forever()

    


if __name__ == '__main__':
    main()
