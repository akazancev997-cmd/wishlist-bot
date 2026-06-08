#!/bin/bash
set -e

echo "=== Установка зависимостей ==="
pip3 install -r requirements.txt

echo ""
echo "=== Создание базы данных ==="
mkdir -p data

echo ""
echo "=== Запуск ==="
echo "Убедись, что файл .env заполнен!"
echo "Затем выполни: python3 main.py"
echo ""
echo "Или для продакшена: uvicorn web:app --host=0.0.0.0 --port=8080"
