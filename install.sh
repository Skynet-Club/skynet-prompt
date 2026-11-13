#!/bin/sh
# 从源码目录安装；也可以被 curl 到本地后执行。
set -eu
DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
exec python3 "$DIR/scripts/install.py" "$@"
