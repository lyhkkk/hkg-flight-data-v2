# HKG Flight Data v2 — 测试报告

**日期：** 2026-08-18
**范围：** 仅当前目录 O:\lyh\Projects\hkia\hkg-flight-data-v2
**目的：** 验证 pi 上一次修改是否完整应用并工作正常。

## 1. Git 状态

- `git status --short`：**干净**（无未提交/暂存改动，无半应用状态）。
- `git log --oneline -5`：
  - `7685e8d docs: fix README for v2`（最近一次提交，本次修改对象 = README）
  - `6946af9 refactor: simplified search flow with time window`
  - `c69bf24 feat: stand/gate search, codeshare filter, reg display`
  - `8746727 fix: remove hardcoded API URL, use env var instead`
  - `c85d6c3 feat: fetch aircraft reg from Menzies LSD API (free, no auth)`

**结论：** 所有修改均已提交（readme v2 修正），无残留在工作区。

## 2. 修改是否完整

- 全部 8 个 `.py` 文件存在，无缺失。
- 最近一次提交只改动 README.md（docs 修正），代码层面无半成品。
- `hkg_termux.py` / `hkg_remote.py` 均可正常导入，结构完整。

## 3. 语法检查

`python -m py_compile` 通过以下所有文件，**全部通过，无报错**：

```
fetch_airlines.py  fetch_menzies_reg.py  fetch_reg.py
hkg_remote.py      hkg_termux.py
scripts/fetch_airlines.py  scripts/fetch_flights.py  scripts/merge_airline_data.py
```

结果：`PY_COMPILE_OK`

## 4. 测试结果

### 导入测试 ✅
- `python -c "import hkg_remote; print('remote import ok')"` → `remote import ok`
- `python -c "import hkg_termux; print('termux import ok')"` → `termux import ok`（均可非交互导入）

### 真实查询测试 ✅（网络到 HKIA）
命令：`python hkg_remote.py search CX759` → 退出码 0，返回 3 条结果（8/17、8/18、8/19 的 HKG→SIN 出发）：

```
CX 759 (CPA/CX) | DEPARTURE
Route:  HKG -> SIN
Date:   2026-08-17  08:40
Status: Dep 08:47
Terminal: T1 | Gate: 40 | Aisle: E
Total: 3 results
```

网络查询功能正常。

## 5. baggage/belt 字段修复验证

`grep -n "belt\|baggage" hkg_remote.py`：

```python
hkg_remote.py:120: 'belt': flight.get('baggage', '') or flight.get('belt', ''),
hkg_remote.py:311: print(f"  Belt:     {f.get('belt', '-')}")
```

✅ **字段映射修复已存在**：`belt` 优先读取 `baggage` 字段，回退到 `belt`，兼容新旧 API 字段名。

`hkg_termux.py`：**无 belt/baggage 原始字段**（该文件通过预处理 DB/排序文件按停机位/登机口组织，不直接消费原始 belt 字段），故无需该修复，符合预期。

## 6. 结论

| 项目 | 结果 |
|:---|:---|
| Git 状态 | ✅ 干净，修改已全部提交 |
| 修改完整性 | ✅ 完整，无半应用状态 |
| 语法检查 | ✅ 8 个 .py 全部通过 |
| 导入测试 | ✅ 两个模块均可导入 |
| 真实查询 | ✅ CX759 返回 3 条，退出码 0 |
| baggage/belt 修复 | ✅ 已存在且正确 |

**能否使用：可以用。**
pi 上一次修改（README v2 修正）已干净应用，当前仓库处于可工作状态，CLI 远程查询功能验证通过。

**缺什么 / 注意事项：**
- 最近一次提交仅涉及文档（README），如需验证完整交互流程（TUI 菜单、Web 界面），需联网手动运行 `python hkg_termux.py .` 与 `python hkg_remote.py web`（本次仅以非交互命令验证了核心查询链路）。
- 未配置 `.env`（`API_BASE_URL`）时依赖默认值；生产使用前建议确认环境变量。
