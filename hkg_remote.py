#!/usr/bin/env python3
"""
HKG Flight Data — 远程实时查询系统
无需传文件，直接调用 HKIA 官方 API
"""
import json
import os
import sys
import urllib.request
from datetime import date, timedelta

# ========== 配置 ==========
API_BASE = "https://www.hongkongairport.com/flightinfo-rest/rest"
CACHE_DIR = os.path.expanduser("~/.hkg_cache")
CACHE_EXPIRY = 3600  # 缓存1小时

# ========== API 调用 ==========
def api_call(endpoint, params=""):
    """调用 HKIA API"""
    url = f"{API_BASE}/{endpoint}?{params}"
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (Linux; Android 10) Termux',
        'Accept': 'application/json',
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        return {"error": str(e)}

def fetch_flights(dt, flight_type=""):
    """获取某天的航班数据"""
    os.makedirs(CACHE_DIR, exist_ok=True)
    cache_file = os.path.join(CACHE_DIR, f"flights_{dt}.json")

    # 检查缓存
    if os.path.exists(cache_file):
        age = os.time.time() - os.path.getmtime(cache_file)
        if age < CACHE_EXPIRY:
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)

    today = date.today()
    target = date.fromisoformat(dt)

    if target < today:
        endpoint = "flights/past"
    else:
        endpoint = "flights"

    data = api_call(endpoint, f"date={dt}&span=1")

    if isinstance(data, list):
        # 写入缓存
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
        return data
    return data

