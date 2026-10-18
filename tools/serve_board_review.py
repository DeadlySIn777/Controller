"""Serve the offline board-review side panel on loopback only."""
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


class ReviewHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def list_directory(self, path):
        self.send_error(404, "Open index.html to inspect the board review")
        return None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8788)
    args = parser.parse_args()
    folder = Path(__file__).resolve().parents[1] / "hardware" / "board_review"
    handler = partial(ReviewHandler, directory=str(folder))
    server = ThreadingHTTPServer(("127.0.0.1", args.port), handler)
    print(f"Board review: http://127.0.0.1:{args.port}/index.html", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
