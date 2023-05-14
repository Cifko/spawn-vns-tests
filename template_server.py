# type:ignore
from http.server import BaseHTTPRequestHandler, HTTPServer
from ports import ports
import threading
import os


class RequestHandler(BaseHTTPRequestHandler):
    def _send_response(self, file_path):
        self.send_response(200)
        self.send_header("Content-type", "application/octet-stream")
        self.send_header("Content-Disposition", f"attachment; filename={os.path.basename(file_path)}")
        self.end_headers()
        with open(file_path, "rb") as f:
            self.wfile.write(f.read())

    def do_GET(self):
        file_path = self.path[1:]
        print(file_path)
        if os.path.isfile(file_path):
            self._send_response(file_path)
        else:
            message = "File not found"
            self.send_response(404)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(bytes(message, "utf8"))


class Server:
    def run(self, server_class=HTTPServer, handler_class=RequestHandler):
        self.port = ports.get_free_port("Server HTTP")
        server_address = ("", self.port)
        self.httpd = server_class(server_address, handler_class)
        self.server = threading.Thread(target=self.httpd.serve_forever)
        self.server.start()

    def __del__(self):
        if self.httpd:
            t = threading.Thread(target=self.httpd.shutdown)
            t.start()
