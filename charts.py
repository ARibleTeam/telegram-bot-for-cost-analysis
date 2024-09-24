# charts.py
import matplotlib.pyplot as plt


async def plot_category_expenses(df, title, filename):
    # Сортировка DataFrame по столбцу 'Дата'
    df_sorted = df.sort_values(by='Дата')

    # Уникальные значения id_категории для оси x
    categories = df_sorted['Название_категории'].unique()

    # Словарь для хранения суммарных затрат по категориям
    category_expenses = {}

    # Вычисляем суммарные затраты по категориям
    for category in categories:
        total_expenses = df_sorted[df_sorted['Название_категории'] == category]['Всего_затрат'].sum()
        category_expenses[category] = total_expenses

    # Создание столбчатой диаграммы
    plt.figure(figsize=(10, 6))
    plt.bar(category_expenses.keys(), category_expenses.values())

    plt.title(title)
    plt.xlabel('Категория')
    plt.ylabel('Всего затрат')
    plt.grid(True)
    plt.savefig(filename)
    plt.close()
