"""python -m jsonflow.server <command>

  serve        run the web app        [--host 127.0.0.1 --port 8080 --data-dir jsonflow_data --demo]
  create-user  add a user             --username NAME --role admin|super_admin  (password prompted, or JSONFLOW_NEW_PASSWORD)

--demo swaps the SAJHA server for synthetic fixtures and the LLM for scripted answers, so the
product can be explored without network access or keys.
"""
from __future__ import annotations

import argparse
import getpass
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def demo_overrides():
    from jsonflow.llm.scripted import ScriptedProvider
    from jsonflow.mcp.fixture import FixtureClient

    fx = REPO / "config" / "jsonflow" / "fixtures"
    scripted = ScriptedProvider(fx / "llm_sector_events.json")
    return ({"sajha": FixtureClient("sajha", fx / "sajha_sector_events.json")},
            {"anthropic": scripted, "openai_compat": scripted})


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -m jsonflow.server", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("serve")
    s.add_argument("--host", default="127.0.0.1")
    s.add_argument("--port", type=int, default=8080)
    s.add_argument("--data-dir", default=os.getenv("JSONFLOW_DATA_DIR", "jsonflow_data"))
    s.add_argument("--demo", action="store_true")
    s.add_argument("--no-examples", action="store_true", help="do not seed the example agent")
    c = sub.add_parser("create-user")
    c.add_argument("--username", required=True)
    c.add_argument("--role", choices=["admin", "super_admin"], required=True)
    c.add_argument("--display-name", default="")
    c.add_argument("--data-dir", default=os.getenv("JSONFLOW_DATA_DIR", "jsonflow_data"))
    args = ap.parse_args(argv)

    if args.cmd == "create-user":
        from jsonflow.server.db import Database
        from jsonflow.server.services import Service, ServiceError

        password = os.getenv("JSONFLOW_NEW_PASSWORD") or getpass.getpass("Password: ")
        db = Database(Path(args.data_dir) / "jsonflow.sqlite")
        svc = Service(db, Path(args.data_dir))
        svc.bootstrap(seed_examples=False)
        try:
            svc.create_user(args.username, password, args.role, args.display_name, "cli")
        except ServiceError as e:
            print(f"error: {e}", file=sys.stderr)
            return 1
        finally:
            svc.shutdown()
        print(f"created {args.role} {args.username}")
        return 0

    import uvicorn

    from jsonflow.server.app import create_app

    clients, llms = demo_overrides() if args.demo else (None, None)
    app = create_app(args.data_dir, client_overrides=clients, llm_overrides=llms, seed_examples=not args.no_examples)
    if not app.state.db.one("SELECT id FROM users LIMIT 1"):
        print("No users yet. Create the first super admin:\n"
              f"  python -m jsonflow.server create-user --username <name> --role super_admin --data-dir {args.data_dir}",
              file=sys.stderr)
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")
    return 0


if __name__ == "__main__":
    sys.exit(main())
