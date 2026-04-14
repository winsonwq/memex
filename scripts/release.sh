#!/bin/bash
# 发布 memex 到 PyPI
# 用法: ./scripts/release.sh

set -e

echo "=== 1. 构建 wheel ==="
python3 -m build

echo ""
echo "=== 2. 上传到 PyPI ==="
echo "请输入 PyPI token: "
read -s TOKEN

TWINE_PASSWORD="$TOKEN" python3 -m twine upload dist/* -u wangqiu777 -p "$TOKEN"

echo ""
echo "=== 发布完成 ==="
echo "验证: pip install memex"
