#!/bin/sh
# 只给这次 codex 进程设置 $VISUAL，不改全局编辑器。
set -eu

self=$(readlink -f -- "$0")
dir=$(CDPATH= cd -- "$(dirname -- "$self")" && pwd)
VISUAL="$dir/psup-editor.sh" exec codex "$@"
