from aiogram import types
import random
import base64
import imgkit
import data_base
import os


# Функция для вывода кнопок отчета
async def get_keyboard(date):
    # Получаем год и месяц из переданной даты
    month_names = {
        "January": "Январь",
        "February": "Февраль",
        "March": "Март",
        "April": "Апрель",
        "May": "Май",
        "June": "Июнь",
        "July": "Июль",
        "August": "Август",
        "September": "Сентябрь",
        "October": "Октябрь",
        "November": "Ноябрь",
        "December": "Декабрь"
    }
    month = month_names[date.strftime("%B")]
    buttons = [
        [
            types.InlineKeyboardButton(text="<<", callback_data=f"last_data_{date.strftime("%m")}"),
            types.InlineKeyboardButton(text=month, callback_data="0"),
            types.InlineKeyboardButton(text=">>", callback_data=f"next_data_{date.strftime("%m")}")
        ],
        [types.InlineKeyboardButton(text="Очистить расходы за " + month.lower(), callback_data=f"clear_{date.strftime("%m")}")],
        [types.InlineKeyboardButton(text="Затраты по категориям", callback_data=f'show_charts_{date.strftime("%m")}')],
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


# Функция для выбора категории покупки пользователя вручную
async def keyboard_category():
    buttons = [
        [types.InlineKeyboardButton(text='Продукты питания', callback_data=f'add_bd_1')],
        [types.InlineKeyboardButton(text='Транспорт', callback_data=f'add_bd_2')],
        [types.InlineKeyboardButton(text='Жилье и ЖКХ', callback_data=f'add_bd_3')],
        [types.InlineKeyboardButton(text='Услуги связи', callback_data=f'add_bd_4')],
        [types.InlineKeyboardButton(text='Одежда и обувь', callback_data=f'add_bd_5')],
        [types.InlineKeyboardButton(text='Медицина', callback_data=f'add_bd_6')],
        [types.InlineKeyboardButton(text='Другое', callback_data=f'add_bd_7')],
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


async def create_photo(user_id, date):
    # фиксированный набор названий категорий
    list_category = ["Продукты питания", "Транспорт", "Жилье и ЖКХ", "Услуги связи", "Одежда и обувь", "Медицина", "Другое"]
    # фиксированный набор цветов
    colors = [
        ["CFE9FF", "E5F3FF", "F1F8FF"],
        ["FFD1CE", "FFE5E5", "FFF0F0"],
        ["CEFFD3", "E5FFE7", "F3FFF4"],
        ["FFF4CE", "FFF6E5", "FFFDF3"],
        ["C8E9EA", "DCF2F4", "E9F4F4"],
        ["EFD5FF", "FBE5FF", "FEF0FF"],
        ["EDFFC5", "F4FFDD", "F7FFE7"]
    ]
    data = await data_base.get_user_purchases_by_date(user_id, date)

    txt_path = f'user_img/{user_id}.txt'
    img_path = f'user_img/{user_id}.png'

    if os.path.exists(txt_path):
        with open(txt_path, 'r', encoding='utf-8') as f:
            if f.read() == str(data):
                return img_path  # Данные совпадают, возвращаем путь к изображению

    total_amount = sum(category['Всего затрат в этой категории'] for category in data)
    total_amount = int(total_amount)
    if total_amount <= 0:
        return 'user_img/zero.png'
    head = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Потрачено</title>
    <style>
        .container {
            width: 1080px;
            position: relative;
            padding: 70px 0 0 0px;
            margin-top: 112px;
        }

        .title {
            color: black;
            font-size: 42px;
            font-family: Unbounded;
            font-weight: 400;
            word-wrap: break-word;
            position: absolute;
            top: 10px;
        }

        .amount {
            padding: 10px 25px;
            background: #C4FFED;
            border-radius: 10px;
            border: 1px #5EFFCE solid;
            font-family: Unbounded;
            font-size: 42px;
            justify-content: center;
            align-items: center;
            position: absolute;
            right: 0;
            top: 0;
            margin-right: 30px;
        }

        .category {
            position: relative; /* Изменяем на relative */
            border-radius: 10px;
            border: 1px #CEE9FF solid;
            padding: 20px;
            margin-left: 60px;
            margin-top: 60px; /* Добавляем отступ между категориями */
        }


        .category-title {
            color: black;
            font-size: 24px;
            font-family: Unbounded;
            font-weight: 400;
            word-wrap: break-word;
            margin-top: 4px;
            display: inline-block; /* Добавляем, чтобы можно было сделать элементы в одну строку */
        }

        .item-wrapper {
            border-radius: 10px;
            margin-bottom: 10px;
            padding: 5px;
        }

        .item {
            color: black;
            font-size: 20px;
            font-family: Manrope;
            font-weight: 400;
            word-wrap: break-word;
            display: inline-block;
        }

        .quantity {
            color: black;
            font-size: 20px;
            font-family: Manrope;
            font-weight: 400;
            word-wrap: break-word;
            display: inline-block;
            position: absolute;
            right: 0px;
            margin-right: 95px;
        }

        .total {
            padding: 5px 10px;
            border-radius: 10px;
            overflow: hidden;
            display: inline-block; /* Добавляем, чтобы элементы были в одной строке */
            color: black;
            font-size: 24px;

            font-family: Unbounded;
            font-weight: 400;
            word-wrap: break-word;
            position: absolute;
            right: 0px; /* Выравниваем с правым краем категории */
            margin-right: 70px;
        }
    </style>
</head>
"""
    with open("img_html/bag.png", "rb") as image_file:
        base64_encoded_image_1 = base64.b64encode(image_file.read()).decode('utf-8')
    with open("img_html/phone.png", "rb") as image_file:
        base64_encoded_image_2 = base64.b64encode(image_file.read()).decode('utf-8')
    with open("img_html/car.png", "rb") as image_file:
        base64_encoded_image_3 = base64.b64encode(image_file.read()).decode('utf-8')
    with open("img_html/persent.png", "rb") as image_file:
        base64_encoded_image_4 = base64.b64encode(image_file.read()).decode('utf-8')
    body = f"""
<body>
      <img style="width: 155.19px; height: 136.97px; left: -20px; top: 10px; position: absolute; transform: rotate(-54.60deg); transform-origin: 0 0" src="data:image/png;base64,{base64_encoded_image_1}" />
    <div class="container">
        <div style="margin-bottom: 21px;">
            <div class="title" style="left: 32px;">Всего потратили</div>
            <div class="amount">{total_amount} ₽</div>
        </div>
            <div>
"""
    available_colors = colors[:] # копии массива цветов
    for category in reversed(data):
        color_group = random.choice(available_colors)
        available_colors.remove(color_group)
        body += f"""
                <div class="category" style="background: #{color_group[1]};">
                    <div style="margin-bottom: 21px;">
                        <div class="category-title">{list_category[int(category['Категория'])-1]}</div>
                        <div class="total" style="background: #{color_group[0]};">{int(category['Всего затрат в этой категории'])} ₽</div>
                    </div>
        """
        for product in category['Продукты']:
            body += f"""
                    <div class="item-wrapper" style="background: #{color_group[2]};">
                        <div class="item">{product['Продукт'][:45]}</div>
                        <div class="quantity">{int(product['Количество покупок'])} шт ({int(product['Стоимость за единицу'])} ₽) - {int(product['Всего затрат'])} ₽</div>
                    </div>
            """
        body += """
                </div>
        """

    body += f"""
            </div>
        </div>
    </div>
    <img style="width: 104.146px; height: 194.896px; position: absolute; -webkit-transform: rotate(16deg); margin-left:1000px" src="data:image/png;base64,{base64_encoded_image_2}" />
    <img style="width: 177.25px; height: 151.25px; left: 2px; position: absolute" src="data:image/png;base64,{base64_encoded_image_3}" />
    <img style="width: 312px; height: 291px; left: 920px; top: 135px; position: absolute" src="data:image/png;base64,{base64_encoded_image_4}" />
</body>
</html>
    """
    # Путь к исполняемому файлу wkhtmltoimage
    config = imgkit.config(wkhtmltoimage='C:/Program Files/wkhtmltopdf/bin/wkhtmltoimage.exe')

    # параметры генерации изображения
    options = {
        '--quality': '100',
        'crop-w': '1130',
    }
    # путь для сохранения изображения
    path_to_img = f'user_img/{user_id}.png'
    # Конвертирование HTML в изображение
    imgkit.from_string(head+body, path_to_img, config=config, options=options)

    # Создаём или перезаписываем .txt файл с актуальными данными
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write(str(data))

    return path_to_img