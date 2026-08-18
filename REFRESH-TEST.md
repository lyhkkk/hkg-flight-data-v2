# 手动刷新航班数据（Refresh data）— 测试说明

**日期：** 2026-08-18
**范围：** 仅当前目录 `O:\lyh\Projects\hkia\hkg-flight-data-v2`
**网络：** 允许访问 HKIA（本项目的数据来源），单日期抓取、短超时，保持礼貌。

## 1. 改动说明（改动内容）

在 `hkg_termux.py` 中新增了「手动刷新航班数据」功能：

- 新增函数 **`run_refresh(db, data_dir='.')`**：
  - 复用项目自身 `scripts/fetch_flights.py`（`fetch_date` / `format_arrivals` / `format_departures`）
    与 `scripts/merge_airline_data.py`（`load_airline_info` / `enrich_flight`）的抓取/格式化/富化管线，
    不重复造轮子。
  - **只抓取「今天」的数据**，调用普通端点（`?date=今天&span=1`），非 `past` 端点。
  - 抓取后解析出今天的乘客到达/出发航班，格式化并合并航司信息。
  - **原地合入** `hkg_arrivals_enriched.json` / `hkg_departures_enriched.json`：
    仅替换日期 == 今天的记录，其它日期的记录全部保留，避免覆盖历史数据。
  - 写入后**重新加载内存中的 FlightDB**（`db.arrivals` / `db.departures`），
    使后续搜索立即看到最新状态。
  - 成功返回 `(arrivals_count, departures_count)`；失败（离线/API 异常/空数据）返回 `None`，
    不会崩溃。

- TUI 主菜单新增选项：
  ```
  0. 刷新航班数据 (Refresh data)
  q. 退出 (Exit)
  ```
  （原「0. Exit」改为 `q` 退出；`0` 现在用于刷新。）

## 2. 菜单用法

```bash
python hkg_termux.py .
```

在主菜单中选择 **0（刷新航班数据）**，程序会：

1. 显示 `Fetching HKIA data for 2026-08-18 ...`
2. 抓取并更新今天的航班数据到 enriched JSON 文件。
3. 打印确认，例如：`✓ Refreshed: 457 arrivals / 446 departures`
4. 自动重载内存数据并显示最新统计（Arrivals / Departures）。
5. 按 Enter 返回主菜单。

刷新失败（无网络 / API 不可用）时打印：
`刷新失败：请检查网络或稍后再试。` 并返回主菜单，不会中断程序。

## 3. 测试输出

### (a) 语法检查

```
python -m py_compile hkg_termux.py   →  PY_COMPILE_OK
```

### (b) 直接调用 refresh 函数

```
python -c "import hkg_termux; db=hkg_termux.FlightDB('.'); print(hkg_termux.run_refresh(db, '.'))"

刷新前 DB：7171 到达 / 7171 出发
  Fetching HKIA data for 2026-08-18 ...
  Fetching .../rest/flights?date=2026-08-18&span=1 ... OK - 10 entries, 1179 flights
  ✓ Refreshed: 457 arrivals / 446 departures
RESULT: (457, 446)
刷新后 DB：7177 到达 / 7176 出发（今天的记录已更新，其它日期保留）
```

文件 mtime / 大小变化（刷新前 22:14 → 刷新后 03:40，且体积变化）：

```
hkg_arrivals_enriched.json    4626855 → 4631608 bytes
hkg_departures_enriched.json  4482623 → 4486392 bytes
```

### (c) 通过菜单选择（stdin 管道模拟）

```
printf "0\n\nq\n" | python hkg_termux.py .

  Choose:
  Fetching HKIA data for 2026-08-18 ...
  Fetching .../rest/flights?date=2026-08-18&span=1 ... OK - 10 entries, 1179 flights
  ✓ Refreshed: 457 arrivals / 446 departures
  ...
  （按 Enter 返回菜单，再输入 q 正常退出，退出码 0）
```

`0` 成功进入刷新流程并返回主菜单。

## 4. 失败处理（离线 / API 不可用）

对 `run_refresh` 做异常/空数据注入测试，均返回 `None`、打印友好提示、不崩溃：

```
空数据（模拟离线）：
  Fetching HKIA data for 2026-08-18 ...
  ✗ No data returned (offline or API down).
  → run_refresh 返回 None，TUI 打印「刷新失败：请检查网络或稍后再试。」

网络异常（模拟 connection refused）：
  ✗ Fetch failed (offline/API error): connection refused
  → run_refresh 返回 None，TUI 同上处理。
```

