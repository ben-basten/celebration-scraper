#!/usr/bin/env python3
"""
Fetches the Celebration Cinema page, extracts the ng-init data object
containing calendarDates, data, films, cinemas, etc., parses each
stringified JSON field, and writes the result to output.json.
"""

import html
import json
import re
import sys

import requests
from bs4 import BeautifulSoup

URL = "https://www.celebrationcinema.com/cinemas/celebration-cinema-crossroads"
OUTPUT_FILE = "output.json"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}


def fetch_html(url: str) -> str:
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.text


def extract_ng_init(page_html: str) -> str:
    """Return the raw (HTML-unescaped) value of the ng-init attribute that
    contains the init({...}) call described in the README."""
    soup = BeautifulSoup(page_html, "html.parser")

    # Find the tag whose ng-init begins with "init("
    tag = soup.find(attrs={"ng-init": re.compile(r"init\s*\(")})
    if not tag:
        sys.exit("Could not find ng-init tag with init() call.")

    # BeautifulSoup already unescapes HTML entities in attribute values
    return tag["ng-init"]


def parse_init_object(ng_init: str) -> dict:
    """Extract the first argument to init() — the object with calendarDates,
    data, films, cinemas, etc. — and parse each of its stringified JSON fields."""

    # Find where the opening '{' of the first argument starts
    start = ng_init.index("{")

    # Walk the string to find the matching closing '}' (respecting nesting and strings)
    depth = 0
    in_string = False
    escape = False
    end = start
    for i, ch in enumerate(ng_init[start:], start):
        if escape:
            escape = False
            continue
        if ch == "\\" and in_string:
            escape = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                end = i
                break

    obj_str = ng_init[start:end + 1]

    # The object values are JSON strings (stringified JSON).
    # json.loads the whole thing first to get the raw escaped strings.
    try:
        raw_obj = json.loads(obj_str)
    except json.JSONDecodeError as exc:
        sys.exit(f"Failed to JSON-parse the init object: {exc}")

    # Now parse each value that is itself a JSON string
    parsed = {}
    for key, value in raw_obj.items():
        if isinstance(value, str):
            try:
                parsed[key] = json.loads(value)
            except json.JSONDecodeError:
                # Keep as-is if it's not valid JSON
                parsed[key] = value
        else:
            parsed[key] = value

    return parsed


def main():
    print(f"Fetching {URL} ...")
    page_html = fetch_html(URL)

    print("Extracting ng-init data ...")
    ng_init = extract_ng_init(page_html)

    print("Parsing init() object and stringified JSON fields ...")
    result = parse_init_object(ng_init)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    keys = list(result.keys())
    print(f"Done. Parsed keys: {keys}")
    print(f"Output written to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
