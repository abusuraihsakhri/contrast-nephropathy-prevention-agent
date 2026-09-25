"""Command-line entry point for the contrast nephropathy prevention calculator."""

from __future__ import annotations

import argparse
import sys

from cin_guard import main as clinical_main


def _serve(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="contrast-nephropathy-prevention-agent serve")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args(argv)

    try:
        import uvicorn
    except ImportError:
        print('Server dependencies are not installed. Run: pip install -e ".[server]"', file=sys.stderr)
        return 1

    from .server import create_app

    uvicorn.run(create_app(), host=args.host, port=args.port)
    return 0


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] == "serve":
        return _serve(args[1:])
    return clinical_main(args)


if __name__ == "__main__":
    raise SystemExit(main())
