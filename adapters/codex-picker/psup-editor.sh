#!/bin/sh
# Codex 的 $VISUAL 入口：草稿里有 ;; 就开抽屉，否则回退到普通编辑器。
set -eu

file=${1:?missing draft file}
dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

if python3 "$dir/picker.py" --has-trigger "$file"; then
	exec python3 "$dir/picker.py" "$file"
fi

# 没有 ;; 时保持原来的编辑器行为；原值由 codex shim 存在 PSUP_ORIGINAL_VISUAL。
fallback=${PSUP_FALLBACK_EDITOR:-${PSUP_ORIGINAL_VISUAL:-vi}}
case "$fallback" in
	*psup-editor.sh*) fallback=vi ;;
esac
if [ -n "$fallback" ] && [ "$fallback" != "vi" ]; then
	exec sh -c "$fallback \"\$1\"" sh "$file"
fi
exec vi "$file"
