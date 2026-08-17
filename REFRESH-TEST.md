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