def fetch_airlines():
    """获取航空公司数据"""
    cache_file = os.path.join(CACHE_DIR, "airlines.json")
    if os.path.exists(cache_file):
        with open(cache_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    data = api_call("airlines")
    if isinstance(data, list):
        os.makedirs(CACHE_DIR, exist_ok=True)
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
        return data
    return []

def parse_flights(raw_data):
    """解析 API 数据"""
    arrivals = []
    departures = []

    if not isinstance(raw_data, list):
        return arrivals, departures

    for entry in raw_data:
        if entry.get('cargo'):
            continue
        for flight in entry.get('list', []):
            record = {
                'date': entry.get('date', ''),
                'time': flight.get('time', ''),
                'flight_number': flight.get('flight', [{}])[0].get('no', '') if flight.get('flight') else '',
                'airline_code': flight.get('flight', [{}])[0].get('airline', '') if flight.get('flight') else '',
                'status': flight.get('status', ''),
                'all_flight_numbers': '|'.join(fl.get('no', '') for fl in flight.get('flight', [])),
                'terminal': flight.get('terminal', ''),
                'gate': flight.get('gate', ''),
                'aisle': flight.get('aisle', ''),
                'hall': flight.get('hall', ''),
                'belt': flight.get('belt', ''),
            }

            if entry.get('arrival'):
                record['type'] = 'arrival'
                record['origin'] = ','.join(flight.get('origin', []))
                arrivals.append(record)
            else:
                record['type'] = 'departure'
                record['destination'] = ','.join(flight.get('destination', []))
                departures.append(record)

    return arrivals, departures

def search_flight(flight_number, date_str=None):
    """搜索航班"""
    fn = flight_number.upper().replace(' ', '')
    results = []

    if date_str:
        dates_to_search = [date_str]
    else:
        # 搜索最近3天
        today = date.today()
        dates_to_search = [
            (today - timedelta(days=1)).isoformat(),
            today.isoformat(),
            (today + timedelta(days=1)).isoformat(),
        ]

    for dt in dates_to_search:
        raw = fetch_flights(dt)
        arr, dep = parse_flights(raw)
        for f in arr + dep:
            fn_clean = f.get('flight_number', '').upper().replace(' ', '')
            all_fn = f.get('all_flight_numbers', '').upper().replace(' ', '')
            if fn == fn_clean or fn in all_fn:
                results.append(f)

    return results

# ========== Web 服务器 ==========
def run_web(port=8080):
    """启动 Web 服务器"""
    from http.server import HTTPServer, SimpleHTTPRequestHandler
    from urllib.parse import urlparse, parse_qs

    class Handler(SimpleHTTPRequestHandler):
        def do_GET(self):
            parsed = urlparse(self.path)
            params = parse_qs(parsed.query)

            self.send_header('Access-Control-Allow-Origin', '*')

            if parsed.path == '/':
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write(get_web_ui().encode('utf-8'))

            elif parsed.path == '/api/search':
                fn = params.get('flight', [''])[0]
                dt = params.get('date', [None])[0]
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                results = search_flight(fn, dt)
                self.wfile.write(json.dumps(results, ensure_ascii=False).encode('utf-8'))

            elif parsed.path == '/api/airlines':
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                airlines = fetch_airlines()
                self.wfile.write(json.dumps(airlines, ensure_ascii=False).encode('utf-8'))

            else:
                self.send_response(404)
                self.end_headers()

    print(f"\n✈  HKG Remote Flight Data Server")
    print(f"   http://localhost:{port}")
    print(f"   http://127.0.0.1:{port}")
    print(f"\n   Direct API: /api/search?flight=CX759")
    print(f"   Press Ctrl+C to stop\n")

    server = HTTPServer(('0.0.0.0', port), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
        server.server_close()


def get_web_ui():
    return '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>HKG Remote Flight Data</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,sans-serif;background:#0f1923;color:#fff;min-height:100vh;padding:16px}
h1{text-align:center;color:#faa718;margin:16px 0;font-size:20px}
.info{text-align:center;color:#8fa4c4;font-size:12px;margin-bottom:16px}
.search-box{max-width:500px;margin:0 auto 20px}
.search-box input{width:100%;padding:14px;border:1px solid rgba(255,255,255,0.2);border-radius:10px;background:rgba(255,255,255,0.08);color:#fff;font-size:16px;margin-bottom:10px}
.search-box button{width:100%;padding:14px;border:none;border-radius:10px;background:#faa718;color:#000;font-size:16px;font-weight:600;cursor:pointer}
.results{max-width:500px;margin:0 auto}
.card{background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.1);border-radius:12px;padding:16px;margin-bottom:12px}
.card .fn{font-size:20px;font-weight:700;color:#faa718}
.card .route{margin:6px 0;font-size:15px}
.card .status{color:#4ade80;font-weight:600;margin:6px 0}
.card .meta{font-size:12px;color:#8fa4c4;line-height:1.8}
.tag{display:inline-block;background:rgba(250,167,24,0.15);color:#faa718;padding:2px 8px;border-radius:12px;font-size:11px;margin:2px}
</style>
</head>
<body>
<h1>✈ HKG Remote Flight Data</h1>
<div class="info">Real-time data from HKIA API · No file transfer needed</div>
<div class="search-box">
  <input id="fn" placeholder="Flight number (e.g. CX759)" onkeydown="if(event.key==='Enter')search()">
  <button onclick="search()">Search</button>
</div>
<div class="results" id="r"></div>
<script>
async function search(){
  const fn=document.getElementById('fn').value.trim();
  if(!fn)return;
  document.getElementById('r').innerHTML='<p style="text-align:center;color:#8fa4c4">Loading...</p>';
  const res=await fetch(`/api/search?flight=${encodeURIComponent(fn)}`);
  const data=await res.json();
  if(!data.length){document.getElementById('r').innerHTML='<p style="text-align:center;color:#8fa4c4">No results</p>';return}
  document.getElementById('r').innerHTML=data.map(f=>`
    <div class="card">
      <div class="fn">${f.flight_number} <span class="tag">${f.type}</span></div>
      <div class="route">${f.type==='arrival'?f.origin+' → HKG':'HKG → '+f.destination}</div>
      <div class="status">${f.status||'Scheduled'}</div>
      <div class="meta">
        📅 ${f.date} ${f.time} · ${f.terminal||'-'}<br>
        ${f.gate?'🚪 Gate '+f.gate+' · ':''}${f.aisle?'Aisle '+f.aisle+' · ':''}
        ${f.hall?'Hall '+f.hall:''}
      </div>
    </div>
  `).join('');
}
</script>
</body>
</html>'''


# ========== CLI 模式 ==========
def run_cli():
    """命令行模式"""
    if len(sys.argv) < 3:
        print("Usage:")
        print("  python hkg_remote.py search CX759")
        print("  python hkg_remote.py search CX759 2026-08-16")
        print("  python hkg_remote.py web")
        return

    cmd = sys.argv[1]

    if cmd == 'web':
        port = int(sys.argv[2]) if len(sys.argv) > 2 else 8080
        run_web(port)

    elif cmd == 'search':
        fn = sys.argv[2]
        dt = sys.argv[3] if len(sys.argv) > 3 else None
        results = search_flight(fn, dt)

        if not results:
            print(f"No results for {fn}")
            return

        for f in results:
            tp = '→' if f.get('type') == 'departure' else '←'
            dest = f.get('destination', f.get('origin', ''))
            print(f"\n{'='*40}")
            print(f"  {f['flight_number']}  |  {f['type'].upper()}")
            print(f"  Route:  HKG {tp} {dest}")
            print(f"  Date:   {f['date']}  {f['time']}")
            print(f"  Status: {f.get('status', 'Scheduled')}")
            print(f"  Terminal: {f.get('terminal', '-')}")
            print(f"  Gate:     {f.get('gate', '-')}")
            print(f"  Aisle:    {f.get('aisle', '-')}")
            print(f"  Hall:     {f.get('hall', '-')}")
            print(f"  Belt:     {f.get('belt', '-')}")
        print(f"\n{'='*40}")
        print(f"Total: {len(results)} results")


if __name__ == '__main__':
    run_cli()
