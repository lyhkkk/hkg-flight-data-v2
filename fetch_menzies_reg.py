#!/usr/bin/env python3
"""
Fetch aircraft registration from Menzies LSD API (free, no auth)
https://fvm.menziescnac.com/flights
"""
import json
import os
import time
import urllib.request

API_URL = "https://fvm.menziescnac.com/flights"
CACHE_DIR = os.path.expanduser("~/.hkg_cache/menzies")
CACHE_EXPIRY = 300  # 5 minutes (real-time data)


def fetch_lsd():
    """Fetch Landing Status Data from Menzies"""
    os.makedirs(CACHE_DIR, exist_ok=True)
    cache_file = os.path.join(CACHE_DIR, "lsd.json")

    # Check cache
    if os.path.exists(cache_file):
        age = time.time() - os.path.getmtime(cache_file)
        if age < CACHE_EXPIRY:
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)

    req = urllib.request.Request(API_URL, headers={
        'User-Agent': 'Mozilla/5.0',
        'Accept': 'application/json',
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False)
            return data
    except Exception as e:
        print(f"Error fetching Menzies LSD: {e}")
        return []


def lookup_reg(flight_id):
    """Look up registration for a flight ID (e.g., 'CX469', 'MM067')"""
    flights = fetch_lsd()
    fn = flight_id.upper().replace(' ', '')
    for f in flights:
        if f.get('flight_id', '').upper().replace(' ', '') == fn:
            return {
                'tailNumber': f.get('REG', ''),
                'equipment': f.get('SUBTYPE', ''),
                'origin': f.get('ORIG', ''),
                'stand': f.get('STAND', ''),
                'runway': f.get('RWY', ''),
                'ata': f.get('ATA', ''),
                'eta': f.get('ETA', ''),
            }
    return None


def get_all_regs():
    """Get all flight->reg mappings as dict"""
    flights = fetch_lsd()
    return {
        f.get('flight_id', ''): f.get('REG', '')
        for f in flights
        if f.get('flight_id') and f.get('REG')
    }


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        fn = sys.argv[1]
        r = lookup_reg(fn)
        if r:
            print(json.dumps(r, indent=2, ensure_ascii=False))
        else:
            print(f"No data for {fn}")
    else:
        regs = get_all_regs()
        print(f"Total flights with reg: {len(regs)}")
        for fn, reg in list(regs.items())[:10]:
            print(f"  {fn}: {reg}")
