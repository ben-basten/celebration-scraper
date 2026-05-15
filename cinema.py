#!/usr/bin/env python3
"""
Celebration Cinema showtime scraper.

Mode 1 — movies by day (default):
    python cinema.py [--days fri sat sun ...] [--weeks N]

Mode 2 — showtimes for a specific movie:
    python cinema.py --movie "mortal kombat" [--days fri sat sun ...] [--weeks N]

Supported day names: today, tomorrow, mon, tue, wed, thu, fri, sat, sun
Omitting --days shows all days within the --weeks window (default: 1 week).
"""

import argparse
import json
import re
import sys
from collections import defaultdict
from datetime import datetime

import requests
from bs4 import BeautifulSoup

URL = "https://www.celebrationcinema.com/cinemas/celebration-cinema-crossroads"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

# Maps 3-letter day names (and aliases) to Python weekday integers (Mon=0)
DAY_NAME_TO_WEEKDAY = {
    "mon": 0, "tue": 1, "wed": 2, "thu": 3,
    "fri": 4, "sat": 5, "sun": 6,
}


# ---------------------------------------------------------------------------
# Fetching & parsing
# ---------------------------------------------------------------------------

def fetch_html(url: str) -> str:
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.text


def extract_ng_init(page_html: str) -> str:
    soup = BeautifulSoup(page_html, "html.parser")
    tag = soup.find(attrs={"ng-init": re.compile(r"init\s*\(")})
    if not tag:
        sys.exit("Could not find ng-init tag with init() call.")
    return tag["ng-init"]


def parse_init_object(ng_init: str) -> dict:
    """Extract and fully parse the first object argument to init(...)."""
    start = ng_init.index("{")

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

    try:
        raw_obj = json.loads(obj_str)
    except json.JSONDecodeError as exc:
        sys.exit(f"Failed to JSON-parse the init object: {exc}")

    parsed = {}
    for key, value in raw_obj.items():
        if isinstance(value, str):
            try:
                parsed[key] = json.loads(value)
            except json.JSONDecodeError:
                parsed[key] = value
        else:
            parsed[key] = value

    return parsed


def fetch_data() -> dict:
    print(f"Fetching {URL} ...", file=sys.stderr)
    page_html = fetch_html(URL)
    ng_init = extract_ng_init(page_html)
    return parse_init_object(ng_init)


# ---------------------------------------------------------------------------
# Day resolution
# ---------------------------------------------------------------------------

def resolve_days(requested: list[str], calendar_dates: list[dict], weeks: int = 1) -> list[tuple[str, str]]:
    """
    Given a list of day name tokens and the calendarDates list from the API,
    return an ordered list of (iso_date, label) pairs for the matched days,
    in calendar order, within the given number of weeks from today.

    calendar_dates entries: {"Text": "Today", "Moment": "2026-05-14T00:00:00", "ID": 0}
    """
    from datetime import date, timedelta
    cutoff = (date.today() + timedelta(weeks=weeks)).isoformat()

    # Build lookup structures from calendarDates
    # iso_date -> label
    cal_by_date: dict[str, str] = {}
    for entry in calendar_dates:
        iso = entry["Moment"][:10]  # "2026-05-14"
        cal_by_date[iso] = entry["Text"]

    # Ordered list of iso dates available within the window
    available_dates = [d for d in sorted(cal_by_date.keys()) if d <= cutoff]
    # today is first available date
    today_iso = sorted(cal_by_date.keys())[0] if cal_by_date else None

    # Resolve requested tokens -> set of iso dates
    matched: dict[str, str] = {}  # iso -> label, preserving calendar order later

    for token in requested:
        token = token.lower()
        if token == "today":
            if today_iso:
                matched[today_iso] = cal_by_date[today_iso]
        elif token == "tomorrow":
            tomorrow_candidates = available_dates[1:2]
            for d in tomorrow_candidates:
                matched[d] = cal_by_date[d]
        elif token in DAY_NAME_TO_WEEKDAY:
            target_wd = DAY_NAME_TO_WEEKDAY[token]
            for iso in available_dates:
                dt = datetime.fromisoformat(iso)
                if dt.weekday() == target_wd:
                    matched[iso] = cal_by_date[iso]
                    break
        else:
            print(f"Warning: unknown day '{token}' (use today/tomorrow/mon/tue/wed/thu/fri/sat/sun)", file=sys.stderr)

    # Return in calendar order
    return [(iso, matched[iso]) for iso in available_dates if iso in matched]


def all_days(calendar_dates: list[dict], weeks: int = 1) -> list[tuple[str, str]]:
    """Return available (iso_date, label) pairs within the given number of weeks from today."""
    from datetime import date, timedelta
    cutoff = (date.today() + timedelta(weeks=weeks)).isoformat()
    pairs = []
    for entry in sorted(calendar_dates, key=lambda e: e["Moment"]):
        iso = entry["Moment"][:10]
        if iso <= cutoff:
            pairs.append((iso, entry["Text"]))
    return pairs


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def fmt_time(iso_datetime: str) -> str:
    """Convert ISO datetime string to '5:35 PM'."""
    dt = datetime.fromisoformat(iso_datetime)
    return dt.strftime("%-I:%M %p")


