from pathlib import Path

from aiogram import Dispatcher, types
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup


from create_bot_wb import bot
from keyboards import keyboard_client as client_kb
from keyboards import keyboard_admin as ad_kb
import config as cfg
from database.sqlite_db import Use

db = Use()


async def admin(message: types.Message):
    if str(message.from_user.id) not in cfg.admin_id:
        await message.answer('Вы не администратор')
    else:
        await message.answer('Режим администратора', reply_markup=ad_kb.adm_kb)




class FSM_edit_message(StatesGroup):
    choice_msg = State()
    msg = State()
    edit_or_cancel = State()

# Изменить сообщение
async def edit_message(message: types.Message):
    if str(message.from_user.id) not in cfg.admin_id:
        await message.answer('Вы не администратор')
    else:
        text = '<b>Изменение сообщений</b>\n' \
                'Вы можете изменить сообщение, в кнопках: "Помощь", "Реферальная система", "Тарифы" и стартовое сообщение'
        text_1 = 'Чтобы сделать текст жирным заключите его в <b>эти тэги</b>\n' \
                 'Для кнопки "Реферальная система" необходимо указать место реферальной ссылки. Напишите <ссылка> в месте где должно находиться ссылка\n' \
                 'Для кнопки "Реферальная система" необходимо указать место количества рефералов. Напишите <кол-во> в месте, где должно отображаться кол-во рефералов\n' \
                 'Выберите сообщение'

        await message.answer(text, parse_mode='HTML')
        await message.answer(text_1, reply_markup=ad_kb.choice_edit_btn)
        await FSM_edit_message.choice_msg.set()

async def edit_message_2(message: types.Message, state: FSMContext):
    if message.text in ['Помощь 🔎', 'Рефералы 👥', 'Тарифы 👛', 'Стартовое сообщение']:
        async with state.proxy() as data:
            data['category'] = message.text
            await message.answer('Введите новое сообщение', reply_markup=ad_kb.remove_kb)
            await FSM_edit_message.msg.set()
    else:
        await message.answer('Неверный вариант ответа', reply_markup=ad_kb.adm_kb)
        await state.finish()

