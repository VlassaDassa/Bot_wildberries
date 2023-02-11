import time
from pathlib import Path
import asyncio
import os
import shutil
import random

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from fake_useragent import UserAgent

import config as cfg
from create_bot_wb import bot
from database.sqlite_db import Use
from keyboards import keyboard_client as kb



# Функция авторизации и сохранения профиля
def save_user_profile(phone_number, user_id, loop):
    db = Use()
    # Занесение в очередь
    db.set_browser_status(str(user_id))

    # Установка статуса на активный
    db.update_link_status(user_id, 'active')

    # Инициализация
    useragent = UserAgent()
    options = Options()

    # Сохранение профиля
    os.mkdir(str(Path(str(Path.cwd()), 'user_profiles', str(user_id))))
    path_to_user_profile = str(Path(str(Path.cwd()), 'user_profiles', str(user_id)))
    options.add_argument('-profile')
    options.add_argument(path_to_user_profile)

    options.headless = True
    a = random.sample(range(10), 3)
    port = int(str(random.randint(1, 9)) + str(a[0]) + str(a[1]) + str(a[2]))
    options.add_argument(f'user-agent={useragent.random}')

    try:
        driver = webdriver.Firefox(executable_path=cfg.path_to_driver, options=options, service_args=['--marionette-port', str(port)])
    except:
        text = '<b>Ошибка</b>\n' \
               'Повторите попытку позже'
        asyncio.run_coroutine_threadsafe(bot.send_message(user_id, text, reply_markup=kb.cl_kb, parse_mode='HTML'), loop)
        db.update_link_status(user_id, 'inactive')
        db.del_browser_status(str(user_id))
        driver.close()
        driver.quit()
        shutil.rmtree(path_to_user_profile)
    else:
        # Переход на сайт
        try:
            driver.get('https://www.wildberries.ru')
        except:
            text = '<b>Ошибка</b>\n' \
                   'Повторите попытку позже'
            asyncio.run_coroutine_threadsafe(bot.send_message(user_id, text, reply_markup=kb.cl_kb, parse_mode='HTML'),
                                             loop)
            db.update_link_status(user_id, 'inactive')
            db.del_browser_status(str(user_id))
            driver.close()
            driver.quit()
            shutil.rmtree(path_to_user_profile)
        else:
            time.sleep(3)

            # Нажимаем на кнопку "Войти"
            try:
                btn = driver.find_element_by_xpath('//*[@id="basketContent"]/div[2]/a/span')
                driver.execute_script('arguments[0].click();', btn)
            except:
                text = '<b>Ошибка</b>\n' \
                       'Возможно вы неверно ввели номер'
                asyncio.run_coroutine_threadsafe(bot.send_message(user_id, text, reply_markup=kb.cl_kb, parse_mode='HTML'), loop)

                driver.close()
                driver.quit()
                shutil.rmtree(path_to_user_profile)
            else:
                time.sleep(3)

                # Ввод номера
                try:
                    input_number = driver.find_element_by_xpath('//*[@id="spaAuthForm"]/div/div[1]/div/div[2]/input')
                    input_number.clear()
                    input_number.send_keys(phone_number)
                except:
                    print('[Ошибка] bot/51')
                    driver.close()
                    driver.quit()
                    shutil.rmtree(path_to_user_profile)
                else:
                    time.sleep(3)

                    # Нажатие на кнопку "Получить код"
                    try:
                        btn = driver.find_element_by_xpath('//*[@id="requestCode"]')
                        driver.execute_script('arguments[0].click();', btn)

                        # Повторное нажатие (на всякий)
                        try:
                            time.sleep(2)
                            btn = driver.find_element_by_xpath('//*[@id="requestCode"]')
                            driver.execute_script('arguments[0].click()', btn)
                        except:
                            pass
                    except:
                        print('[Ошибка] bot/51')
                        driver.close()
                        driver.quit()
                        shutil.rmtree(path_to_user_profile)
                    else:
                        time.sleep(30)

                        # Обнаружение капчи
                        try:
                            driver.find_element_by_xpath('//*[@id="spaAuthForm"]/div/div[2]/div/img')
                        except:
                            # Проверка кода в БД
                            code = db.get_user_code(user_id)
                            if code:

                                # Ввод кода
                                try:
                                    code_input = driver.find_element_by_xpath('//*[@id="spaAuthForm"]/div/div[3]/div/input')
                                    code_input.clear()
                                    code_input.send_keys(code[0])
                                except:
                                    print('[Ошибка] bot/51')
                                    driver.close()
                                    driver.quit()
                                    shutil.rmtree(path_to_user_profile)
                                else:
                                    time.sleep(2)

                                    # Проверка: верный ли код
                                    try:
                                        driver.find_element_by_xpath('//*[@id="spaAuthForm"]/div/div[3]/div/input')
                                    except:
                                        text = 'Аккаунт успешно привязан!'
                                        asyncio.run_coroutine_threadsafe(bot.send_message(user_id, text, reply_markup=kb.cl_kb), loop)
                                        driver.close()
                                        driver.quit()

                                        # Обновление статуса профиля
                                        db.update_profile_status(user_id, 'active')
                                    else:
                                        text = 'Вы ввели неверный код'
                                        asyncio.run_coroutine_threadsafe(bot.send_message(user_id, text, reply_markup=kb.cl_kb), loop)
                                        driver.close()
                                        driver.quit()
                                        time.sleep(2)
                                        shutil.rmtree(path_to_user_profile)
                            else:
                                text = 'Вы не успели ввести код, либо превысили лимит авторизаций\n' \
                                       'Подождите немного'
                                asyncio.run_coroutine_threadsafe(bot.send_message(user_id, text, reply_markup=kb.cl_kb), loop)
                                driver.close()
                                driver.quit()
                                shutil.rmtree(path_to_user_profile)

                        # Если есть капча
                        else:
                            # Сохранение картинки капчи
                            captcha_path = str(Path(str(Path.cwd()), 'captcha_image', f'{user_id}.png'))

                            with open(captcha_path, "wb") as elem_file:
                                elem_file.write(driver.find_element_by_xpath('/html/body/div[1]/main/div[2]/div/div[2]/div/div/form/div/div[2]/div/img').screenshot_as_png)

                            # Получение капчи от пользователя
                            text = 'Обнаружена Captcha, введите её\n' \
                                   '`/captcha` код'

                            image = open(captcha_path, 'rb')
                            asyncio.run_coroutine_threadsafe(bot.send_photo(user_id, image, caption=text, parse_mode='MARKDOWN'), loop)

                            # Удаление изображения капчи
                            time.sleep(30)
                            os.remove(captcha_path)

                            # Получение кода капчи из БД
                            captcha = db.get_user_captcha(user_id)
                            if captcha:

                                # Ввод капчи
                                try:
                                    captcha_input = driver.find_element_by_xpath('//*[@id="smsCaptchaCode"]')
                                    captcha_input.clear()
                                    captcha_input.send_keys(captcha[0])
                                except Exception as _ex:
                                    text = '<b>Ошибка</b>\n' \
                                           'Повторите попытку позже'
                                    asyncio.run_coroutine_threadsafe(bot.send_message(user_id, text, reply_markup=kb.cl_kb, parse_mode='HTML'), loop)
                                    db.update_link_status(user_id, 'inactive')
                                    db.del_browser_status(str(user_id))
                                    driver.close()
                                    driver.quit()
                                    shutil.rmtree(path_to_user_profile)
                                else:
                                    # Нажать на кнопку "Продолжить"
                                    try:
                                        btn = driver.find_element_by_xpath('/html/body/div[1]/main/div[2]/div/div[2]/div/div/form/div/div[2]/button')
                                        driver.execute_script('arguments[0].click();', btn)
                                    except Exception as _ex:
                                        text = '<b>Ошибка</b>\n' \
                                               'Повторите попытку позже'
                                        asyncio.run_coroutine_threadsafe(
                                            bot.send_message(user_id, text, reply_markup=kb.cl_kb, parse_mode='HTML'),
                                            loop)
                                        db.update_link_status(user_id, 'inactive')
                                        db.del_browser_status(str(user_id))
                                        driver.close()
                                        driver.quit()
                                        shutil.rmtree(path_to_user_profile)
                                    else:
                                        time.sleep(3)
                                        # Проверка на правильность капчи
                                        try:
                                            driver.find_element_by_xpath('//*[@id="spaAuthForm"]/div/div[3]/div/input')
                                        except:
                                            driver.close()
                                            driver.quit()
                                            shutil.rmtree(path_to_user_profile)
                                            text = '<b>Ошибка</b>\n' \
                                                   'Неверный код капчи. Подождите и повторите снова'
                                            asyncio.run_coroutine_threadsafe(bot.send_message(user_id, text, parse_mode='HTML', reply_markup=kb.cl_kb), loop)
                                        else:
                                            text = 'В ближайшую минуту вам придёт код\n' \
                                                   'Введите его: `/send_code` код'
                                            asyncio.run_coroutine_threadsafe(bot.send_message(user_id, text, parse_mode='MARKDOWN', reply_markup=kb.cl_kb), loop)

                                            time.sleep(40)

                                            # Получение кода
                                            code = db.get_user_code(user_id)
                                            if code:
                                                input_code = driver.find_element_by_xpath('//*[@id="spaAuthForm"]/div/div[3]/div/input')
                                                input_code.clear()
                                                input_code.send_keys(code[0])

                                                time.sleep(3)

                                                # Проверка ввёлся ли код
                                                try:
                                                    driver.find_element_by_xpath('//*[@id="spaAuthForm"]/div/div[3]/div/input')
                                                except:
                                                    text = 'Аккаунт успешно привязан!'
                                                    asyncio.run_coroutine_threadsafe(bot.send_message(user_id, text, reply_markup=kb.cl_kb), loop)
                                                    driver.close()
                                                    driver.quit()

                                                    # Обновление статуса профиля
                                                    db.update_profile_status(user_id, 'active')
                                                else:
                                                    driver.close()
                                                    driver.quit()
                                                    shutil.rmtree(path_to_user_profile)
                                                    text = '<b>Ошибка</b>\n' \
                                                           'Неверный код'
                                                    asyncio.run_coroutine_threadsafe(bot.send_message(user_id, text, parse_mode='HTML', reply_markup=kb.cl_kb), loop)
                                            else:
                                                driver.close()
                                                driver.quit()
                                                shutil.rmtree(path_to_user_profile)
                                                text = '<b>Ошибка</b>\n' \
                                                       'Вы не успели ввести код. Повторите попытку позже'
                                                asyncio.run_coroutine_threadsafe(bot.send_message(user_id, text, parse_mode='HTML', reply_markup=kb.cl_kb), loop)

                            else:
                                driver.close()
                                driver.quit()
                                text = 'Вы не успели ввести капчу\n' \
                                       'Повторите попытку позже'
                                asyncio.run_coroutine_threadsafe(bot.send_message(user_id, text, reply_markup=kb.cl_kb), loop)
                                shutil.rmtree(path_to_user_profile)

                            if db.get_user_captcha(user_id):
                                db.del_user_captcha(user_id)

    db.update_link_status(user_id, 'inactive')
    db.del_browser_status(str(user_id))

    # Удаление подтверждающего кода
    if db.get_user_code(user_id):
        db.del_user_code(user_id)

    try:
        driver.close()
        driver.quit()
        db.sync_close()
    except:
        pass



