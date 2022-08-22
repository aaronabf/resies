#!/usr/bin/env python3
"""
Script to find reservations at given restaurant on Resy.
"""
import argparse
import collections
from datetime import date, datetime, timedelta
import re
import requests
import time


# Default config
DEFAULT_NUM_SEATS = 2
DEFAULT_START_DATE = str(date.today())
DEFAULT_END_DATE = str(date.today() + timedelta(days=30))
DEFAULT_START_TIME = "6:00 PM"
DEFAULT_END_TIME = "8:30 PM"

# Non-secret Resy API key and endpoint
API_KEY = "VbWk7s3L4KiK5fzlO7JD3Q5EYolJI7n5"
API_URL = "https://api.resy.com"


def find_reservation_id(venue_url: str) -> int:
    """
    Finds venue ID from venue URL.
    """
    matches = re.search(r"https://resy\.com/cities/([\w]*)\/([\w-]*).*", venue_url)
    if matches is None:
        raise Exception("Venue URL does not match the expected pattern")
    city, restaurant = matches.groups()
    result = requests.get(
        f"{API_URL}/3/venue?url_slug={restaurant}&location={city}",
        headers={"authorization": f'ResyAPI api_key="{API_KEY}"'},
    )
    result.raise_for_status()
    return int(result.json()["id"]["resy"])


def get_all_available_dates(venue_id: int, num_seats: int) -> list:
    """
    Returns all available dates that have any available reservations.
    """
    date_today = datetime.today().strftime("%Y-%m-%d")
    date_one_year = (datetime.today() + timedelta(365)).strftime("%Y-%m-%d")
    result = requests.get(
        f"{API_URL}/4/venue/calendar?venue_id={venue_id}&num_seats={num_seats}"
        f"&start_date={date_today}&end_date={date_one_year}",
        headers={"authorization": f'ResyAPI api_key="{API_KEY}"'},
    )
    result.raise_for_status()
    return [
        d["date"]
        for d in result.json()["scheduled"]
        if d["inventory"]["reservation"] == "available"
    ]


def get_specified_dates(available_dates: list, start_date: str, end_date: str) -> dict:
    """
    Filters all available dates between the given start and end dates.
    """
    return [d for d in available_dates if start_date <= d <= end_date]


def get_all_available_times(available_dates: list, venue_id: int, num_seats: int) -> dict:
    """
    For each specified date, returns all available times that have a reservation.
    """
    available_times = collections.defaultdict(list)
    for date in available_dates:
        time.sleep(0.3)  # Try to avoid rate limiting
        result = requests.get(
            f"{API_URL}/4/find?lat=0&long=0&day={date}&party_size={num_seats}"
            f"&venue_id={venue_id}",
            headers={"authorization": f'ResyAPI api_key="{API_KEY}"'},
        )
        result.raise_for_status()
        slots = result.json()["results"]["venues"][0]["slots"]
        for slot in slots:
            _type = slot["config"]["type"]
            _time = datetime.strptime(slot["date"]["start"], "%Y-%m-%d %H:%M:%S")
            available_times[date].append((_time, _type))
    return dict(available_times)


def get_specified_times(available_times: dict, start_time: str, end_time: str) -> dict:
    """
    Filters all available times between the given start and end times.
    """
    restricted_times = collections.defaultdict(list)
    _start_time = datetime.strptime(start_time, "%I:%M %p").time()
    _end_time = datetime.strptime(end_time, "%I:%M %p").time()
    for date, times in available_times.items():
        for info in times:
            if _start_time <= info[0].time() <= _end_time:
                restricted_times[date].append(info)
    return dict(restricted_times)


def main(venue_id: int, num_seats: int, start_date: str,
         end_date: str, start_time: str, end_time: str) -> int:
    available_dates = get_all_available_dates(venue_id, num_seats)
    if not available_dates:
        print("No reservation were found for any dates")
        return 1

    specific_dates = get_specified_dates(available_dates, start_date, end_date)
    if not specific_dates:
        print(f"No reservations were found between {start_date} and {end_date}")
        return 1

    available_times = get_all_available_times(specific_dates, venue_id, num_seats)
    if not available_times:
        print("No reservation were found for any time")
        return 1

    specified_times = get_specified_times(available_times, start_time, end_time)
    if not specified_times:
        print(f"No reservations were found between {start_time} and {end_time}")
        print("The following reservations are available outside these specified hours:")
        for date, times in available_times.items():
            for info in times:
                print(f"  - {date} {info[0].strftime('%I:%M %p')} ({info[1]})")
        return 1

    print("Found reservations!")
    for date, times in specified_times.items():
        for info in times:
            print(f"  - {date} {info[0].strftime('%I:%M %p')} ({info[1]})")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Finds reservations on Resy")
    parser.add_argument("--venue-id", type=int,
                        help="ID of the venue")
    parser.add_argument("--venue-url", type=str,
                        help="URL of the venue")
    parser.add_argument("--num-seats", type=int, default=DEFAULT_NUM_SEATS,
                        help="Number of desired seats")
    parser.add_argument("--start-date", type=str, default=DEFAULT_START_DATE,
                        help="Start date (inclusive) to search for reservations")
    parser.add_argument("--end-date", type=str, default=DEFAULT_END_DATE,
                        help="End date (inclusive) to search for reservations")
    parser.add_argument("--start-time", type=str, default=DEFAULT_START_TIME,
                        help="Start time (inclusive) to search for reservations")
    parser.add_argument("--end-time", type=str, default=DEFAULT_END_TIME,
                        help="End time (inclusive) to search for reservations")
    args = parser.parse_args()

    if args.venue_id is None and args.venue_url is None:
        parser.error("Either --venue-id or --venue-url must be provided")

    params = vars(args)

    venue_url = params.get("venue_url", None)
    if venue_url is not None:
        params["venue_id"] = find_reservation_id(venue_url)
        del params["venue_url"]

    if not params["start_time"].endswith(("AM", "PM")):
        params["start_time"] = datetime.strptime(params["start_time"], "%H:%M").strftime("%I:%M %p")
    if not params["end_time"].endswith(("AM", "PM")):
        params["end_time"] = datetime.strptime(params["end_time"], "%H:%M").strftime("%I:%M %p")

    exit(main(**params))
