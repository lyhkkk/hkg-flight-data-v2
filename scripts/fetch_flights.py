#!/usr/bin/env python
"""
Fetch HKIA flight data for August 16-31
Uses the HKIA flightinfo REST API
"""
import json
import urllib.request
import urllib.error
import time
import sys
from datetime import date, timedelta

BASE_URL = "https://www.hongkongairport.com/flightinfo-rest/rest/flights"

def fetch_date(dt, endpoint=""):
    """Fetch flight data for a specific date"""
    date_str = dt.strftime("%Y-%m-%d")
    if endpoint:
        url = f"{BASE_URL}/{endpoint}?date={date_str}&span=1"
    else:
        url = f"{BASE_URL}?date={date_str}&span=1"
    print(f"  Fetching {url} ...", end=" ", flush=True)
    
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Referer': 'https://www.hongkongairport.com/en/flights/arrivals/passenger.page'
        })
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            if isinstance(data, list):
                total_flights = sum(len(item.get('list', [])) for item in data)
                print(f"OK - {len(data)} entries, {total_flights} flights")
                return data
            else:
                print(f"ERROR - unexpected response: {str(data)[:100]}")
                return []
    except Exception as e:
        print(f"ERROR - {e}")
        return []

def main():
    all_arrivals = []
    all_departures = []
    
    # Date range: Aug 16 to Aug 31, 2026
    start_date = date(2026, 8, 16)
    end_date = date(2026, 8, 31)
    
    today = date.today()
    
    current = start_date
    while current <= end_date:
        date_str = current.strftime("%Y-%m-%d")
        print(f"\n=== Fetching data for {date_str} ===")
        
        # Use 'past' endpoint for past dates, regular for current/future
        if current < today:
            data = fetch_date(current, "past")
        else:
            data = fetch_date(current, "")
        
        # Parse the response
        arrivals_passenger = []
        departures_passenger = []
        
        for entry in data:
            is_arrival = entry.get('arrival', False)
            is_cargo = entry.get('cargo', False)
            flights = entry.get('list', [])
            
            if is_cargo:
                continue  # Skip cargo flights
            
            if is_arrival:
                for flight in flights:
                    flight['_date'] = date_str
                    flight['_type'] = 'arrival'
                arrivals_passenger.extend(flights)
            else:
                for flight in flights:
                    flight['_date'] = date_str
                    flight['_type'] = 'departure'
                departures_passenger.extend(flights)
        
        print(f"  Passenger arrivals: {len(arrivals_passenger)}, departures: {len(departures_passenger)}")
        all_arrivals.extend(arrivals_passenger)
        all_departures.extend(departures_passenger)
        
        current += timedelta(days=1)
        time.sleep(0.5)  # Be nice to the server
    
    print(f"\n=== SUMMARY ===")
    print(f"Total passenger arrivals: {len(all_arrivals)}")
    print(f"Total passenger departures: {len(all_departures)}")
    print(f"Total flights: {len(all_arrivals) + len(all_departures)}")
    
    # Save raw data
    with open('hkg_raw_arrivals.json', 'w', encoding='utf-8') as f:
        json.dump(all_arrivals, f, ensure_ascii=False, indent=2)
    
    with open('hkg_raw_departures.json', 'w', encoding='utf-8') as f:
        json.dump(all_departures, f, ensure_ascii=False, indent=2)
    
    print(f"\nRaw data saved to hkg_raw_arrivals.json and hkg_raw_departures.json")
    
    # Now create the formatted dataset
    formatted_arrivals = format_arrivals(all_arrivals)
    formatted_departures = format_departures(all_departures)
    
    with open('hkg_arrivals_formatted.json', 'w', encoding='utf-8') as f:
        json.dump(formatted_arrivals, f, ensure_ascii=False, indent=2)
    
    with open('hkg_departures_formatted.json', 'w', encoding='utf-8') as f:
        json.dump(formatted_departures, f, ensure_ascii=False, indent=2)
    
    # Also create a CSV version
    create_csv(formatted_arrivals, formatted_departures)
    
    print(f"Formatted data saved to hkg_arrivals_formatted.json and hkg_departures_formatted.json")
    print(f"CSV data saved to hkg_flights.csv")

def format_arrivals(flights):
    """Format arrivals for data system use"""
    records = []
    for f in flights:
        # Get primary flight number
        flight_list = f.get('flight', [])
        primary_flight = flight_list[0] if flight_list else {}
        
        # Get all codeshare flight numbers
        all_flight_nos = [fl.get('no', '') for fl in flight_list]
        all_airlines = list(set([fl.get('airline', '') for fl in flight_list]))
        
        record = {
            'date': f.get('_date', ''),
            'time': f.get('time', ''),
            'flight_number': primary_flight.get('no', ''),
            'airline_code': primary_flight.get('airline', ''),
            'origin': ','.join(f.get('origin', [])),
            'status': f.get('status', ''),
            'status_code': f.get('statusCode', ''),
            'all_flight_numbers': '|'.join(all_flight_nos),
            'all_airlines': '|'.join(all_airlines),
            'terminal': f.get('terminal', ''),
            'hall': f.get('hall', ''),
            'belt': f.get('baggage', '') or f.get('belt', ''),
            'parking_stand': f.get('stand', '') or f.get('parkingStand', ''),
        }
        records.append(record)
    
    # Sort by date and time
    records.sort(key=lambda x: (x['date'], x['time']))
    return records

def format_departures(flights):
    """Format departures for data system use"""
    records = []
    for f in flights:
        flight_list = f.get('flight', [])
        primary_flight = flight_list[0] if flight_list else {}
        
        all_flight_nos = [fl.get('no', '') for fl in flight_list]
        all_airlines = list(set([fl.get('airline', '') for fl in flight_list]))
        
        record = {
            'date': f.get('_date', ''),
            'time': f.get('time', ''),
            'flight_number': primary_flight.get('no', ''),
            'airline_code': primary_flight.get('airline', ''),
            'destination': ','.join(f.get('destination', [])),
            'status': f.get('status', ''),
            'status_code': f.get('statusCode', ''),
            'all_flight_numbers': '|'.join(all_flight_nos),
            'all_airlines': '|'.join(all_airlines),
            'terminal': f.get('terminal', ''),
            'aisle': f.get('aisle', ''),
            'gate': f.get('gate', ''),
        }
        records.append(record)
    
    records.sort(key=lambda x: (x['date'], x['time']))
    return records

def create_csv(arrivals, departures):
    """Create CSV files"""
    import csv
    
    # Arrivals CSV
    if arrivals:
        with open('hkg_arrivals.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=arrivals[0].keys())
            writer.writeheader()
            writer.writerows(arrivals)
    
    # Departures CSV
    if departures:
        with open('hkg_departures.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=departures[0].keys())
            writer.writeheader()
            writer.writerows(departures)

if __name__ == '__main__':
    main()
