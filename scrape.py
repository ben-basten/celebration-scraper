#!/usr/bin/env python3
"""
Scrapes Celebration Cinema Crossroads for movies playing on the upcoming
Friday, Saturday, and Sunday, along with showtimes for each.
"""

import html
import json
import re
import sys
from datetime import date, timedelta
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


def next_weekend_dates():
    """Return ISO date strings for the upcoming (or current) Fri, Sat, Sun."""
    today = date.today()
    dates = []
    for weekday in (4, 5, 6):  # Friday=4, Saturday=5, Sunday=6
        diff = (weekday - today.weekday()) % 7
        dates.append((today + timedelta(days=diff)).isoformat())
    return dates


def fetch_movies(url: str) -> list:
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    # The Angular app seeds its model via ng-init="ctrl.SetModel([...],[...])"
    # on a div inside the page. The JSON is HTML-attribute-escaped.
    tag = soup.find(attrs={"ng-init": re.compile(r"ctrl\.SetModel")})
    if not tag:
        sys.exit("Could not find ng-init tag with showtime data.")

    raw_attr = tag["ng-init"]  # already unescaped by BS4
    # Extract the two JSON arrays passed to SetModel(movies, filmKey)
    match = re.match(r"ctrl\.SetModel\((\[.*\]),\s*(\[.*\])\)\s*$", raw_attr, re.DOTALL)
    if not match:
        sys.exit("Could not parse SetModel arguments.")

    movies = json.loads(match.group(1))
    return movies


def format_showtime(iso: str) -> str:
    dt = datetime.fromisoformat(iso)
    return dt.strftime("%-I:%M %p")


def main():
    target_dates = next_weekend_dates()
    day_labels = {target_dates[0]: "Friday", target_dates[1]: "Saturday", target_dates[2]: "Sunday"}

    print(f"Fetching showtimes from:\n  {URL}\n")
    movies = fetch_movies(URL)

    results = []
    for movie in movies:
        title = movie.get("Title", "Unknown")
        rating = movie.get("Rating", "")
        runtime = movie.get("RunTime", "")
        sessions = movie.get("Sessions", {})

        weekend = {}
        for d in target_dates:
            if d in sessions and sessions[d]:
                weekend[d] = sessions[d]

        if weekend:
            results.append((title, rating, runtime, weekend))

    if not results:
        print("No showtimes found for the upcoming weekend.")
        return

    results.sort(key=lambda x: x[0])

    for title, rating, runtime, weekend in results:
        header = f"{title}  [{rating}  {runtime}]"
        print(header)
        print("-" * len(header))
        for d in target_dates:
            if d not in weekend:
                continue
            label = day_labels[d]
            showtimes = weekend[d]
            times_str = "  ".join(
                f"{format_showtime(s['Showtime'])} ({s.get('FormatCode', '?')})"
                for s in sorted(showtimes, key=lambda s: s["Showtime"])
            )
            print(f"  {label} ({d}): {times_str}")
        print()


if __name__ == "__main__":
    main()
