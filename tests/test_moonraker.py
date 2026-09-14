import os
import sys
import threading
import unittest
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from creality_k2_mcp.moonraker import MoonrakerClient


class MoonrakerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = b'{"result":{"status":{"virtual_sdcard":{"layer":175}}}}'
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass


@contextmanager
def local_server():
    server = ThreadingHTTPServer(("127.0.0.1", 0), MoonrakerHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        thread.join()
        server.server_close()


class MoonrakerClientTests(unittest.TestCase):
    def test_reads_objects_without_using_ambient_proxy(self):
        proxy = "http://127.0.0.1:9"
        env = {
            "HTTP_PROXY": proxy, "http_proxy": proxy,
            "ALL_PROXY": proxy, "all_proxy": proxy,
            "NO_PROXY": "", "no_proxy": "",
        }
        with local_server() as url, patch.dict(os.environ, env, clear=False):
            result = MoonrakerClient(url).get_objects(["virtual_sdcard"])

        self.assertEqual(result, {"virtual_sdcard": {"layer": 175}})


if __name__ == "__main__":
    unittest.main()
