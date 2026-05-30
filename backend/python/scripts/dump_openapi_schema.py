"""Dump the FastAPI OpenAPI schema as raw JSON.

Used by CI to verify ``frontend/openapi.json`` is in sync with the backend
without running a server: the schema comes from ``create_app().openapi()`` by
introspection (no HTTP, no DB). Key-sorting / formatting is left to the
frontend's ``scripts/fetch-openapi.mjs`` so the output matches what
``pnpm generate:api`` produces exactly.

Usage:
    python scripts/dump_openapi_schema.py [output_path]   # default: stdout
"""

import json
import sys

from app import create_app


def main() -> None:
    schema = create_app().openapi()
    payload = json.dumps(schema)
    if len(sys.argv) > 1:
        with open(sys.argv[1], "w", encoding="utf-8") as f:
            f.write(payload)
    else:
        sys.stdout.write(payload)


if __name__ == "__main__":
    main()
