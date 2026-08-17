#!/usr/bin/env python3
"""
Termux 航班数据查询系统
轻量级 TUI + Web 双模式
"""

import json
import os
import sys
from datetime import datetime

# ========== 数据库 ==========
class FlightDB:
    def __init__(self, data_dir='.'):
        self.arrivals = []
        self.departures = []
        self.airlines = {}
        self.load(data_dir)

    def load(self, data_dir):
        arr_path = os.path.join(data_dir, 'hkg_arrivals_enriched.json')
        dep_path = os.path.join(data_dir, 'hkg_departures_enriched.json')
        air_path = os.path.join(data_dir, 'hkg_airlines_info.json')

        if os.path.exists(arr_path):
            with open(arr_path, 'r', encoding='utf-8') as f:
                self.arrivals = json.load(f)
        if os.path.exists(dep_path):
            with open(dep_path, 'r', encoding='utf-8') as f:
                self.departures = json.load(f)
        if os.path.exists(air_path):
            with open(air_path, 'r', encoding='utf-8') as f:
                for a in json.load(f):
                    code = a.get('airline_code', '')
                    if code:
                        self.airlines[code] = a

    def search_flight(self, flight_number, date=None):
        """搜索航班"""
        results = []
        fn = flight_number.upper().replace(' ', '')

        for f in self.arrivals + self.departures:
            fn_clean = f.get('flight_number', '').upper().replace(' ', '')
            all_fn = f.get('all_flight_numbers', '').upper().replace(' ', '')
            if fn == fn_clean or fn in all_fn:
                if date and f.get('date') != date:
                    continue
                results.append(f)
        return results

    def search_by_date(self, date, flight_type='all'):
        """按日期搜索"""
        results = []
        if flight_type in ('all', 'arrival'):
            results += [f for f in self.arrivals if f.get('date') == date]
        if flight_type in ('all', 'departure'):
            results += [f for f in self.departures if f.get('date') == date]
        return results

    def get_airline(self, code):
        """获取航空公司信息"""
        return self.airlines.get(code, {})

    def stats(self):
        """统计信息"""
        dates = set(f.get('date') for f in self.arrivals)
        return {
            'total_arrivals': len(self.arrivals),
            'total_departures': len(self.departures),
            'date_range': f"{min(dates)} ~ {max(dates)}" if dates else "N/A",
            'airlines': len(self.airlines),
        }


