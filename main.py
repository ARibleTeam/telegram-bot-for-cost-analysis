import asyncio
import logging

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters.command import Command
import re #регулярное выражение
import data_base
import charts
import data_base, request, navigation
from aiogram.enums import ParseMode
from datetime import datetime
import os
from PIL import Image

MAX_FILE_SIZE_MB = 10  # Максимальный размер файла в мегабайтах
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024


async def send_photo_split_if_needed(chat_id, photo_path, bot, navigation, date):
    # Получаем размер файла
    file_size = os.path.getsize(photo_path)

    if file_size < MAX_FILE_SIZE_BYTES:
        # Если размер файла меньше 10 МБ, отправляем его
        await bot.send_photo(chat_id, photo=types.FSInputFile(photo_path),
                             caption="💰<b>Ваш отчёт по расходам</b>💰",
                             parse_mode='HTML',
                             reply_markup=await navigation.get_keyboard(date))
    else:
        # Если файл больше 10 МБ, разбиваем его на части
        await split_and_send_image(chat_id, photo_path, bot, navigation, date)


def is_solid_line(img, center_y, width):
    """Проверка, является ли линия на заданной высоте однородной по цвету (800 пикселей от центра)"""
    if center_y >= img.height or center_y < 0:
        return False  # Проверка на выход за границы изображения по высоте

    center_x = width // 2
    line_color = img.getpixel((center_x, center_y))  # Получаем цвет центрального пикселя

    # Проверяем 400 пикселей влево и 400 пикселей вправо от центра
    for x in range(max(center_x - 400, 0), min(center_x + 400, width)):
        if img.getpixel((x, center_y)) != line_color:
            return False  # Линия не однородная
    return True  # Линия однородная


async def split_and_send_image(chat_id, photo_path, bot, navigation, date):
    # Открываем изображение
    img = Image.open(photo_path)

    # Рассчитываем, на сколько частей надо разделить изображение
    width, height = img.size
    num_splits = int(os.path.getsize(photo_path) / MAX_FILE_SIZE_BYTES) + 1
    split_height = height // num_splits

    start_y = 0  # Начальная координата для разделения

    for i in range(num_splits):
        end_y = min(start_y + split_height, height)  # Конечная точка разреза

        # Ищем сплошную горизонтальную линию в точке разреза
        while end_y < height and not is_solid_line(img, end_y, width):
            end_y += 4  # Если линия не однородная, сдвигаемся на 2 пикселя вниз

        # Вырезаем часть изображения
        cropped_img = img.crop((0, start_y, width, end_y))

        # Сохраняем эту часть во временный файл
        temp_path = f"temp_part_{i}.png"
        cropped_img.save(temp_path)

        # Определяем, нужно ли добавлять reply_markup для последней части
        reply_markup = await navigation.get_keyboard(date) if i == num_splits - 1 else None

        # Отправляем часть изображения
        await bot.send_photo(chat_id, photo=types.FSInputFile(temp_path), reply_markup=reply_markup)

        # Удаляем временный файл после отправки
        os.remove(temp_path)

        # Обновляем начальную координату для следующего разделения
        start_y = end_y


# Функция для добавления/обновления/удаления данных через чат
async def check_command_syntax(text, user_id):
    # Регулярное выражение для первого формата команды: число, число, текст
    pattern1 = r'^\d+(\.\d+)?\s+\d+(\.\d+)?\s+.+$'

    # Регулярное выражение для второго формата команды: минус, пробел, текст
    pattern2 = r'^-\s+.+$'

    spl_text = text.split(' ')

    # Проверяем текст на соответствие первому или второму формату команды.
    if re.match(pattern1, text) and len(spl_text) == 3:
        if data_base.check_existing_purchase(user_id, spl_text[2]):
            # Обновляем базу данных
            await data_base.add_purchase_to_database(user_id, spl_text[2], spl_text[1], spl_text[0])
        else:
            # Отправляем таблицу с категориями для выбора. Заносим новые данные в таблицу
            await bot.send_message(user_id, f"Выберите категорию:\n\nНазвание товара: <b>{spl_text[2]}</b> \n\nКоличество: <b>{spl_text[1]}</b> \nСтоимость: <b>{spl_text[0]}</b>", reply_markup= await navigation.keyboard_category(), parse_mode=ParseMode.HTML)

    elif re.match(pattern2, text) and len(spl_text) == 2:
        await data_base.delete_purchase_by_name(user_id, spl_text[1])