def fmt_day_label(iso_date: str, cal_label: str) -> str:
    """Return a friendly day heading like 'Friday, May 16  (Today)'."""
    dt = datetime.fromisoformat(iso_date)
    weekday = dt.strftime("%A")
    month_day = dt.strftime("%B %-d")
    # Append calendar label if it's not just a date string
    if cal_label in ("Today", "Tomorrow"):
        return f"{weekday}, {month_day}  ({cal_label})"
    return f"{weekday}, {month_day}"


# ---------------------------------------------------------------------------
# Mode 1: movies by day
# ---------------------------------------------------------------------------

def mode_days(data: list[dict], day_pairs: list[tuple[str, str]], hide_times: bool = False) -> None:
    # Build: iso_date -> list of (title, runtime, sorted_showtimes)
    for iso_date, cal_label in day_pairs:
        # Collect movies that have showtimes on this date
        movies_on_day = []
        for movie in data:
            title = movie.get("Title", "Unknown")
            showtimes_on_day = [
                s for s in movie.get("Showtime", [])
                if s.get("Date", "")[:10] == iso_date
            ]
            if not showtimes_on_day:
                continue
            runtime = showtimes_on_day[0].get("RunTime", "")
            showtimes_on_day.sort(key=lambda s: s["Showtime"])
            movies_on_day.append((title, runtime, showtimes_on_day))

        if not movies_on_day:
            continue

        movies_on_day.sort(key=lambda m: m[0])

        heading = fmt_day_label(iso_date, cal_label)
        print(heading)
        print("-" * len(heading))
        for title, runtime, showtimes in movies_on_day:
            title_line = f"  {title}"
            if runtime:
                title_line += f"  [{runtime}]"
            print(title_line)
            if not hide_times:
                times_str = "  ".join(
                    f"{fmt_time(s['Showtime'])} ({s.get('FormatCode', '?')})"
                    for s in showtimes
                )
                print(f"    {times_str}")
        print()


# ---------------------------------------------------------------------------
# Mode 2: showtimes by movie
# ---------------------------------------------------------------------------

def mode_movie(data: list[dict], query: str, day_pairs: list[tuple[str, str]], hide_times: bool = False) -> None:
    query_lower = query.lower()
    matches = [m for m in data if query_lower in m.get("Title", "").lower()]

    if not matches:
        print(f"No movies found matching '{query}'.")
        return

    day_set = {iso for iso, _ in day_pairs}
    day_label_map = {iso: label for iso, label in day_pairs}

    for movie in matches:
        title = movie.get("Title", "Unknown")
        all_showtimes = movie.get("Showtime", [])

        # Group showtimes by date, filtered to requested days
        by_date: dict[str, list] = defaultdict(list)
        for s in all_showtimes:
            d = s.get("Date", "")[:10]
            if d in day_set:
                by_date[d].append(s)

        if not by_date:
            continue

        # Get runtime from first showtime
        first = next(iter(s for s in all_showtimes if s.get("RunTime")), None)
        runtime = first.get("RunTime", "") if first else ""

        title_line = title
        if runtime:
            title_line += f"  [{runtime}]"
        print(title_line)

        for iso_date in sorted(by_date.keys()):
            cal_label = day_label_map.get(iso_date, "")
            heading = fmt_day_label(iso_date, cal_label)
            print(f"  {heading}")
            if not hide_times:
                showtimes = sorted(by_date[iso_date], key=lambda s: s["Showtime"])
                times_str = "  ".join(
                    f"{fmt_time(s['Showtime'])} ({s.get('FormatCode', '?')})"
                    for s in showtimes
                )
                print(f"    {times_str}")
        print()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Celebration Cinema showtime scraper.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python cinema.py\n"
            "  python cinema.py --days fri sat sun\n"
            "  python cinema.py --weeks 2\n"
            "  python cinema.py --movie 'mortal kombat'\n"
            "  python cinema.py --movie 'mortal kombat' --days fri sat sun\n"
            "  python cinema.py --movie 'mortal kombat' --weeks 2\n"
        ),
    )
    parser.add_argument(
        "--days",
        nargs="+",
        metavar="DAY",
        help="Days to show: today tomorrow mon tue wed thu fri sat sun",
    )
    parser.add_argument(
        "--no-times",
        action="store_true",
        help="Hide showtimes, listing only movie titles per day",
    )
    parser.add_argument(
        "--weeks",
        type=int,
        default=1,
        metavar="N",
        help="How many weeks out to look (default: 1)",
    )
    parser.add_argument(
        "--movie",
        metavar="TITLE",
        help="Movie title search (case-insensitive substring match)",
    )
    args = parser.parse_args()

    result = fetch_data()
    calendar_dates = result.get("calendarDates", [])
    movie_data = result.get("data", [])

    if not calendar_dates:
        sys.exit("No calendarDates found in page data.")
    if not movie_data:
        sys.exit("No movie data found in page data.")

    if args.days:
        day_pairs = resolve_days(args.days, calendar_dates, weeks=args.weeks)
        if not day_pairs:
            sys.exit("None of the requested days are available in the schedule.")
    else:
        day_pairs = all_days(calendar_dates, weeks=args.weeks)

    print()

    if args.movie:
        mode_movie(movie_data, args.movie, day_pairs, hide_times=args.no_times)
    else:
        mode_days(movie_data, day_pairs, hide_times=args.no_times)


if __name__ == "__main__":
    main()
