#!/usr/bin/env python3
"""Generic Kie AI task runner: create a task, poll it, download results.

Stdlib + curl. Reads KIE_API_KEY from the environment. Contains NO built-in
endpoints: take the base URL, paths, body and field names from docs.kie.ai
for the model you are using.

  kie_client.py run --base-url <docs base> --create-path <path> \
      --status-path <path> --body-file request.json --out ./out
  (--body '<json>' also works, but prefer --body-file: Windows shells mangle
   the quotes inside inline JSON)
  kie_client.py status --base-url <docs base> --status-path <path> <task_id>

Field names are dotted paths into the JSON responses; set them to whatever
the docs say (the defaults are only guesses):
  --id-field data.taskId          where the task id is in the create response
  --id-param taskId               query parameter name for the status call
  --state-field data.state        where the status is in the status response
  --success-values success        comma-separated
  --fail-values fail              comma-separated
  --result-field data.resultJson  where results live (JSON string or object)
"""
import argparse
import json
import os
import sys
import subprocess
import time
import urllib.parse


def dig(obj, dotted):
    for part in dotted.split("."):
        if not isinstance(obj, dict):
            return None
        obj = obj.get(part)
    return obj


def call(base, method, path, body=None):
    """HTTP via curl so the OS trust store (corporate TLS proxies, etc.) is honoured."""
    key = os.environ.get("KIE_API_KEY")
    if not key:
        sys.exit("KIE_API_KEY is not set (see the docs for where to get one)")
    cmd = ["curl", "-sS", "-X", method, base.rstrip("/") + path,
           "-H", "Content-Type: application/json", "-K", "-",
           "-w", "\n%{http_code}", "--max-time", "60"]
    if body is not None:
        cmd += ["--data-binary", json.dumps(body)]
    # key goes via stdin config so it never appears in the process list
    p = subprocess.run(cmd, input=f'header = "Authorization: Bearer {key}"\n',
                       capture_output=True, text=True)
    if p.returncode:
        sys.exit(f"curl failed: {p.stderr.strip()}")
    text, _, code = p.stdout.rpartition("\n")
    if not code.startswith("2"):
        hint = " (rate limited: back off, check the docs' limits, resubmit)" if code == "429" else ""
        sys.exit(f"HTTP {code}{hint}: {text}")
    return json.loads(text)


def find_urls(obj):
    """Collect http(s) URLs anywhere in a result (parsing JSON strings)."""
    if isinstance(obj, str):
        if obj.startswith(("http://", "https://")):
            return [obj]
        try:
            return find_urls(json.loads(obj))
        except ValueError:
            return []
    urls = []
    if isinstance(obj, dict):
        obj = list(obj.values())
    if isinstance(obj, list):
        for v in obj:
            urls += find_urls(v)
    return list(dict.fromkeys(urls))


def download(urls, out):
    os.makedirs(out, exist_ok=True)
    paths = []
    for i, u in enumerate(urls):
        name = os.path.basename(urllib.parse.urlparse(u).path) or f"asset_{i}"
        dest = os.path.join(out, name)
        p = subprocess.run(["curl", "-sSL", "--fail", "-o", dest, u], capture_output=True, text=True)
        if p.returncode:
            sys.exit(f"download failed for {u}: {p.stderr.strip()}")
        paths.append(dest)
    return paths


def get_status(args, task_id):
    q = f"{args.status_path}?{urllib.parse.urlencode({args.id_param: task_id})}"
    return call(args.base_url, "GET", q)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("run", "status"):
        s = sub.add_parser(name)
        s.add_argument("--base-url", required=True)
        s.add_argument("--status-path", required=True)
        s.add_argument("--id-param", default="taskId")
        s.add_argument("--state-field", default="data.state")
        s.add_argument("--success-values", default="success")
        s.add_argument("--fail-values", default="fail")
        s.add_argument("--result-field", default="data.resultJson")
        if name == "run":
            s.add_argument("--create-path", required=True)
            g = s.add_mutually_exclusive_group(required=True)
            g.add_argument("--body", help="full JSON request body")
            g.add_argument("--body-file", help="path to a file holding the JSON body (use this on Windows shells, which mangle quotes)")
            s.add_argument("--id-field", default="data.taskId")
            s.add_argument("--out", default=os.path.expanduser("~/Downloads/kie-output"))
            s.add_argument("--interval", type=int, default=10)
            s.add_argument("--timeout", type=int, default=900)
        else:
            s.add_argument("task_id")
    args = p.parse_args()

    if args.cmd == "status":
        print(json.dumps(get_status(args, args.task_id), indent=2))
        return

    if args.body_file:
        with open(args.body_file, encoding="utf-8") as f:
            body = json.load(f)
    else:
        body = json.loads(args.body)
    res = call(args.base_url, "POST", args.create_path, body)
    task_id = dig(res, args.id_field)
    if not task_id:
        sys.exit(f"No task id at '{args.id_field}' in create response: {json.dumps(res)}")
    print(f"taskId: {task_id}", file=sys.stderr)

    ok = {v.strip().lower() for v in args.success_values.split(",")}
    bad = {v.strip().lower() for v in args.fail_values.split(",")}
    deadline = time.time() + args.timeout
    while time.time() < deadline:
        res = get_status(args, task_id)
        state = str(dig(res, args.state_field)).lower()
        if state in ok:
            urls = find_urls(dig(res, args.result_field) or res)
            files = download(urls, args.out)
            print(json.dumps({"taskId": task_id, "urls": urls, "files": files}, indent=2))
            return
        if state in bad:
            sys.exit(f"Task {task_id} failed: {json.dumps(res)}")
        print(f"  state={state}", file=sys.stderr)
        time.sleep(args.interval)
    sys.exit(f"Timed out after {args.timeout}s. Task {task_id} may still finish; check with `status`. Do not resubmit blindly.")


if __name__ == "__main__":
    main()
