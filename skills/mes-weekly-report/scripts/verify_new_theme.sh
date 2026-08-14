#!/usr/bin/env bash
# mes-weekly-report 周报 HTML 看板 + 邮件自检脚本（§0 独有：160ms 下限 + send_report_email）
# 用法 1：  cd skills/mes/mes-weekly-report
#           bash scripts/verify_new_theme.sh templates/weekly-report.html
# 用法 2：  bash scripts/verify_new_theme.sh --email <body-template>.html
# 退出码：0=全部通过 非0=有FAIL

set -u
MODE="html"
if [ "$#" -ge 1 ] && [ "$1" = "--email" ]; then MODE="email"; shift; fi
if [ $# -ne 1 ]; then
  echo "用法：$0 [--email] <path/to/template_or_email>" >&2
  exit 2
fi
SRC="$1"
if [ ! -f "$SRC" ]; then
  echo "[FAIL] 文件不存在: $SRC" >&2
  exit 2
fi

check() {
  local name="$1" expect="$2" actual="$3" cmp="$4"
  local ok=0
  case "$cmp" in
    ge) [ "$actual" -ge "$expect" ] && ok=1 ;;
    eq) [ "$actual" -eq "$expect" ] && ok=1 ;;
  esac
  if [ "$ok" -eq 1 ]; then
    printf "  %-44s %3d PASS\n" "[$name]" "$actual"
  else
    printf "  %-44s %3d FAIL (期望 %s %d)\n" "[$name]" "$actual" "$cmp" "$expect"
    FAIL=$((FAIL+1))
  fi
}

FAIL=0
echo "=== $MODE :: $SRC ==="

if [ "$MODE" = "email" ]; then
  N=$(grep -cE '<!--\[if mso\]>' "$SRC" 2>/dev/null || echo 0)
  N=$(printf '%d' "$N" 2>/dev/null || echo 0)
  check "§0 Outlook mso fallback (>=4)" 4 "$N" ge

  N=$(grep -cE 'style="[^"]*border-left[^"]*[0-9]+px' "$SRC" 2>/dev/null || echo 0)
  N=$(printf '%d' "$N" 2>/dev/null || echo 0)
  check "§G 禁止 border-left 进度条 (=0)" 0 "$N" eq

  N=$(awk '
    BEGIN { c=0 }
    /style="[^"]*border-radius[^"]*[0-9]+[^0-9"]*px/ {
      line=$0
      while (match(line, /border-radius\s*:\s*[^;"]+[;"]/)) {
        tok = substr(line, RSTART, RLENGTH)
        gsub(/.*border-radius\s*:\s*/, "", tok)
        n = tok
        gsub(/[^0-9 .]/, " ", n)
        split(n, arr, " ")
        max = 0
        for (i in arr) { v = arr[i] + 0; if (v > max) max = v }
        if (max > 4) c++
        line = substr(line, RSTART + RLENGTH)
      }
    }
    END { printf "%d", c+0 }
  ' "$SRC")
  N=$(printf '%d' "$N" 2>/dev/null || echo 0)
  check "§G border-radius <=4px (=0)" 0 "$N" eq
else
  # §0 周报独有：transition 下限 160ms（:active 允许 120ms）——只要求文件里至少 1 条显式 160ms
  N=$(grep -cE '160ms' "$SRC" 2>/dev/null || echo 0)
  N=$(printf '%d' "$N" 2>/dev/null || echo 0)
  check "§0-1 周报 transition 下限 160ms(>=1)" 1 "$N" ge

  N=$(grep -cE -- '-[0-9]+px' "$SRC" 2>/dev/null || echo 0)
  N=$(printf '%d' "$N" 2>/dev/null || echo 0)
  check "§12 Negative Spread(>=4)" 4 "$N" ge

  N=$(grep -cE 'fb-(status|warn|error|success)-bg' "$SRC" 2>/dev/null || echo 0)
  N=$(printf '%d' "$N" 2>/dev/null || echo 0)
  check "§8 fb-4color-bg(>=4)" 4 "$N" ge

  N=$(grep -cE 'prefers-(reduced-motion|reduced-transparency|contrast)' "$SRC" 2>/dev/null || echo 0)
  N=$(printf '%d' "$N" 2>/dev/null || echo 0)
  check "§14 三门控(>=3)" 3 "$N" ge

  N=$(awk '
    /:active[^{]*\{/,/^[[:space:]]*\}/ {
      if (match($0, /scale\(0?\.9/)) { hit++ }
    }
    END { printf "%d", hit+0 }
  ' "$SRC")
  N=$(printf '%d' "$N" 2>/dev/null || echo 0)
  if [ "$N" -lt 1 ]; then
    N=$(grep -cE 'scale\(0?\.9' "$SRC" 2>/dev/null || echo 0)
    N=$(printf '%d' "$N" 2>/dev/null || echo 0)
    if grep -qE ':active[^{]*\{' "$SRC" 2>/dev/null && [ "$N" -ge 1 ]; then N=1; fi
  fi
  check "§7 :active scale(0.9x)(>=1)" 1 "$N" ge

  N=$(grep -c 'inset 0 1px 0' "$SRC" 2>/dev/null || echo 0)
  N=$(printf '%d' "$N" 2>/dev/null || echo 0)
  check "§12 inset-top-highlight(>=4)" 4 "$N" ge
fi

echo
if [ "$FAIL" -eq 0 ]; then
  echo "✅ $SRC 全部通过"
  exit 0
else
  echo "❌ $SRC 共 $FAIL 项未通过"
  exit "$FAIL"
fi
