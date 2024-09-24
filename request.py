import requests
import json
async def get_info_qr(file):
    url = 'https://proverkacheka.com/api/v1/check/get'

    # токен + файл
    data={'token':'YOUR_TOKEN'}
    files = {'qrfile': open(file, 'rb')}
    r = requests.post(url, data=data, files=files)
    r = r.text

    if len(r) > 40:
        # Открытие JSON
        data = json.loads(r)["data"]["json"]
        # Получим информацию о покупках
        items = data.get('items', [])

        # Создадим массив данных для каждой покупки
        purchases = []

        for item in items:
            purchase = {
                'Название продукта': item.get('name', ''),
                'Стоимость единицы': item.get('price', 0) / 100,
                'Количество': item.get('quantity', 0),
                'Общие затраты': item.get('sum', 0) / 100,
                'Дата операции': data.get('dateTime', '').split('T')[0]
            }
            purchases.append(purchase)

        return purchases
        # Выведем результат
        #for purchase in purchases:
        #    print("Название продукта:", purchase['Название продукта'])
        #    print("Стоимость единицы:", purchase['Стоимость единицы'])
        #    print("Количество:", purchase['Количество'])
        #    print("Общие затраты:", purchase['Общие затраты'])
        #    print("Дата операции:", purchase['Дата операции'])
        #    print()
    return "None"
