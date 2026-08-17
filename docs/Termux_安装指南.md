# Termux 航班数据查询系统 — 安装指南

## 1. Termux 安装 Python

```bash
pkg update && pkg upgrade
pkg install python git
```

## 2. 传输数据文件到手机

### 方法 A: 电脑 → Termux (SSH)

```bash
# 在电脑上执行 (先安装 openssh)
# Termux 端:
sshd          # 启动 SSH 服务 (端口 8022)

# 电脑端:
scp -P 8022 hkg_*_enriched.json hkg_airlines_info.json hkg_termux.py \
  user@手机IP:/data/data/com.termux/files/home/hkg/
```

### 方法 B: Termux 直接下载

```bash
mkdir ~/hkg && cd ~/hkg

# 用 curl 下载 (需要临时 HTTP 服务器或网盘链接)
# 或者用 termux-setup-storage 共享存储
termux-setup-storage
cp /storage/emulated/0/Download/hkg_*.json ~/hkg/
```

### 方法 C: Web 下载

```bash
mkdir ~/hkg && cd ~/hkg
# 从 Google Drive / Dropbox 等下载
```

## 3. 启动系统

```bash
cd ~/hkg

# TUI 终端模式 (默认)
python hkg_termux.py .

# Web 浏览器模式 (推荐)
python hkg_termux.py . --web --port 8080

# 然后手机浏览器打开:
# http://localhost:8080
```

## 4. 一键安装脚本

把以下内容保存为 `install.sh`:

```bash
#!/bin/bash
pkg update -y && pkg install python -y
mkdir -p ~/hkg && cd ~/hkg
echo "✅ Python installed"
echo "   Place your hkg_*.json files in ~/hkg/"
echo "   Then run: python hkg_termux.py . --web"
```

## 5. 使用方式

### TUI 模式 (终端界面)

```
==================================================
  ✈  HKG Flight Data System
==================================================
  Arrivals: 7171
  Departures: 7171
  Airlines: 95
  Date Range: 2026-08-16 ~ 2026-08-31
--------------------------------------------------
  1. Search by flight number
  2. Search by date
  3. Show airline info
  4. Start web server (browser)
  0. Exit
--------------------------------------------------
  Choose: 1
  Flight number: CX759

  CX 759 | 2026-08-16 08:40
  Route: HKG → SIN
  Status: Dep 08:54
  Terminal: T1
  Gate: 63
  Check-in: B
  Transfer Desk: W1
```

### Web 模式 (浏览器界面)

```bash
python hkg_termux.py . --web --port 8080
# 手机浏览器打开 http://localhost:8080
```

## API 接口

| 路径 | 说明 |
|:---|:---|
| `GET /api/search?flight=CX759` | 按航班号搜索 |
| `GET /api/search?flight=CX759&date=2026-08-16` | 按航班号+日期搜索 |
| `GET /api/date?date=2026-08-16` | 按日期查询所有航班 |
| `GET /api/stats` | 统计信息 |

## 需要的文件

```
~/hkg/
├── hkg_termux.py            ← 查询系统
├── hkg_arrivals_enriched.json   ← 到达航班数据
├── hkg_departures_enriched.json ← 出发航班数据
└── hkg_airlines_info.json       ← 航空公司信息
```