async def edit_message_3(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['msg'] = message.text
        try:
            await message.answer(f'<b>Ваш текст</b>\n{message.text}', reply_markup=ad_kb.cancel_or_edit, parse_mode='HTML')
        except:
            if '<ссылка>' in message.text:
                await message.answer(f'Ваш текст\n{message.text}', reply_markup=ad_kb.cancel_or_edit)
                await FSM_edit_message.edit_or_cancel.set()
            else:
                await message.answer('<b>Ошибка</b>\n'
                                     'Видимо вы отклонились от инструкции', reply_markup=ad_kb.adm_kb, parse_mode='HTML')
                await state.finish()
        else:
            await FSM_edit_message.edit_or_cancel.set()

async def edit_message_4(message: types.Message, state: FSMContext):
    if message.text == 'Сохранить 💾':
        async with state.proxy() as data:
            if await db.exist_msg(str(data['category'])):
                await db.update_message(str(data['category']), str(data['msg']))
            else:
                await db.add_message(str(data['category']), str(data['msg']))
        await message.answer('Сообщение отредактировано', reply_markup=ad_kb.adm_kb)

    elif message.text == 'Отменить ❌':
        await message.answer('Изменение отменено', reply_markup=ad_kb.adm_kb)
    else:
        await message.answer('Неверный вариант ответа', reply_markup=ad_kb.adm_kb)

    await state.finish()



# Кол-во пользователей
async def quantity_users(message: types.Message):
    if str(message.from_user.id) not in cfg.admin_id:
        await message.answer('Вы не администратор')
    else:
        total_number_users = await db.get_quantity_users()
        total_subs = await db.get_quantity_sub_users()

        text = f'<b>Общее количество пользователей:</b> {total_number_users}\n' \
               f'<b>Количество пользователей с подпиской:</b> {total_subs}'
        await message.answer(text, parse_mode='HTML')



class FSM_send_message(StatesGroup):
    msg = State()
    cancel_or_send = State()

async def send_message(message: types.Message):
    if str(message.from_user.id) not in cfg.admin_id:
        await message.answer('Вы не администратор')
    else:
        text = '<b>Сообщение всем пользователям</b>'
        text_1 = 'Чтобы сделать текст жирным заключите его в <b>эти тэги</b>\n' \
                 'Напишите сообщение'

        await message.answer(text, parse_mode='HTML', reply_markup=ad_kb.remove_kb)
        await message.answer(text_1)

        await FSM_send_message.msg.set()

async def send_message_2(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['msg'] = message.text
    text = f'<b>Ваше сообщение:</b>\n{message.text}'
    await message.answer(text, parse_mode='HTML', reply_markup=ad_kb.send_or_cancel) # отмена, отправить
    await FSM_send_message.cancel_or_send.set()

async def send_message_3(message: types.Message, state: FSMContext):
    if message.text == 'Отменить ❌':
        await message.answer('Отправка сообщения отменена', reply_markup=ad_kb.adm_kb)
    elif message.text == 'Отправить ✅':
        await message.answer('Отправляем сообщение', reply_markup=ad_kb.adm_kb)
        if await db.get_user_ids():
            async with state.proxy() as data:
                for tgid in await db.get_user_ids():
                    await bot.send_message(str(tgid[0]), data['msg'], parse_mode='HTML')
            await message.answer('Сообщение отправлено ✅')
        else:
            await message.answer('Не кому отправлять сообщения')
    else:
        await message.answer('Неверный вариант ответа', reply_markup=ad_kb.adm_kb)

    await state.finish()


async def back(message: types.Message):
    if str(message.from_user.id) not in cfg.admin_id:
        await message.answer('Вы не администратор')
    else:
        await message.answer('Режим пользователя', reply_markup=client_kb.cl_kb)



class FSM_edit_payments(StatesGroup):
    image = State()
    price = State()
    title = State()
    description = State()
    choice = State()

# Изменение данных платежа
async def edit_pay(message: types.Message):
    if str(message.from_user.id) not in cfg.admin_id:
        await message.answer('Вы не администратор')
    else:
        text = '<b>Измените данные для выставления счёта:</b>\n' \
               '    1. Фото\n' \
               '    2. Цена\n' \
               '    3. Название\n' \
               '    4. Описание'
        await message.answer(text, parse_mode='HTML', reply_markup=ad_kb.adm_kb)

        text_2 = 'Пришлите URL фото\n' \
                 'Если вам не нужно фото, пришлите "нет"'
        await message.answer(text_2, parse_mode='HTML', reply_markup=ad_kb.remove_kb)
        await FSM_edit_payments.image.set()

async def edit_pay_2(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        if 'нет' == str(message.text):
            data['image'] = 'None'
        else:
            data['image'] = str(message.text)

    await message.answer('Пришлите цену', reply_markup=ad_kb.remove_kb)

    await FSM_edit_payments.price.set()

async def edit_pay_3(message: types.Message, state: FSMContext):
    try:
        int(message.text)
    except:
        await message.answer('Введите целое число', reply_markup=ad_kb.adm_kb)
        await state.finish()
    else:
        if int(message.text) >= 100:

            async with state.proxy() as data:
                data['price'] = int(message.text)

            await message.answer('Введите название платежа', reply_markup=ad_kb.remove_kb)
            await FSM_edit_payments.title.set()
        else:
            await message.answer('Введите цену больше 100', reply_markup=ad_kb.adm_kb)
            await state.finish()

async def edit_pay_4(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['title'] = str(message.text)

    await message.answer('Введите описание')
    await FSM_edit_payments.description.set()

async def edit_pay_5(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['description'] = message.text

    await message.answer('Сохранить изменения?', reply_markup=ad_kb.pay_edit)
    await FSM_edit_payments.choice.set()


async def edit_pay_6(message: types.Message, state: FSMContext):
    if 'Сохранить ✅' == str(message.text):
        async with state.proxy() as data:
            # Занесение в БД
            data_pay = (data['image'], data['price'], data['title'], data['description'],)
            await db.delete_pay_inf()
            await db.add_pay_inf(data_pay)

            await message.answer('Данные платежа изменены ✅', reply_markup=ad_kb.adm_kb)
    else:
        await message.answer('Изменения отменены ❌', reply_markup=ad_kb.adm_kb)

    await state.finish()



class FSM_give_sub(StatesGroup):
    choice = State()
    user_id = State()
    choice_days = State()

async def give_sub(message: types.Message):
    if str(message.from_user.id) not in cfg.admin_id:
        await message.answer('Вы не администратор')
    else:
        await message.answer('Выберите кому дать подписку', reply_markup=ad_kb.choice_whom)
        await FSM_give_sub.choice.set()


async def give_sub_2(message: types.Message, state: FSMContext):
    if message.text in ['Другому пользователю', 'Себе']:
        if message.text == 'Себе':
            await db.update_user_status(str(message.from_user.id), 'active')
            await message.answer('Подписка успешно выдана', reply_markup=ad_kb.adm_kb)
            await state.finish()
        elif message.text == 'Другому пользователю':
            txt = 'Введите ID пользователя\n' \
                  '<i>Пользователь может узнать его, прописав <b>/id</b> боту</i>\n'
            await message.answer(txt, parse_mode='HTML', reply_markup=ad_kb.remove_kb)
            await FSM_give_sub.user_id.set()
    else:
        await message.answer('Нет такого варианта', reply_markup=ad_kb.adm_kb)
        await state.finish()


async def give_sub_3(message: types.Message, state: FSMContext):
    # Проверка есть ли этот пользователь в БД
    exist_user = await db.exist_user(str(message.text))
    if exist_user:
        async with state.proxy() as data:
            data['user_id'] = str(message.text)
            await message.answer('Выберите количество дней подписки', reply_markup=await ad_kb.count_days())
            await FSM_give_sub.choice_days.set()
    else:
        await message.answer('Нет пользователя с таким ID', reply_markup=ad_kb.adm_kb)
        await state.finish()


async def give_sub_4(message: types.Message, state: FSMContext):
    if int(message.text) in range(1, 8):
        async with state.proxy() as data:
            days = int(message.text)
            cur_days = await db.get_sub_days(data['user_id'])
            new_days = cur_days - days
            await db.update_sub_days(data['user_id'], new_days)
            await db.update_user_status(data['user_id'], 'active')
            await message.answer(f'Подписка на {message.text} дней выдана', reply_markup=ad_kb.adm_kb)
    else:
        await message.answer('Нет такого варианта ответа', reply_markup=ad_kb.adm_kb)
    await state.finish()





def register_handlers_client(dp: Dispatcher):
    dp.register_message_handler(admin, Text(equals=cfg.admin_password), chat_type='private')
    dp.register_message_handler(edit_message, Text(equals='Изменить сообщения ✏'), chat_type='private')
    dp.register_message_handler(edit_message_2, state=FSM_edit_message.choice_msg, chat_type='private')
    dp.register_message_handler(edit_message_3, state=FSM_edit_message.msg, chat_type='private')
    dp.register_message_handler(edit_message_4, state=FSM_edit_message.edit_or_cancel, chat_type='private')
    dp.register_message_handler(quantity_users, Text(equals='Количество пользователей 👥'), chat_type='private')
    dp.register_message_handler(send_message, Text(equals='Отправить всем сообщение ✉'), chat_type='private')
    dp.register_message_handler(send_message_2, state=FSM_send_message.msg, chat_type='private')
    dp.register_message_handler(send_message_3, state=FSM_send_message.cancel_or_send, chat_type='private')
    dp.register_message_handler(back, Text(equals='Вернуться 💤'), chat_type='private')

    dp.register_message_handler(edit_pay, Text(equals='Изменить платёж 👛'), chat_type='private')
    dp.register_message_handler(edit_pay_2, state=FSM_edit_payments.image, chat_type='private')
    dp.register_message_handler(edit_pay_3, state=FSM_edit_payments.price, chat_type='private')
    dp.register_message_handler(edit_pay_4, state=FSM_edit_payments.title, chat_type='private')
    dp.register_message_handler(edit_pay_5, state=FSM_edit_payments.description, chat_type='private')
    dp.register_message_handler(edit_pay_6, state=FSM_edit_payments.choice, chat_type='private')
    
    dp.register_message_handler(give_sub, Text(equals='Выдать подписку'), chat_type='private')
    dp.register_message_handler(give_sub_2, state=FSM_give_sub.choice, chat_type='private')
    dp.register_message_handler(give_sub_3, state=FSM_give_sub.user_id, chat_type='private')
    dp.register_message_handler(give_sub_4, state=FSM_give_sub.choice_days, chat_type='private')