async def add_new_purchase_from_qr(user_id, product_name, quantity, unit_cost):
    if data_base.check_existing_purchase(user_id, product_name):
        # Обновляем базу данных
        await data_base.add_purchase_to_database(user_id, product_name, quantity, unit_cost)
    else:
        # Отправляем таблицу с категориями для выбора. Заносим новые данные в таблицу
        await bot.send_message(user_id, f"Выберите категорию:\n\nНазвание товара: <b>{product_name}</b> \n\nКоличество: <b>{quantity}</b> \nСтоимость: <b>{unit_cost}</b>", reply_markup=await navigation.keyboard_category(), parse_mode=ParseMode.HTML)


# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)
# Объект бота
bot = Bot(token="YOUR_TOKEN")
# Диспетчер
dp = Dispatcher()


# Обработчик, который реагирует на команду /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    kb = [[types.KeyboardButton(text="ОТЧЕТ")]]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    await message.answer("🔴<b>ИНСТРУКЦИЯ</b>🔴\n\nДля добавления покупки напишите в чат:\n1. (<b>Стоимость_единицы</b>)\n2. (<b>Количество</b>)\n3. (<b>Название_продукта</b>)\nНапример: 100 1 картошка\n\n<b>Или пришлите чек с QR-кодом.</b>\n\n<b>Для удаления покупки напишите в чат:</b>\n(<b>-</b>) (<b>Название_продукта</b>)\nНапример: - картошка.", reply_markup=keyboard, parse_mode='HTML')

    await data_base.add_user_to_database(message.chat.id, message.chat.username, message.chat.first_name)

    await bot.send_photo(message.chat.id, photo=types.FSInputFile(await navigation.create_photo(message.chat.id, datetime.now())), caption="💰<b>Ваш отчёт по расходам</b>💰", parse_mode='HTML', reply_markup=await navigation.get_keyboard(datetime.now()))


@dp.message(F.photo)
async def handle_photo(message: types.Message):
    await bot.download(message.photo[-1], destination=(f"user_data/{message.photo[-1].file_id}.jpg"))
    await bot.delete_message(message.from_user.id, message.message_id)

    purchases = await request.get_info_qr(f"user_data/{message.photo[-1].file_id}.jpg")
    os.remove(f"user_data/{message.photo[-1].file_id}.jpg")
    # Выведем результат
    for purchase in purchases:
        product_name = purchase['Название продукта']

        while not product_name[0].isalpha():
            product_name = product_name[1:]

        await add_new_purchase_from_qr(message.chat.id, purchase['Название продукта'], purchase['Количество'], purchase['Стоимость единицы'])


# Обработчик, который реагирует на присланное текстовое сообщение
@dp.message(F.text)
async def some_message(message: types.Message):
    ms = message.text.replace(',', '.')

    await bot.delete_message(message.chat.id, message.message_id)
    if ms == "ОТЧЕТ":
        # await bot.send_photo(message.chat.id,
                       #photo=types.FSInputFile(await navigation.create_photo(message.chat.id, datetime.now())),
                       #caption="💰<b>Ваш отчёт по расходам</b>💰", parse_mode='HTML',
                       #reply_markup=await navigation.get_keyboard(datetime.now()))
        await bot.send_message(message.chat.id, "💰<b>Ваш отчёт по расходам</b>💰", parse_mode='HTML')
        await send_photo_split_if_needed(
            message.chat.id,
            await navigation.create_photo(message.chat.id, datetime.now()),
            bot,
            navigation,
            datetime.now()
        )

    else:
        await check_command_syntax(ms.lower(), message.chat.id) # вносим данные в базу данных


# Обработчик, который реагирует на выбор категории. Заносит новые данные в таблицу.
@dp.callback_query(lambda query: F.data.startswith('add_bd_') and not query.data.startswith('next_data_') and not query.data.startswith('last_data') and not query.data.startswith('clear_') and not query.data.startswith('update_') and not query.data.startswith('show_charts'))
async def process_callback_data(query: types.CallbackQuery):
    # Разбиение строки с данными обратного вызова
    callback_data_parts = query.data.split('_')
    id_category = callback_data_parts[-1]
    text = query.message.text.split(' ')
    name = ' '.join(text[3:-4])
    count = text[-3]
    cost = text[-1]

    # Удаляем выведенную таблицу с категориями
    await bot.delete_message(query.message.chat.id, query.message.message_id)

    # Здесь нужно будет занести данные в базу данных!
    await data_base.add_new_purchase_to_database(query.message.chat.id,id_category,name,count,cost)


