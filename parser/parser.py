import asyncio
import multiprocessing
from threading import Thread
from pathlib import Path
import os

import aiohttp
import aiofiles


from headers.CURLs import CURL
from database.sqlite_db import Use
from create_bot_wb import bot
from inline_keyboards.menu import button_buy, button_size_buy, link_to_prod
from other import other
import config as cfg



# Функция для повторного запроса в случае неуспеха
async def repeat_request(url, headers, attempts=5):
    # Цикл попыток
    for attempt in range(attempts):
        # Запрос
        async with aiohttp.ClientSession() as session:
            response = await session.get(url=url, headers=headers)
            # Проверка - всё ли в порядке
            try:
                await response.json(content_type=None)
            except Exception as _ex:
                await asyncio.sleep(attempt * 5)

                # Если ни одна из попыток не увенчалась успехом
                # Пропускаем эту страницу
                if attempt == attempts - 1:
                    return False
                    break

            # Если всё хорошо останавливаем цикл и благополучно возвращаем json страницу
            else:
                return await response.json(content_type=None)
                break


# Асинхронный генератор json страниц
async def get_json(curl):
    db = Use()

    # Выбор категорий, которые будут парситься
    if await db.get_users_categories():
        user_categories = []
        for i in await db.get_users_categories():
            if i[0] not in user_categories:
                user_categories.append(i[0])

        if curl['category'] in user_categories:
            category = curl['category']
            headers = curl['headers']

            # Итерация по страницам категории
            for page in range(1, 101):
                # Формирование URL и Headers
                if page == 1:
                    headers['Referer'] = curl['headers']['Referer'].replace('_replace_me_', str(page))
                else:
                    headers['Referer'] = curl['headers']['Referer'].replace(str(page - 1), str(page))
                url = curl['url'].replace('_replace_me_', str(page))

                # Запрос и получение json страницы
                response_text = await repeat_request(url, headers)

                # Если страница не пострадала возвращаем её
                if response_text:
                    response_text['category'] = category

                    # Вытягивание данных
                    await get_data(response_text)
    await db.close()


data = []
async def get_data(response):
    global data
    for product in response['data']['products']:
        id = str(product['id'])
        price = product['salePriceU']
        category = response['category']
        link = f'https://www.wildberries.ru/catalog/{id}/detail.aspx?targetUrl=GP'
        image_link = f"https://images.wbstatic.net/c516x688/new/{id[:-4]}0000/{id}-1.jpg"
        name = product['name']

        try:
            product['sizes'][0]['rank']
        except:
            data.append([id, price, link, image_link, category, None, None, name])
        else:
            if product['colors'] and product['sizes'][0]['rank'] != 0:
                colors_list = [i['name'] for i in product['colors']]
                colors = ', '.join(colors_list)

                sizes_list = [i['name'] for i in product['sizes']]
                sizes = ', '.join(sizes_list)

                data.append([id, price, link, image_link, category, colors, sizes, name])
            elif product['colors']:
                colors_list = [i['name'] for i in product['colors']]
                colors = ', '.join(colors_list)

                data.append([id, price, link, image_link, category, colors, None, name])
            elif product['sizes'][0]['rank'] != 0:
                sizes_list = [i['name'] for i in product['sizes']]
                sizes = ', '.join(sizes_list)

                data.append([id, price, link, image_link, category, None, sizes, name])


def middleware(curl):
    db = Use()
    asyncio.run(get_json(curl))
    asyncio.run(db.add_new_prods(data))
    data.clear()
    asyncio.run(db.close())

async def start_pars():
    db = Use()

    await db.update_status_pars('active')

    try:
        with multiprocessing.Pool(cfg.count_pool) as p:
            p.map(middleware, CURL)
    except:
        await other.end_tasks()
    else:
        await other.end_tasks()

    await db.close()


async def start_parsing():
    db = Use()
    status = await db.get_status_pars()

    if status[0] == 'inactive':
        thread = Thread(target=asyncio.run, args=(start_pars(), ))
        thread.start()
    await db.close()


