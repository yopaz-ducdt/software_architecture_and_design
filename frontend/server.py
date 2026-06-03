"""
Custom HTTP server for frontend that sets correct UTF-8 charset header
Run: python server.py
"""
from http.server import HTTPServer, SimpleHTTPRequestHandler
import os

class UTF8Handler(SimpleHTTPRequestHandler):
    def guess_type(self, path):
        mtype = super().guess_type(path)
        if isinstance(mtype, str) and 'text/html' in mtype and 'charset' not in mtype:
            return 'text/html; charset=utf-8'
        if isinstance(mtype, str) and 'application/javascript' in mtype and 'charset' not in mtype:
            return 'application/javascript; charset=utf-8'
        if isinstance(mtype, str) and 'text/css' in mtype and 'charset' not in mtype:
            return 'text/css; charset=utf-8'
        return mtype

    def log_message(self, format, *args):
        pass  # Suppress access logs


if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    port = 4000
    server = HTTPServer(('0.0.0.0', port), UTF8Handler)
    print(f'LearnMart Frontend running at http://localhost:{port}')
    server.serve_forever()
