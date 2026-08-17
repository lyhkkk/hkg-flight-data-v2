#!/usr/bin/env python3
"""
Fetch aircraft registration numbers from FlightStats
Polite frequency: 3 seconds between requests, local cache
"""
import json
import os
import re
import sys
import time
import urllib.request

BASE_URL = "https://www.flightstats.com/v2/flight-tracker"
CACHE_DIR = os.path.expanduser("~/.hkg_cache/flightstats")
DELAY = 3  # seconds between requests


def fetch_flight_stats(carrier, flight_num, year, month, date):
    """Fetch flight data from FlightStats"""
    url = f"{BASE_URL}/{carrier}/{flight_num}?year={year}&month={month}&date={date}"
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html',
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode('utf-8')
            # Extract __NEXT_DATA__ JSON
            match = re.search(r'__NEXT_DATA__\s*=\s*({.*?})\s*;\s*__NEXT_LOADED_PAGES__', html, re.DOTALL)
            if match:
                data = json.loads(match.group(1))
                flight = data.get('props', {}).get('initialState', {}).get('flightTracker', {}).get('flight', {})
                positional = flight.get('positional', {}).get('flexTrack', {})
                return {
                    'tailNumber': positional.get('tailNumber', ''),
                    'callsign': positional.get('callsign', ''),
                    'equipment': flight.get('additionalFlightInfo', {}).get('equipment', {}).get('name', ''),
                    'equipment_iata': flight.get('additionalFlightInfo', {}).get('equipment', {}).get('iata', ''),
                }
    except Exception as e:
        return {'error': str(e)}
    return {}


def get_cache_path(carrier, flight_num, date):
    """Get cache file path"""
    os.makedirs(CACHE_DIR, exist_ok=True)
    return os.path.join(CACHE_DIR, f"{carrier}_{flight_num}_{date}.json")


def load_cache(carrier, flight_num, date):
    """Load from cache if exists"""
    path = get_cache_path(carrier, flight_num, date)
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None


def save_cache(carrier, flight_num, date, data):
    """Save to cache"""
    path = get_cache_path(carrier, flight_num, date)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def extract_flight_info(flight_number):
    """Extract carrier code and flight number from flight number string"""
    # e.g., "CX 759" -> ("CX", "759"), "MU725" -> ("MU", "725")
    fn = flight_number.replace(' ', '').strip()
    # Find where digits start
    match = re.match(r'([A-Za-z]+)(\d+)', fn)
    if match:
        return match.group(1).upper(), match.group(2)
    return None, None


def lookup_reg(carrier, num, date):
    """Look up cached reg for a flight. Returns dict or None."""
    cached = load_cache(carrier, num, date)
    if cached:
        return cached
    # Try fetching if not cached
    year, month, day = date.split('-')
    result = fetch_flight_stats(carrier, num, year, month, int(day))
    if 'error' not in result and result.get('tailNumber'):
        save_cache(carrier, num, date, result)
    return result


def lookup_by_flight(flight_number, date):
    """Look up reg by flight number string like 'CX 759' or 'MU725'"""
    carrier, num = extract_flight_info(flight_number)
    if not carrier or not num:
        return None
    return lookup_reg(carrier, num, date)


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, default=0, help='Max flights to fetch (0=all)')
    parser.add_argument('--delay', type=float, default=DELAY, help='Seconds between requests')
    args = parser.parse_args()

    # Load enriched data
    arr_path = 'hkg_arrivals_enriched.json'
    dep_path = 'hkg_departures_enriched.json'

    flights = []
    for path in [arr_path, dep_path]:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                flights.extend(json.load(f))

    print(f"Total flights: {len(flights)}")

    # Get unique flight+date combinations
    seen = set()
    unique_flights = []
    for f in flights:
        fn = f.get('flight_number', '')
        date = f.get('date', '')
        key = f"{fn}_{date}"
        if key not in seen:
            seen.add(key)
            unique_flights.append(f)

    print(f"Unique flight+date combos: {len(unique_flights)}")

    # Check cache hit rate
    cached = 0
    to_fetch = []
    for f in unique_flights:
        carrier, num = extract_flight_info(f.get('flight_number', ''))
        if carrier and num:
            cached_data = load_cache(carrier, num, f.get('date', ''))
            if cached_data:
                cached += 1
            else:
                to_fetch.append(f)

    print(f"Cache hits: {cached}")
    print(f"To fetch: {len(to_fetch)}")

    if args.limit > 0:
        to_fetch = to_fetch[:args.limit]
        print(f"Limited to: {len(to_fetch)}")

    if not to_fetch:
        print("All flights cached!")
        return

    # Fetch with polite delay
    fetched = 0
    errors = 0
    for i, f in enumerate(to_fetch):
        carrier, num = extract_flight_info(f.get('flight_number', ''))
        if not carrier or not num:
            continue

        date = f.get('date', '')
        year, month, day = date.split('-')

        print(f"[{i+1}/{len(to_fetch)}] Fetching {carrier}{num} on {date}...", end=' ', flush=True)
        result = fetch_flight_stats(carrier, num, year, month, int(day))

        if 'error' in result:
            print(f"ERROR: {result['error']}")
            errors += 1
        else:
            save_cache(carrier, num, date, result)
            tail = result.get('tailNumber', '')
            print(f"OK - {tail or 'no reg'}")
            fetched += 1

        # Polite delay
        if i < len(to_fetch) - 1:
            time.sleep(args.delay)

    print(f"\nDone: {fetched} fetched, {errors} errors")


if __name__ == '__main__':
    main()