## 结论

- 手动刷新功能可用：**菜单按 `0` 即可**抓取今天最新航班并刷新内存数据，之后搜索能看到新状态。
- 其它日期的历史数据不受影响（仅替换当天记录）。
- 离线 / API 故障时安全降级，不会使 TUI 崩溃。

---

## 窗口跨天修复 + S/G 列

**改动内容（hkg_termux.py）：**

1. **窗口跨天修复（`run_refresh` 刷新跨天问题）**
   - 旧版 `run_refresh` 只抓取「今天」并只原地合入 `date == 今天` 的记录；
     午夜后将 12h ~ +2h 搜索窗内、但日期属于昨天的航班漏刷（如 NH 811 8-17 仍是
     "Est at 21:57"）。
   - 新版 `run_refresh` **同时抓取昨天与今天**：
     - 昨天 → `flights/past?date=<昨天>&span=1`（past 端点）；
     - 今天 → `flights?date=<今天>&span=1`（普通端点）。
   - 两个日期都走项目的 `fetch_date` / `format_arrivals` / `format_departures` /
     `enrich_flight` 管线，然后**原地合入**：仅替换 `date == <昨天>` 与
     `date == <今天>` 的记录，其它日期全部保留。
   - 合并后重载内存 `FlightDB`，并按日期打印刷新数量。
   - `_in_window` 不变，仍为 12h 前 ~ +2h 后；昨天在窗内的航班现在会拿到最新 status。

2. **S/G（Stand/Gate）列**
   - `_print_results` 结果表新增 **`S/G`** 列（表头在 Route 与 Status 之间）。
   - 到达（ARR）显示 `parking_stand`（如 W63），出发（DEP）显示 `gate`（如 10、20）。
   - 若同一航班同时有 stand 与 gate 且不同，显示 `stand/gate`；否则取非空值，缺省 `-`。
   - 新增辅助函数 `_pick_stand_gate(r)`。

**验证结果（实测）：**

- 语法检查：`python -m py_compile hkg_termux.py` → `PY_COMPILE_OK`
- 刷新（一次抓昨天+今天）：
  ```
  Fetching 2026-08-17 (yesterday) ... past ... 459 arrivals / 454 departures
  Fetching 2026-08-18 (today)     ...           457 arrivals / 446 departures
  ✓ Refreshed [2026-08-17 / 2026-08-18]: 916 arrivals / 900 departures
  RESULT: (916, 900)
  ```
- NH 811 2026-08-17 状态：修复前 `Est at 21:57` → 修复后 **`At gate 22:05`**（与 live API 一致），
  `parking_stand = W63`。
- S/G 列实测（`_print_results`）：
  ```
  ARR   NH 811   2026-08-17  NRT→HKG   W63   At gate 22:05
  DEP   ZE 862   2026-08-17  HKG→ICN   20    Dep 00:11
  DEP   CX 261   2026-08-17  HKG→CDG   23    Dep 00:11
  ```

**已知（与本改动无关）：** 菜单快速查询输入 `NH 811`（带空格）会进入“数字/站坪”分支，
且站坪/航班号搜索对带空格的分支不影响 S/G 列本身；S/G 列功能已单独用
`_print_results` 验证通过。

---

## 动态36h窗口

**改动内容（hkg_termux.py，仅 `run_refresh`）：**

1. **动态滚动窗口**：不再固定抓昨天+今天，而是计算
   `start_date = (now - 12h).date()`、`end_date = (now + 24h).date()`，
   抓取 `[start_date, end_date]` 区间内所有日期（最多 3 天）。
2. **端点选择**：过去日期（`date < today`）用 `flights/past`，
   今天/未来用普通 `flights` 端点，继续复用
   `scripts/fetch_flights.py` 的 `fetch_date` / `format_arrivals` / `format_departures`
   与 `scripts/merge_airline_data.py` 的 `load_airline_info` / `enrich_flight`。
3. **逐日期原地合并**：每个成功抓取的日期只替换 enriched JSON 中
   `date == 该日期` 的记录，其它日期全部保留。
4. **单日失败不中断**：某一天离线/空数据只打印 `✗` 并跳过，
   其它日期继续刷新；全部日期都失败才返回 `None`。
5. **合并后重载内存 DB**：`db.arrivals` / `db.departures` 更新为合并后的数据，
   并按日期打印到达/出发数量。

