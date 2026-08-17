# Quick Search 功能验证报告 (hkg_termux.py)

验证范围：仅在当前目录 `O:\lyh\Projects\hkia\hkg-flight-data-v2` 内进行。

## 一、现状：实现 vs 描述

| 描述中的 UX | 修复前现状 | 结论 |
|---|---|---|
| 输入 `N32`（字母+数字）→ 直接 Stand/Gate 搜索 | 任何以字母开头的输入都判为「航班号」，`N32` 被当成航班号搜索（问 codeshare），结果为空 | **未实现（bug）** |
| 输入 `32`（纯数字）→ 询问 Stand/Gate or Flight（1/2） | 纯数字走 else 分支，询问 1/2 | ✅ 已实现 |
| 输入 `CX759`（字母）→ 航班号搜索，再问 codeshare y/n | 字母开头判为航班号，问 codeshare | ✅ 已实现 |
| 所有搜索用时间窗 12h 前 ~ 2h 后 NOW | `search_by_stand_or_gate` 与 `search_flight_number_contains` 均调用 `_in_window()` | ✅ 已实现且正确 |
| 所有结果显示 Reg 列 | `_print_results` 含 Reg 列，调用 `get_reg()` | ✅ 列存在；但 Reg 常显示 `-`（本地无 FlightStats 缓存文件，属数据缺失，非代码 bug） |

### 为什么「应用不了」
根因是**输入分类器错误**：原先 `is_flight = bool(re.match(r'^[A-Za-z]', …))`，只要输入以字母开头（无论 `N32` 还是 `CX759`）都被判为航班号。于是 `N32` 永远进不了 Stand/Gate 搜索，永远「No results」。

`N32` 与 `CX759` 都是「字母+数字」，无法靠纯字母开头区分。但实际数据中：
- 停机位/登机口前缀都是**单个字母**：D / N / R / S / W（如 N32、D201）
- 航班号航空公司代码都是**多字母**（CX、SQ、KA…），库里不存在单字母航班前缀

因此可按「前缀字母数」分类：1 个字母 → Stand/Gate；2 个及以上字母 → 航班号；无字母 → 询问。

## 二、测试步骤与输出

### 0. 语法检查
```
python -m py_compile hkg_termux.py   →  COMPILE OK
```

### 1. `N32`（单字母 → Stand/Gate）
```
1
N32
0
```
输出：
```
Stand/Gate 'N32' flights (12h~+2h):
  Type  Flight     Reg      Date         Time   Route                Status
  ARR   SQ 894     -        2026-08-17   17:05  SIN→HKG              At gate 17:15
  ARR   CX 549     -        2026-08-17   20:00  HND→HKG              At gate 19:31
```
✅ 现在进入 Stand/Gate 搜索（修复前此处会进入 codeshare 航班号搜索并报 No results）。

### 2. `32`（纯数字 → 询问）
```
1
32
1
```
输出：
```
'32' - Search as:
1. Stand / Gate
2. Flight number
Choose (1/2):
```
选 1 后列出 Stand/Gate 结果 5 条。✅

### 3. `CX759`（多字母 → 航班号 + codeshare）
```
1
CX759
y
```
输出：进入「Include codeshare? (y/n) [n]:」→「Flights containing 'CX759' (codeshare, 12h~+2h):」→ No results found。
这是**正确**行为：`CX759` 每日 08:40，测试时 NOW≈03:24，当日航班在 +5h（超出 +2h 窗）、前一日在 -19h（超出 12h 窗），均不在窗内。直接函数调用确认全量 16 条 (CX759) 存在，但窗口内 0 条。

### 4. 直接函数验证（绕过 UI 循环）
```
FlightDB('.').search_by_stand_or_gate('32')  → 5 条（均 _in_window）
FlightDB('.').search_flight_number_contains('CX759', codeshare=True) → 0 条（窗口内）
db.get_reg(...) → None（无 ~/.hkg_cache/flightstats 缓存文件）
```
✅ 逻辑独立验证通过。

## 三、是否可用
- 修复后：`N32` / `32` / `CX759` 三种输入分类均符合描述，时间窗与 Reg 列均正常。
- **可用**（需按上面交互逐项操作）。
- 注意：Reg 列在缺少 FlightStats 缓存时显示 `-`，这是数据缺失，不是功能损坏；若已有 `~/.hkg_cache/flightstats/<CARRIER>_<num>_<date>.json` 则会显示真实机尾号。

## 四、修复了什么
在 `hkg_termux.py` 的 `run_tui()` 快速搜索分支，把原来「以任意字母开头即判为航班号」的分类器改成三分类：
- 前缀 ≥2 个字母（如 `CX759`）→ 航班号搜索 + codeshare 询问
- 前缀 1 个字母（如 `N32`、`D201`）→ 直接 Stand/Gate 搜索
- 无字母（纯数字，如 `32`）→ 询问 Stand/Gate or Flight (1/2)

只改了这一处判断逻辑，未触碰搜索、时间窗、Reg 渲染等其余部分。

## 五、使用说明
启动：
```
python hkg_termux.py .
```
主菜单选 `1`（Quick search）后输入：
- `N32` → 直接查 N32 停机位/登机口
- `32` → 提示选择：`1`=Stand/Gate，`2`=航班号
- `CX759` → 航班号搜索，随后按提示输入 `y`（含 codeshare）/ `n`（仅承运航司）
