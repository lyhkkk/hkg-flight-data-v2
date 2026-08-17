#!/bin/bash
# HKG Flight Data — Termux 诊断脚本
# 在 Termux 中运行: bash diagnose.sh

echo "=========================================="
echo "  HKG Flight Data — 环境诊断"
echo "=========================================="
echo ""

# 1. 检查 Python
echo "[1/6] 检查 Python..."
if command -v python3 &>/dev/null; then
    echo "  ✅ python3: $(python3 --version 2>&1)"
elif command -v python &>/dev/null; then
    echo "  ✅ python: $(python --version 2>&1)"
else
    echo "  ❌ Python 未安装"
    echo "  → 安装: pkg update && pkg install python"
fi
echo ""

# 2. 检查当前目录
echo "[2/6] 当前目录: $(pwd)"
echo ""

# 3. 检查文件是否存在
echo "[3/6] 检查文件..."
FILES=(
    "hkg_remote.py"
    "hkg_termux.py"
    "README.md"
    "scripts/fetch_flights.py"
    "scripts/fetch_airlines.py"
    "scripts/merge_airline_data.py"
    "docs/Termux_安装指南.md"
    "examples/flight_cx759.html"
)

ALL_OK=true
for f in "${FILES[@]}"; do
    if [ -f "$f" ]; then
        size=$(wc -c < "$f" 2>/dev/null || echo "?")
        echo "  ✅ $f ($size bytes)"
    else
        echo "  ❌ $f — 缺失！"
        ALL_OK=false
    fi
done
echo ""

# 4. 检查文件权限
echo "[4/6] 检查执行权限..."
if [ -x "hkg_remote.py" ]; then
    echo "  ✅ hkg_remote.py 可执行"
else
    echo "  ⚠️  hkg_remote.py 无执行权限"
    echo "  → 修复: chmod +x hkg_remote.py"
fi
if [ -x "hkg_termux.py" ]; then
    echo "  ✅ hkg_termux.py 可执行"
else
    echo "  ⚠️  hkg_termux.py 无执行权限"
fi
echo ""

# 5. 检查网络连接
echo "[5/6] 检查网络..."
if ping -c 1 -W 2 www.hongkongairport.com &>/dev/null; then
    echo "  ✅ 可以连接 HKIA API"
else
    echo "  ❌ 无法连接 HKIA API"
    echo "  → 检查网络: ping www.hongkongairport.com"
fi
echo ""

# 6. 尝试运行
echo "[6/6] 尝试运行..."
if command -v python3 &>/dev/null; then
    python3 -c "
import sys, json, urllib.request
print('  ✅ Python 模块加载正常')
try:
    req = urllib.request.Request('https://www.hongkongairport.com/flightinfo-rest/rest/airlines', headers={'User-Agent': 'Termux'})
    resp = urllib.request.urlopen(req, timeout=10)
    data = json.loads(resp.read())
    print(f'  ✅ API 连接正常 (airlines: {len(data)} records)')
except Exception as e:
    print(f'  ❌ API 连接失败: {e}')
"
elif command -v python &>/dev/null; then
    python -c "
import sys, json, urllib.request
print('  ✅ Python 模块加载正常')
try:
    req = urllib.request.Request('https://www.hongkongairport.com/flightinfo-rest/rest/airlines', headers={'User-Agent': 'Termux'})
    resp = urllib.request.urlopen(req, timeout=10)
    data = json.loads(resp.read())
    print(f'  ✅ API 连接正常 (airlines: {len(data)} records)')
except Exception as e:
    print(f'  ❌ API 连接失败: {e}')
"
fi
echo ""

echo "=========================================="
echo "  诊断完成"
echo "=========================================="
echo ""
echo "如果全部通过，运行:"
echo "  python hkg_remote.py search CX759"
echo ""
echo "如果报错，请截图发给我"
