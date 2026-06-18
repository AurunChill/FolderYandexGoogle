#!/usr/bin/env bash
#
# backup.sh — интерактивный запуск бэкапа Obsidian-vault на облака.
# При первом запуске сам создаёт venv и ставит зависимости.
#
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
VENV="$HERE/venv"
PY="$VENV/bin/python"

# ---- 1. venv + зависимости (один раз) -----------------------------
if [ ! -x "$PY" ]; then
  echo "==> Первый запуск: создаю venv и ставлю зависимости..."
  python3 -m venv "$VENV"
  "$PY" -m pip install --upgrade pip >/dev/null
  "$PY" -m pip install -r "$HERE/requirements.txt"
  echo ""
fi

# ---- 2. меню выбора --------------------------------------------------
echo "Куда сохранить бэкап Obsidian?"
echo "  1) Яндекс Диск"
echo "  2) Google Drive"
echo "  3) Оба"
read -r -p "Выбор [1-3]: " ans
case "${ans:-}" in
  1) TARGET=yandex ;;
  2) TARGET=google ;;
  3) TARGET=both ;;
  *) echo "Не понял выбор — выхожу." >&2; exit 1 ;;
esac

# ---- 3. запуск -------------------------------------------------------
exec "$PY" "$HERE/backup.py" --target "$TARGET"
