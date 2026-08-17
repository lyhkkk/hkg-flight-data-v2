#!/usr/bin/env python
"""
Fetch HKIA airline information: logo, check-in aisle, transfer desk
"""
import json
import re
import urllib.request
from html.parser import HTMLParser

BASE_URL = "https://www.hongkongairport.com"
ICON_DIR = "/iwov-resources/image/flights/airline-information/"

def fetch_html():
    """Fetch the airlines page"""
    url = f"{BASE_URL}/en/flights/airlines-information/airlines.page"
    print(f"Fetching {url} ...")
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode('utf-8')

def fetch_api_airlines():
    """Fetch airline codes from API"""
    url = f"{BASE_URL}/flightinfo-rest/rest/airlines"
    print(f"Fetching {url} ...")
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode('utf-8'))

def parse_airlines_from_html(html):
    """Parse airline info from HTML page"""
    airlines = []
    
    # Find all airline data blocks using data-filter
    # Pattern: <div class="data accordionItemMobile" data-filter="...">
    pattern = r'<div class="data accordionItemMobile" data-filter="([^"]*)">(.*?)(?=<div class="data accordionItemMobile" data-filter="|$)'
    blocks = re.findall(pattern, html, re.DOTALL)
    
    print(f"Found {len(blocks)} airline blocks")
    
    for filter_str, block in blocks:
        airline = {}
        
        # Parse data-filter: "Airline Name CN EN icon_code IATA_CODE ISO_CODE TERMINAL ... groupN"
        filter_parts = filter_str.strip().split()
        
        # Extract icon filename
        icon_match = re.search(r'(wm[a-z0-9]+)', filter_str)
        if icon_match:
            airline['icon_code'] = icon_match.group(1)
            ext = '.gif'  # default
            # Check if png
            if f'{icon_match.group(1)}.png' in block:
                ext = '.png'
            airline['logo_url'] = f"{BASE_URL}{ICON_DIR}{icon_match.group(1)}{ext}"
        
        # Extract airline name (first part before Chinese)
        name_match = re.match(r'^([A-Za-z0-9\s&\'-]+)', filter_str)
        if name_match:
            airline['name_en'] = name_match.group(1).strip()
        
        # Extract IATA code and airline code
        codes = re.findall(r'\b([A-Z]{2,3})\b', filter_str)
        # Filter out common non-airline words
        skip_codes = {'T1', 'T2', 'group', 'ALL'}
        iata_codes = [c for c in codes if c not in skip_codes and len(c) <= 3]
        if len(iata_codes) >= 2:
            airline['airline_code'] = iata_codes[-2]  # IATA airline code (e.g., CPA)
            airline['iata_code'] = iata_codes[-1]      # IATA 2-letter (e.g., CX)
        elif len(iata_codes) == 1:
            airline['airline_code'] = iata_codes[0]
            airline['iata_code'] = iata_codes[0]
        
        # Extract terminal
        term_match = re.search(r'\b(T[12])\b', filter_str)
        if term_match:
            airline['terminal'] = term_match.group(1)
        
        # Extract check-in aisle from block
        aisle_match = re.search(r'data-map-category="Check_in_Aisle"[^>]*data-map-location="([^"]*)"', block)
        if aisle_match:
            airline['check_in_aisle'] = aisle_match.group(1)
        else:
            # Try alternate pattern
            aisle_match2 = re.search(r'aria-label="AISLE:\s*([^"]*)"', block)
            if aisle_match2:
                airline['check_in_aisle'] = aisle_match2.group(1)
            else:
                airline['check_in_aisle'] = ''
        
        # Extract transfer desk from block
        desk_match = re.search(r'data-map-category="Transfer_Desk"[^>]*data-map-location="([^"]*)"', block)
        if desk_match:
            airline['transfer_desk'] = desk_match.group(1)
        else:
            # Check if deskData contains just "-"
            desk_block = re.search(r'class="deskData"[^>]*>(.*?)</div>', block, re.DOTALL)
            if desk_block:
                desk_text = desk_block.group(1).strip().replace('-', '').strip()
                if desk_text and 'aria-label' in desk_text:
                    desk_label = re.search(r'aria-label="TRANSFER DESK:\s*([^"]*)"', desk_text)
                    if desk_label:
                        airline['transfer_desk'] = desk_label.group(1)
                    else:
                        airline['transfer_desk'] = 'N/A'
                else:
                    airline['transfer_desk'] = 'N/A'
            else:
                airline['transfer_desk'] = 'N/A'
        
        # Extract website
        web_match = re.search(r'aria-label="airline website:\s*([^"]*)"', block)
        if web_match:
            airline['website'] = web_match.group(1)
        
        # Extract reservations phone
        res_match = re.search(r'aria-label="RESERVATIONS:\s*([^"]*)"', block)
        if res_match:
            airline['reservations'] = res_match.group(1)
        
        # Extract general enquiries phone
        enq_match = re.search(r'aria-label="GENERAL ENQUIRIES:\s*([^"]*)"', block)
        if enq_match:
            airline['general_enquiries'] = enq_match.group(1)
        
        if airline.get('name_en') or airline.get('iata_code'):
            airlines.append(airline)
    
    return airlines

def merge_with_api(airlines, api_data):
    """Merge HTML data with API data to fill in missing codes"""
    # Build lookup from API
    api_lookup = {}
    for item in api_data:
        code = item.get('code', '')
        desc = item.get('description', [])
        icon = item.get('icon', '')
        if desc:
            api_lookup[code] = {
                'name_cn_trad': desc[0] if len(desc) > 0 else '',
                'name_cn_simp': desc[1] if len(desc) > 1 else '',
                'name_en': desc[2] if len(desc) > 2 else '',
                'icon': icon,
            }
    
    # Try to match and enrich
    for airline in airlines:
        iata = airline.get('iata_code', '')
        if iata in api_lookup:
            api_info = api_lookup[iata]
            if not airline.get('name_cn_trad'):
                airline['name_cn_trad'] = api_info['name_cn_trad']
            if not airline.get('name_cn_simp'):
                airline['name_cn_simp'] = api_info['name_cn_simp']
    
    return airlines

def main():
    html = fetch_html()
    api_data = fetch_api_airlines()
    
    airlines = parse_airlines_from_html(html)
    airlines = merge_with_api(airlines, api_data)
    
    # Sort by IATA code
    airlines.sort(key=lambda x: x.get('iata_code', ''))
    
    print(f"\nTotal airlines parsed: {len(airlines)}")
    
    # Stats
    with_aisle = sum(1 for a in airlines if a.get('check_in_aisle'))
    with_desk = sum(1 for a in airlines if a.get('transfer_desk') and a['transfer_desk'] != 'N/A')
    with_logo = sum(1 for a in airlines if a.get('logo_url'))
    print(f"  With check-in aisle: {with_aisle}")
    print(f"  With transfer desk: {with_desk}")
    print(f"  With logo: {with_logo}")
    
    # Sample
    print("\n=== SAMPLE ===")
    for a in airlines[:3]:
        print(json.dumps(a, indent=2, ensure_ascii=False))
    
    # Save
    with open('hkg_airlines_info.json', 'w', encoding='utf-8') as f:
        json.dump(airlines, f, ensure_ascii=False, indent=2)
    
    print(f"\nSaved to hkg_airlines_info.json")

if __name__ == '__main__':
    main()