# Функция покупки
def buy_prod(user_id, size, link, loop):
    db = Use()
    db.set_browser_status(str(user_id))
    try:
        # Сделать выбор того, что покупать (размер, цвет)
        useragent = UserAgent()
        options = Options()

        # Опции
        options.headless = True
        options.add_argument(f'user-agent={useragent.random}')

        # Открытие профиля
        path_to_user_profile = str(Path(str(Path.cwd()), 'user_profiles', str(user_id)))
        user_profile = webdriver.FirefoxProfile(path_to_user_profile)

        driver = webdriver.Firefox(executable_path=cfg.path_to_driver, options=options, firefox_profile=user_profile)

        # Переход на страницу продукта
        try:
            driver.get(link)
        except Exception as _ex:
            print(_ex)
            text = '<b>Ошибка</b>' \
                   'У нас не получилось купить товар'
            asyncio.run_coroutine_threadsafe(bot.send_message(user_id, text, reply_markup=kb.cl_kb, parse_mode='HTML'), loop)
            driver.close()
            driver.quit()
        else:
            time.sleep(3)

            if size:
                # Выбор размера:
                for i in range(1, 1000):
                    try:
                        path_element = f'/html/body/div[1]/main/div[2]/div/div[3]/div/div[3]/div[4]/div[4]/ul/li[{i}]/label'
                        element = driver.find_element_by_xpath(path_element).text
                    except:
                        # мессаге
                        break
                    else:
                        if str(size) in str(element):
                            try:
                                btn = driver.find_element_by_xpath(path_element)
                                driver.execute_script('arguments[0].click();', btn)
                            except Exception as _ex:
                                print('1')
                                print(_ex)
                                text = '<b>Ошибка</b>\n' \
                                       'У нас не получилось купить товар'
                                asyncio.run_coroutine_threadsafe(
                                    bot.send_message(user_id, text, reply_markup=kb.cl_kb, parse_mode='HTML'), loop)
                                driver.close()
                                driver.quit()
                                break
                            else:
                                time.sleep(3)

                                # Нажатие на кнопку "Купить сейчас"
                                try:
                                    btn = driver.find_element_by_xpath('/html/body/div[1]/main/div[2]/div/div[3]/div/div[3]/div[8]/div[1]/div/button[1]')
                                    driver.execute_script('arguments[0].click();', btn)
                                except Exception as _ex:
                                    print('2')
                                    print(_ex)
                                    text = '<b>Ошибка</b>\n' \
                                           'У нас не получилось купить товар'
                                    asyncio.run_coroutine_threadsafe(bot.send_message(user_id, text, reply_markup=kb.cl_kb, parse_mode='HTML'), loop)
                                    driver.close()
                                    driver.quit()
                                    break
                                else:
                                    time.sleep(7)

                                    # Нажатие на кнопку "Оплатить"
                                    try:
                                        btn = driver.find_element_by_xpath('/html/body/div[1]/main/div[2]/div/div[2]/div/div[1]/form/div[2]/div/div/div/div[4]/button')
                                        driver.execute_script('arguments[0].click();', btn)
                                    except Exception as _ex:
                                        print('3')
                                        print(_ex)
                                        text = '<b>Ошибка</b>\n' \
                                               'У нас не получилось купить товар'
                                        asyncio.run_coroutine_threadsafe(bot.send_message(user_id, text, reply_markup=kb.cl_kb, parse_mode='HTML'), loop)
                                        driver.close()
                                        driver.quit()
                                        break
                                    else:
                                        text = 'Товар успешно заказан!'
                                        asyncio.run_coroutine_threadsafe(bot.send_message(user_id, text, reply_markup=kb.cl_kb), loop)
                                        driver.close()
                                        driver.quit()
                                        time.sleep(2)
                                        break
            else:
                # Нажатие на кнопку "Купить сейчас"
                try:
                    btn = driver.find_element_by_xpath('/html/body/div[1]/main/div[2]/div/div[3]/div/div[3]/div[8]/div[1]/div/button[1]')
                    driver.execute_script('arguments[0].click();', btn)
                except Exception as _ex:
                    print('4')
                    print(_ex)
                    text = '<b>Ошибка</b>\n' \
                           'У нас не получилось купить товар'
                    asyncio.run_coroutine_threadsafe(
                        bot.send_message(user_id, text, reply_markup=kb.cl_kb, parse_mode='HTML'), loop)
                    driver.close()
                    driver.quit()
                else:
                    time.sleep(7)

                    # Нажатие на кнопку "Оплатить"
                    try:
                        btn = driver.find_element_by_xpath('/html/body/div[1]/main/div[2]/div/div[2]/div/div[1]/form/div[2]/div/div/div/div[4]/button')
                        driver.execute_script('arguments[0].click();', btn)
                    except Exception as _ex:
                        print('5')
                        print(_ex)
                        text = '<b>Ошибка</b>\n' \
                               'У нас не получилось купить товар'
                        asyncio.run_coroutine_threadsafe(bot.send_message(user_id, text, reply_markup=kb.cl_kb, parse_mode='HTML'), loop)
                        driver.close()
                        driver.quit()
                    else:
                        text = 'Товар успешно заказан!'
                        asyncio.run_coroutine_threadsafe(bot.send_message(user_id, text, reply_markup=kb.cl_kb), loop)
                        driver.close()
                        driver.quit()

        db.del_browser_status(str(user_id))
        db.sync_close()

        try:
            driver.close()
            driver.quit()
        except:
            pass

    except Exception as _ex:
        print('7')
        text = '<b>Ошибка</b>\n' \
               'У нас не получилось купить товар'
        asyncio.run_coroutine_threadsafe(bot.send_message(user_id, text, reply_markup=kb.cl_kb, parse_mode='HTML'), loop)
        print(_ex)
        db.del_browser_status(str(user_id))
        db.sync_close()
        try:
            driver.close()
            driver.quit()
        except:
            pass



