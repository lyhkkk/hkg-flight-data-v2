# HKG Flight Data v2 🛫

香港国际机场（HKG）航班数据查询系统

支持 CLI / TUI / Web 三种模式，可直接在 Termux 上运行。

## 功能

- 🔍 按航班号搜索（如 CX759）
- 📅 按日期查询所有航班
- ✈️ 到达 + 出发航班数据
- 🏢 航空公司信息（Logo、值机柜台、中转柜台）
- 🅿️ 按停机位/登机口搜索（如 N32、32）
- 🔗 航班号模糊搜索 + 代码共享过滤
- 🛩️ 飞机注册号查询（FlightStats 缓存）
- 📱 Termux 友好，支持手机使用
- 🌐 Web 界面，浏览器直接访问

## 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/lyhkkk/hkg-flight-data-v2.git
cd hkg-flight-data-v2
```

### 2. 使用

#### TUI 模式（推荐）

```bash
python hkg_termux.py .
```

菜单说明：
- **Quick search** - 输入停机位(N32)、登机口(32)或航班号(CX759)
  - 输入字母开头 → 作为航班号搜索，询问代码共享
  - 输入数字 → 询问按停机位/登机口 或 航班号搜索
- 所有搜索结果包含**飞机注册号**（Reg）列

#### Web 模式

```bash
python hkg_termux.py . --web
# 浏览器打开 http://localhost:8080
```

#### 远程模式（需网络）

```bash
python hkg_remote.py search CX759
python hkg_remote.py web
```

## API 接口

| 路径 | 说明 |
|:---|:---|
| `GET /api/search?flight=CX759` | 按航班号搜索 |
| `GET /api/search?flight=CX759&date=2026-08-16` | 按航班号+日期搜索 |
| `GET /api/date?date=2026-08-16` | 按日期搜索所有航班 |
| `GET /api/reg?flight=CX759&date=2026-08-16` | 查询飞机注册号 |
| `GET /api/stats` | 获取统计信息 |

## 数据字段

### 航班数据

| 字段 | 说明 |
|:---|:---|
| `date` | 日期 (YYYY-MM-DD) |
| `time` | 计划时间 (HH:MM) |
| `flight_number` | 航班号 |
| `all_flight_numbers` | 所有航班号（含代码共享） |
| `airline_code` | 航空公司代码 |
| `origin` / `destination` | 出发地/目的地 |
| `status` | 航班状态 |
| `terminal` | 航站楼 |
| `gate` | 登机口（出发） |
| `parking_stand` | 停机位（到达） |
| `check_in_aisle` | 值机柜台 |
| `transfer_desk` | 中转柜台 |
| `airline_terminal` | 航空公司航站楼 |

### 航空公司数据

| 字段 | 说明 |
|:---|:---|
| `name_en` | 英文名称 |
| `airline_code` | ICAO 代码 |
| `iata_code` | IATA 2位代码 |
| `logo_url` | Logo URL |
| `check_in_aisle` | 值机柜台 |
| `transfer_desk` | 中转柜台 (E1/W1/N/A) |
| `website` | 官网 |

## 数据来源

- [香港国际机场官网](https://www.hongkongairport.com/en/flights/)
- HKIA Flight Info REST API
- FlightStats（飞机注册号缓存）

## 文件结构

```
hkg-flight-data-v2/
├── README.md
├── hkg_termux.py              # TUI + Web 模式
├── hkg_remote.py              # 远程查询系统
├── fetch_reg.py               # 飞机注册号采集（FlightStats）
├── fetch_airlines.py          # 航空公司数据采集
├── hkg_arrivals_enriched.json # 到达航班数据
├── hkg_departures_enriched.json # 出发航班数据
├── hkg_airlines_info.json     # 航空公司数据
└── docs/
```

## License

MIT
