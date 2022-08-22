# Reservation Finder

Finds reservations on given platform. Currently only [Resy](https://resy.com) is
supported.

### Setup

Requires `requests`. Either run globally if `requests` is installed or set up
a virtual environment:
```bash
python3 -m venv .venv
.venv/bin/pip install requests
.venv/bin/python resy.py -h
```

### Usage

For ease-of-use, the script works with a single argument `--venue-url`. If you
visit a restaurant on Resy you can use that URL as this argument. For example:
```bash
python resy.py --venue-url 'https://resy.com/cities/ny/cool-restaurant?date=2022-08-22&seats=2'
```
Alternatively, you can specify the `--venue-id` manually, which can be found in
the network requests.

You can also specify number of seats and start/end times. Run with `--help` to
view all arguments.
