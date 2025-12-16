#!/bin/bash

DB_HOST="localhost"
DB_PORT="5432"
DB_NAME="subscriptions_db"
DB_USER="postgres"
DB_PASS="postgres"

VENV_DIR="venv"
PID_FILE="app.pid"

setup_database() {
  echo "setup_database: проверка базы данных" # функция для проверки и создания базы данных

  export PGPASSWORD="$DB_PASS" # передаем пароль PostgreSQL через переменную окружения

  createdb -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" "$DB_NAME" 2>/dev/null
  # проверяем, можем ли подключиться к базе
  psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1;" >/dev/null 2>&1

  # проверяем код завершения команды
  if [ $? -eq 0 ]; then
    echo "OK: подключение к БД есть"
  else
    echo "ОШИБКА: нет подключения к БД"
  fi
}

install_dependencies() {
  echo "install_dependencies: установка зависимостей" # функция для установки зависимостей проекта

  python -m venv "$VENV_DIR" # создаем виртуальное окружение Python
  source "$VENV_DIR/Scripts/activate"

  pip install -r requirements.txt

  echo "OK: зависимости установлены"
}

start_app() {
  echo "start_app: запуск приложения" # функция запуска Flask-приложения

  source "$VENV_DIR/Scripts/activate"
  # передаем параметры БД в приложение через переменные окружения
  export DB_HOST DB_PORT DB_NAME DB_USER DB_PASS

  python app.py &
  echo $! > "$PID_FILE"

  echo "OK: приложение запущено"
}

stop_app() {
  echo "stop_app: остановка приложения"

  # проверяем, существует ли PID-файл
  if [ ! -f "$PID_FILE" ]; then
    echo "PID файл не найден"
    return
  fi

  # останавливаем процесс по PID
  kill "$(cat $PID_FILE)" 2>/dev/null
  # удаляем PID-файл
  rm -f "$PID_FILE"

  echo "OK: приложение остановлено"
}

run_tests() {
  echo "run_tests: запуск тестов"

  source "$VENV_DIR/Scripts/activate"
  # запускаем pytest
  pytest

  echo "OK: тесты выполнены"
}

# получаем команду из аргумента скрипта
CMD="$1"

if [ "$CMD" = "setup_database" ]; then
  setup_database
elif [ "$CMD" = "install_dependencies" ]; then
  install_dependencies
elif [ "$CMD" = "start_app" ]; then
  start_app
elif [ "$CMD" = "stop_app" ]; then
  stop_app
elif [ "$CMD" = "run_tests" ]; then
  run_tests
else
  echo "Доступные команды:"
  echo "  ./helper.sh setup_database"
  echo "  ./helper.sh install_dependencies"
  echo "  ./helper.sh start_app"
  echo "  ./helper.sh stop_app"
  echo "  ./helper.sh run_tests"
fi