async def checker_and_sender():
    db = Use()
    user_category_ids = await db.get_categories_and_ids()

    # Проверка заказывали ли пользователи что-либо
    if user_category_ids:
        if await db.exists_good_prods():
            for i in user_category_ids:
                prod = await db.get_good_prod(str(i[1]))
                if prod != []:
                    if not await db.exist_in_shipped_items(str(i[0]), str(prod[0][2])):

                        # Скачивание картинки
                        image_link = prod[0][5]
                        async with aiohttp.ClientSession() as session:
                            async with session.get(image_link) as resp:
                                if resp.status == 200:
                                    path_to_file = str(Path(str(Path.cwd()), 'images', f'{i[0]}.jpg'))
                                    f = await aiofiles.open(path_to_file, mode='wb')
                                    await f.write(await resp.read())
                                    await f.close()

                        old_price = int(int(prod[0][3]) / 100)
                        new_price = int(int(prod[0][2]) / 100)
                        difference_price = old_price - new_price
                        text = f'🚗{prod[0][9]}🔥\n' \
                               f'<b>Категория:</b> {prod[0][6]}\n' \
                               f'<b>Текущая цена:</b> <b>{new_price} RUB</b>\n' \
                               f'<b>Прошлая цена:</b> {old_price} RUB\n' \
                               f'<b>Понижение:</b> {difference_price} RUB 🔻🔻'


                        # Добавление характеристик, если они есть
                        text_ = ''
                        if prod[0][7] and prod[0][8]:
                            text_ = text + f'\n<b>Цвет:</b> {prod[0][7]}' + f'\n<b>Размеры:</b> {prod[0][8]}'
                        elif prod[0][7]:
                            text_ = text + f'\n<b>Цвет:</b> {prod[0][7]}'
                        elif prod[0][8]:
                            text_ = text + f'\n<b>Размеры:</b> {prod[0][8]}'



                        exist_profile = await db.select_profile_status(str(i[0]))
                        exist_sub = await db.get_status_user(str(i[0]))

                        # Кидаем кнопку "Купить"
                        if exist_profile[0] == 'active' and exist_sub[0] == 'active':
                            if 'Размеры' in text_:
                                try:
                                    try:
                                        img = open(path_to_file, 'rb')
                                    except:
                                        pass
                                    else:
                                        await db.add_shipped_item(str(i[0]), str(prod[0][1]), str(prod[0][4]), str(prod[0][8]))
                                        await bot.send_photo(i[0], img)
                                        await bot.send_message(i[0], text_, parse_mode='HTML', reply_markup=await button_size_buy(prod[0][1]))
                                except Exception as _ex:
                                    print(_ex)
                            else:
                                try:
                                    try:
                                        img = open(path_to_file, 'rb')
                                    except:
                                        pass
                                    else:
                                        await db.add_shipped_item(str(i[0]), str(prod[0][1]), link=str(prod[0][4]))
                                        await bot.send_photo(i[0], img)
                                        await bot.send_message(i[0], text_, parse_mode='HTML', reply_markup=await button_buy(prod[0][1]))
                                except Exception as _ex:
                                    print(_ex)

                        # Кидаем без кнопки "Купить"
                        else:

                            # Определяем количество отправлений
                            count_send = await db.get_count_send(str(i[0]))
                            if int(count_send) <= int(cfg.count_send):
                                if 'Размеры' in text_:
                                    try:
                                        try:
                                            img = open(path_to_file, 'rb')
                                        except:
                                            pass
                                        else:
                                            await db.add_shipped_item(str(i[0]), str(prod[0][1]), str(prod[0][4]), str(prod[0][8]))
                                            await bot.send_photo(i[0], img)
                                            await bot.send_message(i[0], text_, parse_mode='HTML', reply_markup=await link_to_prod(prod[0][4]))
                                    except Exception as _ex:
                                        print(_ex)
                                else:
                                    try:
                                        try:
                                            img = open(path_to_file, 'rb')
                                        except:
                                            pass
                                        else:
                                            await db.add_shipped_item(str(i[0]), str(prod[0][1]), link=str(prod[0][4]))
                                            await bot.send_photo(i[0], img)
                                            await bot.send_message(i[0], text_, parse_mode='HTML', reply_markup=await link_to_prod(prod[0][4]))
                                    except Exception as _ex:
                                        print(_ex)

                                # Обновляем количество отправлений
                                await db.update_count_send(str(i[0]), int(count_send + 1))
                        try:
                            os.remove(path_to_file)
                        except Exception as _ex:
                            pass

        await db.clear_good_prod()
    await db.close()



# Уменьшаем 10 картинок в 10 раз
# Раскидываем




