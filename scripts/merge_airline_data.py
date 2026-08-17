#!/usr/bin/env python
"""
Merge airline info (logo, check-in aisle, transfer desk) into flight data files
"""
import json
import csv

def load_airline_info():
    """Load airline information"""
    with open('hkg_airlines_info.json', 'r', encoding='utf-8') as f:
        airlines = json.load(f)
    
    # Build lookup by airline_code (IATA 3-letter) and iata_code (IATA 2-letter)
    lookup = {}
    for a in airlines:
        code = a.get('airline_code', '')
        iata = a.get('iata_code', '')
        if code:
            lookup[code] = a
        if iata and iata != code:
            lookup[iata] = a
    
    return airlines, lookup

def enrich_flight(flight, airline_lookup):
    """Add airline info to a single flight record"""
    code = flight.get('airline_code', '')
    info = airline_lookup.get(code, {})
    
    if info:
        flight['airline_name'] = info.get('name_en', '')
        flight['airline_logo_url'] = info.get('logo_url', '')
        flight['check_in_aisle'] = info.get('check_in_aisle', '')
        flight['transfer_desk'] = info.get('transfer_desk', 'N/A')
        flight['airline_terminal'] = info.get('terminal', '')
        flight['airline_website'] = info.get('website', '')
    else:
        flight['airline_name'] = ''
        flight['airline_logo_url'] = ''
        flight['check_in_aisle'] = ''
        flight['transfer_desk'] = 'N/A'
        flight['airline_terminal'] = ''
        flight['airline_website'] = ''
    
    return flight

def main():
    airlines_list, airline_lookup = load_airline_info()
    print(f"Loaded {len(airlines_list)} airlines, lookup has {len(airline_lookup)} entries")
    
    # Load flight data
    with open('hkg_arrivals_final.json', 'r', encoding='utf-8') as f:
        arrivals = json.load(f)
    with open('hkg_departures_final.json', 'r', encoding='utf-8') as f:
        departures = json.load(f)
    
    print(f"Loaded {len(arrivals)} arrivals, {len(departures)} departures")
    
    # Enrich arrivals
    matched_arr = 0
    for flight in arrivals:
        enrich_flight(flight, airline_lookup)
        if flight.get('airline_name'):
            matched_arr += 1
    
    # Enrich departures
    matched_dep = 0
    for flight in departures:
        enrich_flight(flight, airline_lookup)
        if flight.get('airline_name'):
            matched_dep += 1
    
    print(f"Arrivals matched with airline info: {matched_arr}/{len(arrivals)} ({matched_arr*100/len(arrivals):.1f}%)")
    print(f"Departures matched with airline info: {matched_dep}/{len(departures)} ({matched_dep*100/len(departures):.1f}%)")
    
    # Save enriched JSON
    with open('hkg_arrivals_enriched.json', 'w', encoding='utf-8') as f:
        json.dump(arrivals, f, ensure_ascii=False, indent=2)
    with open('hkg_departures_enriched.json', 'w', encoding='utf-8') as f:
        json.dump(departures, f, ensure_ascii=False, indent=2)
    
    # Save enriched CSV
    if arrivals:
        with open('hkg_arrivals_enriched.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=arrivals[0].keys())
            writer.writeheader()
            writer.writerows(arrivals)
    if departures:
        with open('hkg_departures_enriched.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=departures[0].keys())
            writer.writeheader()
            writer.writerows(departures)
    
    # Save airlines info as CSV too
    if airlines_list:
        # Normalize keys
        all_keys = set()
        for a in airlines_list:
            all_keys.update(a.keys())
        fieldnames = sorted(all_keys)
        with open('hkg_airlines_info.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(airlines_list)
    
    # Sample enriched record
    print("\n=== ENRICHED ARRIVAL SAMPLE ===")
    print(json.dumps(arrivals[50], indent=2, ensure_ascii=False))
    print("\n=== ENRICHED DEPARTURE SAMPLE ===")
    print(json.dumps(departures[50], indent=2, ensure_ascii=False))
    
    # Count airlines with transfer desk vs N/A
    transfer_na = sum(1 for a in airlines_list if a.get('transfer_desk') == 'N/A')
    transfer_yes = len(airlines_list) - transfer_na
    print(f"\n=== AIRLINE INFO STATS ===")
    print(f"Total airlines: {len(airlines_list)}")
    print(f"With transfer desk: {transfer_yes}")
    print(f"Transfer desk = N/A: {transfer_na}")

if __name__ == '__main__':
    main()
