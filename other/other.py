from database import sqlite_db

async def end_tasks():
    db = sqlite_db.Use()

    # Поиск подходящих товаров
    await db.compare()

    # Очищение старой таблицы
    await db.clear_old_prod()

    # Копирование из новой в старую
    await db.migration()

    # Очищение новой таблицы
    await db.clear_new_prod()

    await db.update_status_pars('inactive')


# Получение ключа по значение
async def get_key(dict_, value):
    for k, v in dict_.items():
        if v == value:
            return k


async def check_number(phone_number):
    if str(phone_number).isdigit():
        if len(str(phone_number)) == 10:
            return True
        else:
            return False
    else:
        return False


# Можно ли запускать
# async def permission_to_launch():



