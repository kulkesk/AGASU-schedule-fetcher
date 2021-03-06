# https://api.xn--80aai1dk.xn--p1ai/api/schedule?range=3&subdivision_cod=2&group_name=4562
import json
import typing as tp
import datetime as dt
import urllib.request as urll
# from pprint import pprint as pp
from operator import methodcaller
from urllib.error import URLError


week_days_rus = [
    "Понедельник",
    "Вторник",
    "Среда",
    "Четверг",
    "Пятница",
    "Суббота",
    "Воскресенье\nя ёбнусь если эти бляди посмеют потрогать моё воскресенье"
]


Pair = tp.Dict[str, tp.Union[str, dt.datetime, int]]  # Формат в котором возвращаются данные об парах
# для большей информации об работе библиотеке typing прошу посмотреть соответствующую документацию


def grouping_by_days(schedule: tp.List[Pair]) -> tp.Dict[dt.datetime, Pair]:
    """
    Группирует уроки по дате
    Возвращает данные по шаблону: {dt.datetime: [Pair, ...], ...]
    """
    lessons_grouped_by_days = {}  # {dt.datetime: [lesson1, lesson2, lesson3]}

    # заполняем дни уроками:
    for lesson in schedule:
        lesson_date = lesson.get("date")
        if lesson_date in lessons_grouped_by_days:
            lessons_grouped_by_days[lesson_date].append(lesson)
        else:
            lessons_grouped_by_days.update({lesson_date: [lesson]})
    ####

    # сортируем уроки по парам:
    for day, lessons in lessons_grouped_by_days.items():
        lessons_grouped_by_days[day] = sorted(lessons, key=methodcaller("get", "pair"))
    ####

    return lessons_grouped_by_days


def remove_extra_spaces(text: str) -> str:
    """
    Удаляет лишние пробелы
    Какой-то очень не умный человек решил использовать пробелы в ответе от api для форматинга
    """
    return ' '.join(text.split())


def get_schedule_from_server() -> tp.List[Pair]:
    """
    Получаем данные с сервера АГАСУ и форматируем данные в нужные нам объекты для более лёгкой работы
    """

    url = "https://api.xn--80aai1dk.xn--p1ai/api/schedule?"\
        "range=3&subdivision_cod=2&group_name=4562"

    try:
        response = urll.urlopen(url)
    except URLError:
        return False

    if response.code != 200:
        return False

    response_text = response.read().decode("utf-8")
    schedule = json.loads(response_text)  # list[dict[str, str]]

    for lesson in schedule:
        for key, value in lesson.items():
            if key == "date":
                date_ = dt.datetime.strptime(value, "%d.%m.%y")
                # переводим текст с датой в объект даты, для более удобной работы
                lesson.update({key: date_})
                continue

            elif key == "pair":
                # переводим текст с номером пары в число
                lesson.update({key: int(value)})
                continue

            lesson.update({key: remove_extra_spaces(value)})
    return schedule


def main():
    # получаем расписание с сервера:
    schedule = get_schedule_from_server()

    # проверяем что мы всё же получили ответ от сервера:
    if schedule is False:
        return

    # сортируем пары по дням:
    schedule = grouping_by_days(schedule)

    # выводим информацию на экран терминала:

    #  делаем визуальные сепараторы между днями и парами
    separator_between_subjects = "-" * 10
    separator_between_days = "=" * 10

    for day, lessons in schedule.items():
        print(separator_between_days, f"{week_days_rus[day.weekday()]}", separator_between_days, sep="\n")
        for lesson in lessons:
            subject = lesson.get("subject")
            signature = lesson.get("signature")
            classroom_building, classroom = lesson.get("classroom_building"), lesson.get("classroom")

            print(separator_between_subjects, '\n',
                  subject, '\n',
                  signature, '\n',
                  classroom, classroom_building
                  )
        print()


if __name__ == "__main__":
    main()
