#!/usr/bin/env python3
"""Build the fixture sites for the manual checks recorded in tests/verify/README.md.

Takes an unpacked Pages artifact and writes one copy of it per scenario, changing
only data/specs.json:

    python3 tests/verify/build_fixtures.py ARTIFACT_DIR OUT_DIR
"""
import json
import os
import shutil
import sys

# Formula-shaped titles for the CSV check. All are inert: at worst they add 1 and 1.
CSV_TITLES = [
    ("ascii =", "=1+1"),
    ("ascii +", "+1+1"),
    ("ascii -", "-1+1"),
    ("ascii @", "@SUM(1,1)"),
    ("full-width =", "＝1+1"),
    ("full-width +", "＋1+1"),
    ("full-width -", "－1+1"),
    ("full-width @", "＠SUM(1,1)"),
    ("leading space", " =1+1"),
    ("leading tab", "\t=1+1"),
    ("leading ideographic space", "　=1+1"),
    ("leading no-break space", " =1+1"),
    ("leading BOM", "﻿=1+1"),
    ("leading LF", "\n=1+1"),
    ("leading CR", "\r=1+1"),
    ("leading CRLF", "\r\n@SUM(1,1)"),
    ("LF inside text", "line one\n=1+1"),
    ("quoted delimiter", 'a,"b",=1+1'),
    ("quote first", '"=1+1"'),
    ("two formulas", "=1+1,=2+2"),
    ("control", "OpenID Connect Core 1.0"),
]


def live_specs(data, status=None):
    return [s for s in data["specs"] if not s.get("redirect") and not s.get("moved_to")
            and (status is None or s["status"] == status)]


def set_workgroup(value):
    def change(data):
        live_specs(data, "final")[0]["workgroup"] = value
    return change


def set_bad_status(data):
    live_specs(data, "final")[1]["status"] = "constructor"


def remove_revisions(data):
    live_specs(data, "final")[2].update(revisions=[], current_url=None, latest=None, milestone=None)


def set_csv_titles(data):
    specs = live_specs(data)
    for spec, (_, title) in zip(specs, CSV_TITLES):
        spec["title"] = title
    # The same values reach the other free-text columns.
    specs[0]["authors"] = [{"name": "=1+1"}]
    specs[1]["workgroup"] = "@SUM(1,1)"


SCENARIOS = {
    "baseline": None,
    "workgroup-proto": set_workgroup("__proto__"),
    "workgroup-constructor": set_workgroup("constructor"),
    "workgroup-tostring": set_workgroup("toString"),
    "status-constructor": set_bad_status,
    "no-revision": remove_revisions,
    "csv": set_csv_titles,
}


def main(artifact, out):
    with open(os.path.join(artifact, "data", "specs.json"), encoding="utf-8") as f:
        original = f.read()
    for name, change in SCENARIOS.items():
        site = os.path.join(out, name)
        shutil.rmtree(site, ignore_errors=True)
        shutil.copytree(artifact, site)
        data = json.loads(original)
        if change:
            change(data)
        with open(os.path.join(site, "data", "specs.json"), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        print(name, site)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