# ========== Web 服务器模式 ==========
def run_web_server(data_dir='.', port=8080):
    """启动 Web 服务器，可通过浏览器访问"""
    from http.server import HTTPServer, SimpleHTTPRequestHandler
    import webbrowser

    db = FlightDB(data_dir)

    class Handler(SimpleHTTPRequestHandler):
        def do_GET(self):
            if self.path == '/':
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write(generate_index(db).encode('utf-8'))
            elif self.path.startswith('/api/search'):
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                from urllib.parse import urlparse, parse_qs
                params = parse_qs(urlparse(self.path).query)
                fn = params.get('flight', [''])[0]
                date = params.get('date', [None])[0]
                results = db.search_flight(fn, date)
                self.wfile.write(json.dumps(results, ensure_ascii=False).encode('utf-8'))
            elif self.path.startswith('/api/date'):
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                from urllib.parse import urlparse, parse_qs
                params = parse_qs(urlparse(self.path).query)
                date = params.get('date', [''])[0]
                results = db.search_by_date(date)
                self.wfile.write(json.dumps(results, ensure_ascii=False).encode('utf-8'))
            elif self.path == '/api/stats':
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps(db.stats(), ensure_ascii=False).encode('utf-8'))
            else:
                self.send_response(404)
                self.end_headers()

    print(f"\n✈  HKG Flight Data Server")
    print(f"   http://localhost:{port}")
    print(f"   http://127.0.0.1:{port}")
    print(f"\n   Press Ctrl+C to stop\n")

    server = HTTPServer(('0.0.0.0', port), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
        server.server_close()


def generate_index(db):
    """生成首页 HTML"""
    stats = db.stats()
    dates = sorted(set(f.get('date') for f in db.arrivals))

    date_options = ''.join(f'<option value="{d}">{d}</option>' for d in dates)

    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>HKG Flight Data</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,sans-serif;background:#0f1923;color:#fff;min-height:100vh;padding:16px}}
h1{{text-align:center;color:#faa718;margin:16px 0;font-size:22px}}
.stats{{display:flex;justify-content:center;gap:16px;margin:16px 0;flex-wrap:wrap}}
.stat{{background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);border-radius:10px;padding:12px 20px;text-align:center;min-width:100px}}
.stat-val{{font-size:24px;font-weight:700;color:#faa718}}
.stat-lbl{{font-size:11px;color:#8fa4c4;margin-top:4px}}
.search-box{{max-width:600px;margin:24px auto;background:rgba(255,255,255,0.05);border-radius:12px;padding:20px}}
.search-box input,.search-box select{{width:100%;padding:12px;border:1px solid rgba(255,255,255,0.2);border-radius:8px;background:rgba(0,0,0,0.3);color:#fff;font-size:16px;margin-bottom:12px}}
.search-box button{{width:100%;padding:12px;border:none;border-radius:8px;background:#faa718;color:#000;font-size:16px;font-weight:600;cursor:pointer}}
.search-box button:hover{{background:#e59510}}
.results{{max-width:600px;margin:16px auto}}
.flight-card{{background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);border-radius:12px;padding:16px;margin-bottom:12px}}
.flight-card .fn{{font-size:20px;font-weight:700;color:#faa718}}
.flight-card .route{{font-size:16px;margin:8px 0}}
.flight-card .status{{color:#4ade80;font-weight:600}}
.flight-card .detail{{font-size:12px;color:#8fa4c4;margin-top:8px;line-height:1.8}}
</style>
</head>
<body>
<h1>✈ HKG Flight Data</h1>
<div class="stats">
  <div class="stat"><div class="stat-val">{stats['total_arrivals']}</div><div class="stat-lbl">Arrivals</div></div>
  <div class="stat"><div class="stat-val">{stats['total_departures']}</div><div class="stat-lbl">Departures</div></div>
  <div class="stat"><div class="stat-val">{stats['airlines']}</div><div class="stat-lbl">Airlines</div></div>
  <div class="stat"><div class="stat-val">{len(dates)}</div><div class="stat-lbl">Days</div></div>
</div>
<div class="search-box">
  <input id="fn" placeholder="Flight number (e.g. CX759)">
  <select id="date"><option value="">-- Select date --</option>{date_options}</select>
  <button onclick="search()">Search</button>
</div>
<div class="results" id="results"></div>
<script>
async function search(){{
  const fn=document.getElementById('fn').value;
  const date=document.getElementById('date').value;
  if(!fn&&!date)return;
  let url=fn?`/api/search?flight=${{fn}}`:`/api/date?date=${{date}}`;
  const res=await fetch(url);
  const data=await res.json();
  const el=document.getElementById('results');
  if(!data.length){{el.innerHTML='<p style="text-align:center;color:#8fa4c4">No results</p>';return}}
  el.innerHTML=data.map(f=>`
    <div class="flight-card">
      <div class="fn">${{f.flight_number}}</div>
      <div class="route">${{f.type==='arrival'?f.origin+' → HKG':'HKG → '+f.destination}}</div>
      <div class="status">${{f.status||'Scheduled'}}</div>
      <div class="detail">
        Date: ${{f.date}} | Time: ${{f.time}} | Terminal: ${{f.airline_terminal||f.terminal||'-'}}<br>
        ${{f.gate?'Gate: '+f.gate+' | ':''}}${{f.check_in_aisle?'Check-in: '+f.check_in_aisle:''}}<br>
        Airline: ${{f.airline_name||f.airline_code}} | Transfer: ${{f.transfer_desk||'N/A'}}
      </div>
    </div>
  `).join('');
}}
</script>
</body>
</html>'''


# ========== TUI 模式 ==========
def run_tui(data_dir='.'):
    """终端 TUI 模式"""
    db = FlightDB(data_dir)
    stats = db.stats()

    while True:
        os.system('clear' if os.name != 'nt' else 'cls')
        print("=" * 50)
        print("  ✈  HKG Flight Data System")
        print("=" * 50)
        print(f"  Arrivals: {stats['total_arrivals']}")
        print(f"  Departures: {stats['total_departures']}")
        print(f"  Airlines: {stats['airlines']}")
        print(f"  Date Range: {stats['date_range']}")
        print("-" * 50)
        print("  1. Search by flight number")
        print("  2. Search by date")
        print("  3. Show airline info")
        print("  4. Start web server (browser)")
        print("  0. Exit")
        print("-" * 50)

        choice = input("  Choose: ").strip()

        if choice == '1':
            fn = input("  Flight number: ").strip()
            if fn:
                results = db.search_flight(fn)
                if results:
                    for r in results:
                        print(f"\n  {r['flight_number']} | {r['date']} {r['time']}")
                        tp = '→' if 'destination' in r else '←'
                        dest = r.get('destination', r.get('origin', ''))
                        print(f"  Route: HKG {tp} {dest}")
                        print(f"  Status: {r.get('status', 'Scheduled')}")
                        print(f"  Terminal: {r.get('airline_terminal', r.get('terminal', '-'))}")
                        print(f"  Gate: {r.get('gate', '-')}")
                        print(f"  Check-in: {r.get('check_in_aisle', '-')}")
                        print(f"  Transfer Desk: {r.get('transfer_desk', 'N/A')}")
                else:
                    print("  No results found.")
            input("\n  Press Enter...")

        elif choice == '2':
            date = input("  Date (YYYY-MM-DD): ").strip()
            if date:
                results = db.search_by_date(date)
                print(f"\n  Found {len(results)} flights on {date}")
                for r in results[:20]:
                    tp = '→' if 'destination' in r else '←'
                    dest = r.get('destination', r.get('origin', ''))
                    print(f"  {r['time']} {r['flight_number']:8s} {tp} {dest:5s} {r.get('status', 'Sched')}")
                if len(results) > 20:
                    print(f"  ... and {len(results)-20} more")
            input("\n  Press Enter...")

        elif choice == '3':
            code = input("  Airline code (e.g. CPA): ").strip().upper()
            info = db.get_airline(code)
            if info:
                print(f"\n  Name: {info.get('name_en', 'N/A')}")
                print(f"  IATA: {info.get('iata_code', 'N/A')}")
                print(f"  Logo: {info.get('logo_url', 'N/A')}")
                print(f"  Check-in: {info.get('check_in_aisle', 'N/A')}")
                print(f"  Transfer: {info.get('transfer_desk', 'N/A')}")
                print(f"  Website: {info.get('website', 'N/A')}")
            else:
                print("  Airline not found.")
            input("\n  Press Enter...")

        elif choice == '4':
            port = input("  Port [8080]: ").strip() or '8080'
            run_web_server(data_dir, int(port))

        elif choice == '0':
            break


# ========== 入口 ==========
if __name__ == '__main__':
    data_dir = sys.argv[1] if len(sys.argv) > 1 else '.'

    if '--web' in sys.argv:
        port = 8080
        for i, arg in enumerate(sys.argv):
            if arg == '--port' and i+1 < len(sys.argv):
                port = int(sys.argv[i+1])
        run_web_server(data_dir, port)
    else:
        run_tui(data_dir)
