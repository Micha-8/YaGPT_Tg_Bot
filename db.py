import sqlite3

from config import DB_NAME, DB_TABLE_USERS_NAME, ADMINS


def create_db():
    connection = sqlite3.connect(DB_NAME)
    connection.close()


def execute_query(query: str, data: tuple | None = None, db_name: str = DB_NAME):
    try:
        connection = sqlite3.connect(db_name)
        cursor = connection.cursor()

        if data:
            cursor.execute(query, data)
            connection.commit()

        else:
            cursor.execute(query)

    except sqlite3.Error as e:
        print("Ошибка при выполнении запроса: ", e)

    else:
        result = cursor.fetchall()
        connection.close()
        return result


def create_table():
    sql_query = (
        f"CREATE TABLE IF NOT EXISTS {DB_TABLE_USERS_NAME} "
        f"(id INTEGER PRIMARY KEY, "
        f"user_id INTEGER, "
        f"sessions INTEGER, "
        f"tokens INTEGER, "
        f"genre TEXT, "
        f"character TEXT, "
        f"setting TEXT, "
        f"additional_info TEXT, "
        f"messages TEXT);"
    )

    execute_query(sql_query)
    print("Таблица успешно создана")


def add_new_user(user_id: int):
    if not is_user_in_db(user_id):
        sql_query = (
            f"INSERT INTO {DB_TABLE_USERS_NAME} "
            f"(user_id, sessions) "
            f"VALUES (?, 0);"
        )

        execute_query(sql_query, (user_id,))
        print("Пользователь успешно добавлен")
    else:
        print("Пользователь уже существует!")


def is_user_in_db(user_id: int) -> bool:
    sql_query = f"SELECT user_id " f"FROM {DB_TABLE_USERS_NAME} " f"WHERE user_id = ?;"
    return bool(execute_query(sql_query, (user_id,)))


def update_row(user_id: int, column_name: str, new_value: str | int | None):
    if is_user_in_db(user_id):
        sql_query = (
            f"UPDATE {DB_TABLE_USERS_NAME} "
            f"SET {column_name} = ? "
            f"WHERE user_id = ?;"
        )

        execute_query(sql_query, (new_value, user_id))
        print("Значение обновлено")

    else:
        print("Пользователь не найден в базе")


def get_user_data(user_id: int):
    if is_user_in_db(user_id):
        sql_query = (
            f"SELECT * "
            f"FROM {DB_TABLE_USERS_NAME} "
            f"WHERE user_id = {user_id}"
        )

        row = execute_query(sql_query)[0]
        result = {
            "sessions": row[2],
            "tokens": row[3],
            "genre": row[4],
            "character": row[5],
            "setting": row[6],
            "additional_info": row[7],
            "messages": row[8],
        }
        return result


def get_all_users_data() -> list[tuple[int, int, int, int, str, str, str, str, str, str]]:
    sql_query = (
        f"SELECT * "
        f"FROM {DB_TABLE_USERS_NAME};"
    )

    result = execute_query(sql_query)
    return result


def delete_user(user_id: int):
    if is_user_in_db(user_id):
        sql_query = (
            f"DELETE "
            f"FROM {DB_TABLE_USERS_NAME} "
            f"WHERE user_id = ?;"
        )

        execute_query(sql_query, (user_id,))
        print("Пользователь удалён")

    else:
        print("Пользователь не найден в базе")

