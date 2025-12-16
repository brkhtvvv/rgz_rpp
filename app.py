import os
from flask import Flask, request, jsonify
import psycopg2

app = Flask(__name__)

# параметры подключения к БД берем из переменных окружения
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")

def get_conn():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )

# запись действий пользователя в таблицу audit
def log_action(user_id, action, details):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO audit (user_id, action, details) VALUES (%s, %s, %s)",
        (user_id, action, details)
    )
    conn.commit()
    cur.close()
    conn.close()
# эндпоинт для проверки, что API запущено
@app.route("/")
def index():
    return "Subscriptions API работает"

# создание подписки
@app.route("/subscriptions", methods=["POST"])
def create_subscription():
    data = request.get_json() # получаем JSON из запроса
    if not data:
        return jsonify({"error": "json required"}), 400
    
    # достаем данные из JSON
    user_id = data.get("user_id")
    name = data.get("name")
    amount = data.get("amount")
    period = data.get("period")
    start_date = data.get("start_date")

    # проверка обязательных полей
    if not user_id or not name or amount is None or not period or not start_date:
        return jsonify({"error": "user_id, name, amount, period, start_date required"}), 400

    conn = get_conn()
    cur = conn.cursor()

    # добавляем новую подписку
    cur.execute(
        "INSERT INTO subscriptions (user_id, name, amount, period, start_date) "
        "VALUES (%s, %s, %s, %s, %s) RETURNING id",
        (user_id, name, amount, period, start_date)
    )

    # получаем id созданной подписки
    sub_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()

    # записываем действие в аудит
    log_action(user_id, "CREATE", f"subscription {sub_id}")
    return jsonify({"id": sub_id}), 201

# просмотр подписок пользователя
@app.route("/subscriptions/<int:user_id>", methods=["GET"])
def get_subscriptions(user_id):
    # получаем все подписки конкретного пользователя
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, name, amount, period, start_date "
        "FROM subscriptions WHERE user_id = %s",
        (user_id,)
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()

    # формируем ответ в виде списка словарей
    result = []
    for r in rows:
        result.append({
            "id": r[0],
            "name": r[1],
            "amount": r[2],
            "period": r[3],
            "start_date": str(r[4])
        })
    return jsonify(result)

# редактирование подписки
@app.route("/subscriptions/<int:sub_id>", methods=["PUT"])
def update_subscription(sub_id):
    # обновление суммы или периода подписки
    data = request.get_json()
    if not data:
        return jsonify({"error": "json required"}), 400

    user_id = data.get("user_id")
    amount = data.get("amount")
    period = data.get("period")

    # проверяем, что передан пользователь
    if not user_id:
        return jsonify({"error": "user_id required"}), 400

    conn = get_conn()
    cur = conn.cursor()

    # обновляем только те поля, которые передали
    if amount is not None:
        cur.execute(
            "UPDATE subscriptions SET amount = %s WHERE id = %s AND user_id = %s",
            (amount, sub_id, user_id)
        )

    if period is not None:
        cur.execute(
            "UPDATE subscriptions SET period = %s WHERE id = %s AND user_id = %s",
            (period, sub_id, user_id)
        )
    conn.commit()
    cur.close()
    conn.close()

    log_action(user_id, "UPDATE", f"subscription {sub_id}") # пишем изменение в аудит
    return jsonify({"status": "updated"})

# удаление подписки
@app.route("/subscriptions/<int:sub_id>", methods=["DELETE"])
def delete_subscription(sub_id):
    # удаление подписки пользователя
    data = request.get_json()
    if not data:
        return jsonify({"error": "json required"}), 400

    user_id = data.get("user_id")
    if not user_id:
        return jsonify({"error": "user_id required"}), 400

    conn = get_conn()
    cur = conn.cursor()

    # удаляем подписку только если она принадлежит пользователю
    cur.execute(
        "DELETE FROM subscriptions WHERE id = %s AND user_id = %s",
        (sub_id, user_id)
    )

    conn.commit()
    cur.close()
    conn.close()

    log_action(user_id, "DELETE", f"subscription {sub_id}")

    return jsonify({"status": "deleted"})

if __name__ == "__main__":
    app.run()
