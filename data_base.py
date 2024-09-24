import psycopg2
from psycopg2 import Error
from datetime import date
import pandas as pd
from sqlalchemy import create_engine

# Параметры подключения к базе данных
dbname = 'Finance_bot'
user = 'postgres'
password = 'vivt'
host = 'localhost'
port = '5432'


async def fetch_data(query, params):
    engine = create_engine(f'postgresql://{user}:{password}@{host}:{port}/{dbname}')
    conn = engine.connect()
    df = pd.read_sql(query, conn, params=params)
    conn.close()
    return df


async def get_category_expenses_for_month(user_id, month):
    # SQL-запрос для получения затрат по категориям за указанный месяц текущего года
    query = """
SELECT 
    Категории.Название_категории AS Название_категории, 
    DATE_TRUNC('day', Пользователь_Покупки.Дата_операции) AS Дата, 
    SUM(Пользователь_Покупки.Всего_затрат) AS Всего_затрат
FROM 
    Пользователь_Покупки
JOIN 
    Категории ON Пользователь_Покупки.id_категории = Категории.id
WHERE 
    Пользователь_Покупки.id_пользователя = %s
    AND EXTRACT(month FROM Пользователь_Покупки.Дата_операции) = %s
    AND EXTRACT(year FROM Пользователь_Покупки.Дата_операции) = EXTRACT(year FROM CURRENT_DATE)
GROUP BY 
    Категории.Название_категории, Дата
ORDER BY 
    Дата;
"""
    return await fetch_data(query, (user_id, month))


async def add_user_to_database(chat_id, nickname, first_name):

    # Подключение к базе данных
    try:
        connection = psycopg2.connect(dbname=dbname, user=user, password=password, host=host, port=port)
        cursor = connection.cursor()

        # Проверка, существует ли пользователь с таким chat_id
        sql_query = "SELECT COUNT(*) FROM \"Пользователь\" WHERE \"id_пользователя\" = %s"
        cursor.execute(sql_query, (chat_id,))
        count = cursor.fetchone()[0]

        if count == 0:  # Если пользователь с таким chat_id не существует
            # SQL-запрос для добавления пользователя в таблицу "Пользователь"
            sql_query = "INSERT INTO \"Пользователь\" (\"id_пользователя\", \"Ник\", \"имя\") VALUES (%s, %s, %s)"
            cursor.execute(sql_query, (chat_id, nickname, first_name))
            connection.commit()

    except psycopg2.Error as e:
        print("Ошибка при работе с базой данных:", e)

    finally:
        # Закрытие соединения с базой данных
        if connection:
            cursor.close()
            connection.close()


def check_existing_purchase(user_id, product_name):
    try:
        # Подключение к базе данных
        connection = psycopg2.connect(dbname=dbname, user=user, password=password, host=host, port=port)
        cursor = connection.cursor()

        # Проверка, существует ли уже запись о покупке для данного продукта, категории и пользователя
        for category_id in range(1, 8):
            sql_query = "SELECT COUNT(*) FROM \"Пользователь_Покупки\" WHERE \"id_пользователя\" = %s AND \"id_категории\" = %s AND \"Название_продукта\" = %s"
            cursor.execute(sql_query, (user_id, category_id, product_name[:45]))
            count = cursor.fetchone()[0]
            if count > 0:
                return True
        return False

    except psycopg2.Error as e:
        print("Ошибка при работе с базой данных(проверка на существующую запись):", e)
        return False

    finally:
        # Закрытие соединения с базой данных
        if connection:
            cursor.close()
            connection.close()


async def add_new_purchase_to_database(user_id, category_id, product_name, quantity, unit_cost):
    try:
        # Подключение к базе данных
        connection = psycopg2.connect(dbname=dbname, user=user, password=password, host=host, port=port)
        cursor = connection.cursor()

        # Вычисление общей стоимости покупки
        total_cost = float(quantity) * float(unit_cost)

        sql_query = "INSERT INTO \"Пользователь_Покупки\" (\"id_пользователя\", \"id_категории\", \"Название_продукта\", \"Количество_покупок\", \"Стоимость_ед\", \"Всего_затрат\", \"Дата_операции\") VALUES (%s, %s, %s, %s, %s, %s, %s)"
        cursor.execute(sql_query,
                       (user_id, category_id, product_name[:45], quantity, unit_cost, total_cost, date.today()))

        connection.commit()
    except psycopg2.Error as e:
        print("Ошибка при работе с базой данных:", e)
    finally:
        # Закрытие соединения с базой данных
        if connection:
            cursor.close()
            connection.close()