**本次实测窗口（2026-08-18 15:08 运行）：**

- `now - 12h` → `2026-08-18 03:08`，所在日期 `2026-08-18`
- `now + 24h` → `2026-08-19 15:08`，所在日期 `2026-08-19`
- 因此本次抓取 **2 个日期**：`2026-08-18`、`2026-08-19`

**测试输出：**

```
python -m py_compile hkg_termux.py   →  PY_COMPILE_OK

python -c "import hkg_termux; db=hkg_termux.FlightDB('.'); hkg_termux.run_refresh(db,'.'); print('refresh ok')"

  Fetching HKIA data for 2026-08-18 (today) ...
  Fetching .../rest/flights?date=2026-08-18&span=1 ... OK - 10 entries, 1179 flights
  ✓  2026-08-18: 457 arrivals / 446 departures

  Fetching HKIA data for 2026-08-19 (future) ...
  Fetching .../rest/flights?date=2026-08-19&span=1 ... OK - 8 entries, 1158 flights
  ✓  2026-08-19: 437 arrivals / 441 departures
  ✓ Refreshed 2 date(s): 2026-08-18, 2026-08-19
    2026-08-18: 457 arrivals / 446 departures
    2026-08-19: 437 arrivals / 441 departures
  ✓ Total fresh: 894 arrivals / 887 departures
refresh ok
```

**新鲜状态抽查（12h 前窗口内的今日早班）：**

刷新后 enriched JSON 中，`2026-08-18` 凌晨到达航班已带最新状态：

```
HB 711  04:00  →  At gate 03:42
CX 875  04:05  →  At gate 04:12
UO 517  04:05  →  At gate 04:00
```

这些航班仍处于 12h 前 ~ +2h 后的搜索窗口内，刷新后状态不再是过期快照。

---

## 三层刷新逻辑

**改动内容（hkg_termux.py，仅 `run_refresh` + 模块级常量 `FINAL_STATUSES`）：**

1. **36h 滚动窗口（已有，保留并去重）**：
   - 抓取日期范围 `(now - 12h).date()` 到 `(now + 24h).date()`，含首尾。
2. **Straggler catch-up（新增，每次刷新都执行）**：
   - 扫描现有 arrivals + departures，凡是 `date + time` 早于 `now - 12h`、且状态不属于
     `FINAL_STATUSES = {'at gate', 'departed', 'cancelled'}`（含 `Dep ...` 等缩写）的航班，
     其日期会被加入抓取集合。
3. **每日 0400 first-refresh（新增）**：
   - HKT ≥ 04:00 且 `~/.hkg_cache/.0400_refresh_<YYYY-MM-DD>` 不存在时，追加
     `today - 2` 与 `today - 1` 两个过去日期；两个日期都成功抓取后写入 flag 文件。
   - 同日后续刷新看到 flag 存在即跳过本层。

所有日期先去重、排序，再逐日抓取（过去 `flights/past`，今天/未来普通 `flights`），
单日失败不影响其它日期；结束后原地合并 JSON 并重载内存 FlightDB。

**验证（2026-08-18 15:3x HKT）：**

```
python -m py_compile hkg_termux.py   →  PY_COMPILE_OK
```

真实刷新（当日 0400 flag 已存在，straggler 为 0）：

```
Refresh date set (2 date(s)): 2026-08-18, 2026-08-19
  ✓ 2026-08-18: 457 arrivals / 446 departures
  ✓ 2026-08-19: 437 arrivals / 441 departures
  ✓ Straggler catch-up: 0 stale date(s): -
  ✓ 0400 first-refresh: skipped (before 04:00 HKT or flag already exists)
RESULT: (894, 887)
```

首次无 flag 时（temp HOME 隔离 + mock 抓取，成功路径）：

```
Refresh date set (4 date(s)): 2026-08-16, 2026-08-17, 2026-08-18, 2026-08-19
  ✓ 0400 first-refresh: done (2026-08-16, 2026-08-17); flag written: .../.0400_refresh_2026-08-18
```

Straggler 注入测试（temp 数据含 2026-08-01 旧航班 + `Est` 状态，mock 抓取为空）：

```
Refresh date set (3 date(s)): 2026-08-01, 2026-08-18, 2026-08-19
  ✓ Straggler catch-up: 1 stale date(s) found
```

结论：三层刷新可用；`Dep ...` 按 departed 视为最终状态，避免把已起飞航班反复当 straggler 抓取。
