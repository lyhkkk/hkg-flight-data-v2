# HKG Flight Data 🛫

香港国际机场（HKG）航班数据查询系统

实时调用 HKIA 官方 API，支持 CLI / TUI / Web 三种模式，可直接在 Termux 上运行。

## 功能

- 🔍 按航班号搜索（如 CX759）
- 📅 按日期查询所有航班
- ✈️ 到达 + 出发航班数据
- 🏢 航空公司信息（Logo、值机柜台、中转柜台）
- 📱 Termux 友好，支持手机使用
- 🌐 Web 界面，浏览器直接访问
- 💾 本地缓存，减少 API 请求

## 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/lyhkkk/hkg-flight-data.git
cd hkg-flight-data
```

### 2. 安装依赖（无需额外依赖）

```bash
# Python 3.6+ 即可，无需 pip install
```

### 3. 使用

#### 远程模式（推荐，无需传数据文件）

```bash
# 搜索航班
python hkg_remote.py search CX759

# 搜索指定日期
python hkg_remote.py search CX759 2026-08-16

# 启动 Web 界面
python hkg_remote.py web
# 浏览器打开 http://localhost:8080
```

#### 本地模式（使用已下载的数据）

```bash
# 先运行数据采集脚本
python fetch_flights.py
python fetch_airlines.py
python merge_airline_data.py

# 启动 TUI 模式
python hkg_termux.py .

# 启动 Web 模式
python hkg_termux.py . --web
```

## Termux 安装

```bash
# 安装 Python
pkg update && pkg install python

# 下载脚本（只需这一个文件）
curl -O https://raw.githubusercontent.com/lyhkkk/hkg-flight-data/main/hkg_remote.py

# 使用
python hkg_remote.py search CX759
python hkg_remote.py web
```

详见 [Termux 安装指南](docs/Termux_安装指南.md)

## API 接口

| 路径 | 说明 |
|:---|:---|
| `GET /api/search?flight=CX759` | 按航班号搜索 |
| `GET /api/search?flight=CX759&date=2026-08-16` | 按航班号+日期搜索 |
| `GET /api/airlines` | 获取航空公司列表 |

## 数据字段

### 航班数据

| 字段 | 说明 |
|:---|:---|
| `date` | 日期 (YYYY-MM-DD) |
| `time` | 计划时间 (HH:MM) |
| `flight_number` | 航班号 |
| `airline_code` | 航空公司代码 |
| `origin` / `destination` | 出发地/目的地 |
| `status` | 航班状态 |
| `terminal` | 航站楼 |
| `gate` | 登机口 |
| `aisle` | 走廊 |
| `check_in_aisle` | 值机柜台 |
| `transfer_desk` | 中转柜台 |
| `airline_logo_url` | 航空公司 Logo |

### 航空公司数据

| 字段 | 说明 |
|:---|:---|
| `name_en` | 英文名称 |
| `airline_code` | IATA 代码 |
| `iata_code` | IATA 2位代码 |
| `logo_url` | Logo URL |
| `check_in_aisle` | 值机柜台 |
| `transfer_desk` | 中转柜台 (E1/W1/N/A) |
| `website` | 官网 |

## 数据来源

- [香港国际机场官网](https://www.hongkongairport.com/en/flights/)
- HKIA Flight Info REST API

## 示例

```
$ python hkg_remote.py search CX759

========================================
  CX 759  |  DEPARTURE
  Route:  HKG → SIN
  Date:   2026-08-16  08:40
  Status: Dep 08:54
  Terminal: T1
  Gate:     63
  Aisle:    E
========================================
```

## 文件结构

```
hkg-flight-data/
├── README.md                 # 项目说明
├── hkg_remote.py             # 远程查询系统（推荐）
├── hkg_termux.py             # Termux TUI + Web 模式
├── fetch_flights.py          # 航班数据采集脚本
├── fetch_airlines.py         # 航空公司数据采集脚本
├── merge_airline_data.py     # 数据合并脚本
├── docs/
│   ├── Termux_安装指南.md
│   └── HKIA航班数据摘要.md
└── examples/
    └── flight_cx759.html     # 航班展示页面示例
```

## License

MIT
