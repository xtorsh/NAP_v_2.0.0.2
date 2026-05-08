import pandas as pd
import requests
import json
import locale
from pathlib import Path

locale.setlocale(locale.LC_ALL, "")

# Указываем имя каталога
directory_path = Path('C:/Users/HG/Logistics')
# Создаем каталог
try:
    directory_path.mkdir()
    print(f"Directory '{directory_path}' created successfully.")
except FileExistsError:
    print(f"Directory '{directory_path}' already exists.")
except PermissionError:
    print(f"Permission denied: Unable to create '{directory_path}'.")
except Exception as e:
    print(f"An error occurred: {e}")

# Функция для преобразования времени "чч:мм" в минуты
def time_to_minutes(t):
    hours, minutes = map(int, t.split(':'))
    return hours * 60 + minutes

date_range = pd.date_range(start='2026-04-27', end='2026-05-03')
for date in date_range:
    date_print = date.strftime("%d %B %Y (%A)")
    print(date_print)
    # Создаем встроенный каталог с датой
    # Specify the nested directory structure
    date_directory_path = Path(f'{directory_path}/{date_print}')
    # Create nested directories
    date_directory_path.mkdir(parents=True, exist_ok=True)
    print(f"Nested directories '{date_directory_path}' created successfully.")

    # Создаем переменную для накопления данных вывода и вносим в нее дату
    result = f"{date_print}\n\n"
    # Создаем переменную для накопления данных вывода без описания и вносим в нее дату
    result_short = f"{date_print}\n\n"

    # Открываем файл JSON с пользователями
    with open('C:/Users/HG/TempFiles/new_logisticians.json', 'r', encoding='utf-8') as file:
        data_users = json.load(file)

    # Формируем и запускаем цикл перебора пользователей
    for data_user in data_users:
        name = data_user.get("name")
        ids = data_user.get("userId")

        # Создаем встроенный каталог с названием филиала
        # Указываем структуру вложенных каталогов
        nested_directory_path = Path(f'{date_directory_path}/{name}')
        # Создание вложенных каталогов
        nested_directory_path.mkdir(parents=True, exist_ok=True)
        print(f"Nested directories '{nested_directory_path}' created successfully.")
        # Выполняем Get-запрос распределенных заказов с авторизацией на сервере
        url = f"https://nav.by/lumen/integration/routed-points?date={date}&expIds={ids}"
        path = Path(f"{nested_directory_path}/routed-points.json")
        payload = {}
        headers = {
            'Authorization': 'Bearer fc65573f-dac7-45d7-8f72-35f3c2f5efdc'
        }
        response = requests.request("GET", url, headers=headers, data=payload)
        # Сохраняем ответ в файл
        path.write_text(response.text, encoding='utf-8')
        # Откройте файл JSON
        with open(f'{path}', 'r', encoding='utf-8') as file:
            data = json.load(file)

        # Структура такая:
        # data = {"root": {"data": [ ... ] } }

        # Получаем список точек
        points = data['root']['data']
        # Собираем уникальные routeId
        route_ids = set(point['routeId'] for point in points)
        # Создаем список точек без гаражей
        no_garage_points = []

        for point in points:
            prevName = point.get("prevName")
            timeToNext = point.get("timeToNext")
            status = point.get("status")
            if not ((prevName == "" or timeToNext == "00:00") and status == -1):
                no_garage_points.append(point)

        # Сохраняем результат в файл
        with open(f'{nested_directory_path}/no_garage_points.json', 'w', encoding='utf-8') as f:
            json.dump(no_garage_points, f, ensure_ascii=False, indent=4)

        # Создаем список торговых точек
        shop_points = []

        for point in points:
            status = point.get("status")
            if status != -1:
                shop_points.append(point)

        # Сохраняем результат в файл
        with open(f'{nested_directory_path}/shop_points.json', 'w', encoding='utf-8') as f:
            json.dump(shop_points, f, ensure_ascii=False, indent=4)

        # Создаем список точек с радиусами более 100 метров
        max_radius_points = []

        for point in points:
            radius = point.get("radius")
            if radius != "-":
                if radius > 100:
                    max_radius_points.append(point)

        # Сохраняем результат в файл
        with open(f'{nested_directory_path}/max_radius_points.json', 'w', encoding='utf-8') as f:
            json.dump(max_radius_points, f, ensure_ascii=False, indent=4)

        # Собираем в новый список все точки с радиусами более 100 метров без учета гаражей
        max_reaal_radius_points = [max_radius_point for max_radius_point in max_radius_points if
                                   not ((max_radius_point.get(
                                       "prevName") == "" or max_radius_point.get(
                                       "timeToNext") == "00:00") and max_radius_point.get("status"))]

        # Сохраняем результат в файл
        with open(f'{nested_directory_path}/max_reaal_radius_points.json', 'w', encoding='utf-8') as f:
            json.dump(max_reaal_radius_points, f, ensure_ascii=False, indent=4)

        # Создаем список точек с задержкой > 15 минут
        delayed_points = []

        for shop_point in shop_points:
            real_time_str = shop_point.get("realArrivalTime")
            due_time_str = shop_point.get("dueTime")
            if real_time_str and due_time_str and real_time_str != "-" and due_time_str != "-":
                real_minutes = time_to_minutes(real_time_str)
                due_minutes = time_to_minutes(due_time_str)
                if real_minutes - due_minutes > 15:
                    delayed_points.append(shop_point)

        # Сохраняем результат в файл
        with open(f'{nested_directory_path}/delayed_points.json', 'w', encoding='utf-8') as f:
            json.dump(delayed_points, f, ensure_ascii=False, indent=4)

        # Собираем в новый список все точки с "realArrivalTime" == "-"
        unvisited_points = [point for point in points if
                            point.get("status") != -1 and point.get("realArrivalTime") == "-"]

        # Сохраняем в новый файл
        with open(f'{nested_directory_path}/unvisited_points.json', 'w', encoding='utf-8') as f:
            json.dump(unvisited_points, f, ensure_ascii=False, indent=4)

        # Собираем в новый список все не посещенные точки с "rstatus" != 0
        closed_points = [unvisited_point for unvisited_point in unvisited_points if unvisited_point.get("status") != 0]
        # Сохраняем в новый файл
        with open(f'{nested_directory_path}/closed_points.json', 'w', encoding='utf-8') as f:
            json.dump(closed_points, f, ensure_ascii=False, indent=4)

        # Собираем в новый список все не посещенные точки с "rstatus" = 0
        no_closed_points = [unvisited_point for unvisited_point in unvisited_points if
                            unvisited_point.get("status") == 0]
        # Сохраняем в новый файл
        with open(f'{nested_directory_path}/no_closed_points.json', 'w', encoding='utf-8') as f:
            json.dump(no_closed_points, f, ensure_ascii=False, indent=4)

        # собираем в новый список все объекты с комментарием
        comment_points = [point for point in points if point.get("comment") != ""]
        # Сохраняем в новый файл
        with open(f'{nested_directory_path}/comment_points.json', 'w', encoding='utf-8') as f:
            json.dump(comment_points, f, ensure_ascii=False, indent=4)

        # Собираем в новый список не посещенные точки с комментарием
        comment_unvisited_points = [unvisited_point for unvisited_point in unvisited_points if
                                    unvisited_point.get("comment") != ""]
        # Сохраняем в новый файл
        with open(f'{nested_directory_path}/comment_unvisited_points.json', 'w', encoding='utf-8') as f:
            json.dump(comment_unvisited_points, f, ensure_ascii=False, indent=4)

        # Собираем в новый список не посещенные точки без комментариев
        no_comment_unvisited_points = [unvisited_point for unvisited_point in unvisited_points if
                                       unvisited_point.get("comment") == ""]
        # Сохраняем в новый файл
        with open(f'{nested_directory_path}/no_comment_unvisited_points.json', 'w', encoding='utf-8') as f:
            json.dump(no_comment_unvisited_points, f, ensure_ascii=False, indent=4)
        # Вносим результаты для вывода
        result_local = f"{date_print}\n"
        result += f"{name}\n"
        result_local += f"{name}\n\n"
        result_short += f"{name}\n"
        result += f"Создано маршрутов: {len(route_ids)}\n"
        result_local += f"Создано маршрутов: {len(route_ids)}\n"
        result_short += f"{len(route_ids)}\n"
        # result += f"Введено точек: {len(points)}\n"
        # result += f"Из них, точек без учета гаражей: {len(no_garage_points)}\n"
        # result += f"Из них, торговых: {len(shop_points)}\n"
        result += f"Введено точек: {len(shop_points)}\n"
        result_local += f"Введено точек: {len(shop_points)}\n"
        result_short += f"{len(shop_points)}\n"
        # result += f"Всего точек с радиусом более 100 метров: {len(max_radius_points)}\n"
        # result += f"Из них, с радиусом более 100 метров без учета гаража: {len(max_reaal_radius_points)}\n"
        result += f"Точек с радиусом более 100 метров: {len(max_reaal_radius_points)}\n"
        result_local += f"Точек с радиусом более 100 метров: {len(max_reaal_radius_points)}\n"
        result_short += f"{len(max_reaal_radius_points)}\n"
        # result += f"{len(delayed_points)} торговых точек посещено с задержкой более 15 минут\n"
        result += f"{len(delayed_points)} точек посещено с задержкой более 15 минут\n"
        result_local += f"{len(delayed_points)} точек посещено с задержкой более 15 минут\n"
        result_short += f"{len(delayed_points)}\n"
        result += f"{len(unvisited_points)} точек не посещено\n"
        result_local += f"{len(unvisited_points)} точек не посещено\n"
        result_short += f"{len(unvisited_points)}\n"
        result += f"Из нмх, {len(no_closed_points)} точек не закрыты в ручную\n"
        result_local += f"Из нмх, {len(no_closed_points)} точек не закрыты в ручную\n"
        result_short += f"{len(no_closed_points)}\n"
        result += f"{len(no_comment_unvisited_points)} не посещенных точек не прокомментировано\n"
        result_local += f"{len(no_comment_unvisited_points)} не посещенных точек не прокомментировано\n"
        result_short += f"{len(no_comment_unvisited_points)}\n"
        result += "\n"
        result_local += "\n"
        result_short += "\n"

        # Сохраняем result_local в файл
        path = Path(f"{nested_directory_path}/result_local.txt")
        path.write_text(result_local, encoding='utf-8')

    # Создаем встроенный каталог с названием филиала
    # Создаем структуру вложенных каталогов
    results_directory_path = Path(f'{date_directory_path}/Results')
    # Создание вложенных каталогов
    results_directory_path.mkdir(parents=True, exist_ok=True)
    print(f"Nested directories '{results_directory_path}' created successfully.")
    # Сохраняем result в файл
    path = Path(f"{results_directory_path}/result.txt")
    path.write_text(result, encoding='utf-8')

    # Сохраняем result_short в файл
    path = Path(f"{results_directory_path}/result_short.txt")
    path.write_text(result_short, encoding='utf-8')
