import argparse
from pathlib import Path

from .server import make_server


def main():
    parser = argparse.ArgumentParser(description="Controller OS development shell; disconnected, no machine authority")
    parser.add_argument("--directory", type=Path, required=True, help="Explicit local workspace; existing settings are preserved")
    parser.add_argument("--port", type=int, default=8769)
    args = parser.parse_args()
    server = make_server(args.directory, args.port)
    print(f"Controller OS development shell: http://127.0.0.1:{server.server_port}/", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