# Обработчик для получения отчёта next
@dp.callback_query(lambda query: F.data.startswith('next_data_') and not query.data.startswith('add_bd_') and not query.data.startswith('last_data') and not query.data.startswith('clear_') and not query.data.startswith('update_') and not query.data.startswith('show_charts'))
async def next_data(query: types.CallbackQuery):
    # Разбиение строки с данными обратного вызова
    callback_data_parts = query.data.split('_')
    month = int(callback_data_parts[-1]) + 1
    if month == 13:
        month = 1
    date = datetime.now().replace(day=1, month=int(month))
    await bot.send_message(query.message.chat.id, "💰<b>Ваш отчёт по расходам</b>💰", parse_mode='HTML')
    await send_photo_split_if_needed(
        query.message.chat.id,
        await navigation.create_photo(query.message.chat.id, date),
        bot,
        navigation,
        date
    )

    # await bot.send_photo(query.message.chat.id, photo=types.FSInputFile(await navigation.create_photo(query.message.chat.id, date)), caption="💰<b>Ваш отчёт по расходам</b>💰", parse_mode='HTML', reply_markup=await navigation.get_keyboard(date))
    # await bot.delete_message(query.message.chat.id, query.message.message_id)


# Обработчик для получения отчёта last
@dp.callback_query(lambda query: F.data.startswith('last_data_') and not query.data.startswith('add_bd_') and not query.data.startswith('next_data_') and not query.data.startswith('clear_') and not query.data.startswith('update_') and not query.data.startswith('show_charts'))
async def last_data(query: types.CallbackQuery):
    # Разбиение строки с данными обратного вызова
    callback_data_parts = query.data.split('_')
    month = int(callback_data_parts[-1]) - 1
    if month == 0:
        month = 12
    date = datetime.now().replace(day=1, month=int(month))
    await bot.send_message(query.message.chat.id, "💰<b>Ваш отчёт по расходам</b>💰", parse_mode='HTML')
    await send_photo_split_if_needed(
        query.message.chat.id,
        await navigation.create_photo(query.message.chat.id, date),
        bot,
        navigation,
        date
    )

    # await bot.send_photo(query.message.chat.id, photo=types.FSInputFile(await navigation.create_photo(query.message.chat.id, date)), caption="💰<b>Ваш отчёт по расходам</b>💰", parse_mode='HTML', reply_markup=await navigation.get_keyboard(date))
    # await bot.delete_message(query.message.chat.id, query.message.message_id)


# Обработчик для получения отчёта clear
@dp.callback_query(lambda query: F.data.startswith('clear_') and not query.data.startswith('add_bd_') and not query.data.startswith('next_data_') and not query.data.startswith('last_data') and not query.data.startswith('update_') and not query.data.startswith('show_charts'))
async def clear(query: types.CallbackQuery):
    # Разбиение строки с данными обратного вызова
    callback_data_parts = query.data.split('_')
    month = int(callback_data_parts[-1])
    date = datetime.now().replace(day=1, month=int(month))

    await data_base.delete_current_month_purchases(query.message.chat.id, month, datetime.now().year)
    await bot.delete_message(query.message.chat.id, query.message.message_id)
    await bot.send_photo(query.message.chat.id, photo=types.FSInputFile(await navigation.create_photo(query.message.chat.id, date)), caption="💰<b>Ваш отчёт по расходам</b>💰", parse_mode='HTML', reply_markup=await navigation.get_keyboard(date))


# ГЕНЕРАЦИЯ ГРАФИКОВ
@dp.callback_query(F.data.startswith('show_charts'))
async def process_callback_show_charts(query: types.CallbackQuery):
    user_id = query.from_user.id

    callback_data_parts = query.data.split('_')
    month = int(callback_data_parts[-1])

    path_to_img = f'users/{user_id}/'

    # Получаем данные о затратах по категориям за выбранный месяц
    df_category = await data_base.get_category_expenses_for_month(user_id, month)

    # Построение и сохранение графика затрат по категориям
    await charts.plot_category_expenses(df_category, 'Затраты по категориям за выбранный месяц', path_to_img + 'category_expenses.png')
    await bot.send_photo(query.message.chat.id, photo=types.FSInputFile(path_to_img + 'category_expenses.png'))


# Запуск процесса поллинга новых апдейтов
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