async def add_purchase_to_database(user_id, product_name, quantity, unit_cost):
    try:
        # Подключение к базе данных
        connection = psycopg2.connect(dbname=dbname, user=user, password=password, host=host, port=port)
        cursor = connection.cursor()

        # Находим категорию товара по имени продукта и user_id
        sql_query = "SELECT \"id_категории\" FROM \"Пользователь_Покупки\" WHERE \"id_пользователя\" = %s AND \"Название_продукта\" = %s"
        cursor.execute(sql_query, (user_id, product_name[:45]))
        category_id = cursor.fetchone()[0]

        # Вычисление общей стоимости покупки
        total_cost = float(quantity) * float(unit_cost)

        sql_query = "INSERT INTO \"Пользователь_Покупки\" (\"id_пользователя\", \"id_категории\", \"Название_продукта\", \"Количество_покупок\", \"Стоимость_ед\", \"Всего_затрат\", \"Дата_операции\") VALUES (%s, %s, %s, %s, %s, %s, %s)"
        cursor.execute(sql_query, (user_id, category_id, product_name[:45], quantity, unit_cost, total_cost, date.today()))
        connection.commit()

    except psycopg2.Error as e:
        print("Ошибка при работе с базой данных:", e)
    finally:
        # Закрытие соединения с базой данных
        if connection:
            cursor.close()
            connection.close()


async def delete_purchase_by_name(user_id, product_name):
    try:
        # Подключение к базе данных
        connection = psycopg2.connect(dbname=dbname, user=user, password=password, host=host, port=port)
        cursor = connection.cursor()

        # Удаление записи о покупке для данного товара и пользователя, добавленной в текущем месяце и году
        sql_query = "DELETE FROM \"Пользователь_Покупки\" WHERE \"id_пользователя\" = %s AND \"Название_продукта\" LIKE %s AND EXTRACT(MONTH FROM \"Дата_операции\") = EXTRACT(MONTH FROM CURRENT_DATE) AND EXTRACT(YEAR FROM \"Дата_операции\") = EXTRACT(YEAR FROM CURRENT_DATE)"
        cursor.execute(sql_query, (user_id, '%' + product_name.replace(' ', '-') + '%'))
        connection.commit()
    except psycopg2.Error as e:
        print("Ошибка при работе с базой данных:", e)
    finally:
        # Закрытие соединения с базой данных
        if connection:
            cursor.close()
            connection.close()


async def get_user_purchases_by_date(user_id, date):
    # Формируем строку соединения
    conn_string = f"dbname='{dbname}' user='{user}' password='{password}' host='{host}' port='{port}'"
    results = []
    try:
        # Устанавливаем соединение с базой данных
        connection = psycopg2.connect(conn_string)
        cursor = connection.cursor()
        # Получаем год и месяц из переданной даты
        year_month = date.strftime("%Y-%m")
        # Запрос для получения всех категорий пользователя
        category_query = f"""
                        SELECT DISTINCT id_категории 
                        FROM Пользователь_Покупки 
                        WHERE id_пользователя = {user_id}
                        AND DATE_TRUNC('month', Дата_операции) = DATE_TRUNC('month', TIMESTAMP '{year_month}-01')
                        """
        cursor.execute(category_query)
        categories = cursor.fetchall()
        # Запрос для получения товаров категории пользователя за указанный месяц
        for category in categories:
            category_id = category[0]
            product_query = f"""
                            SELECT 
                                Название_продукта, 
                                SUM(Количество_покупок) AS Количество_покупок, 
                                SUM(Стоимость_ед) AS Стоимость_ед, 
                                SUM(Всего_затрат) AS Всего_затрат
                            FROM Пользователь_Покупки 
                            WHERE id_пользователя = {user_id} 
                            AND id_категории = {category_id} 
                            AND DATE_TRUNC('month', Дата_операции) = DATE_TRUNC('month', TIMESTAMP '{year_month}-01')
                            GROUP BY Название_продукта;
                            """
            cursor.execute(product_query)
            products = cursor.fetchall()
            # Считаем сумму затрат в данной категории
            total_category_cost = sum(product[3] for product in products)

            # Собираем результаты запроса
            category_data = {
                "Категория": category_id,
                "Всего затрат в этой категории": round(total_category_cost, 2),
                "Продукты": []
            }
            for product in products:
                total_cost = round(product[3], 2)
                category_data["Продукты"].append({
                    "Продукт": product[0],
                    "Количество покупок": product[1],
                    "Стоимость за единицу": product[2],
                    "Всего затрат": total_cost
                })
            results.append(category_data)
        # Закрываем курсор и соединение с базой данных
        cursor.close()
        connection.close()
    except (Exception, Error) as error:
        print("Ошибка при работе с PostgreSQL:", error)
    return results


async def delete_current_month_purchases(user_id, month, year):
    # Формируем строку соединения
    conn_string = f"dbname='{dbname}' user='{user}' password='{password}' host='{host}' port='{port}'"
    # Подключаемся к базе данных
    conn = psycopg2.connect(conn_string)
    cur = conn.cursor()
    # Удаляем строки с текущим месяцем, годом и указанным user_id
    cur.execute(
        f"DELETE FROM Пользователь_Покупки WHERE EXTRACT(MONTH FROM Дата_операции) = %s AND EXTRACT(YEAR FROM Дата_операции) = %s AND id_пользователя = %s",
        (month, year, user_id))
    # Подтверждаем изменения в базе данных
    conn.commit()
    # Закрываем соединение
    cur.close()
    conn.close()
