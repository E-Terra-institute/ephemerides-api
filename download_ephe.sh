DEST_DIR="ephe"
mkdir -p "$DEST_DIR"

for YEAR in $(seq -1000 10 2100); do
  FILE="seas_${YEAR}.se1"
  URL="https://www.astro.com/ftp/swisseph/ephe/${FILE}"
  echo "Скачиваю $FILE..."
  curl -fSL "$URL" -o "${DEST_DIR}/${FILE}"
  if [ $? -ne 0 ]; then
    echo "  ⚠️ Не удалось скачать $FILE (файл может отсутствовать на сервере)"
    rm -f "${DEST_DIR}/${FILE}"
  fi
done

echo "Готово! Проверь папку $DEST_DIR"
