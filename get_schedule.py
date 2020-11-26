# https://api.xn--80aai1dk.xn--p1ai/api/schedule?range=3&subdivision_cod=2&group_name=4562
import json
import typing as tp
import datetime as dt
import urllib.request as urll
# from pprint import pprint as pp
from operator import methodcaller
from urllib.error import URLError
from argparse import ArgumentParser as ap


week_days_rus = [
    "Понедельник",
    "Вторник",
    "Среда",
    "Четверг",
    "Пятница",
    "Суббота",
    "Воскресенье\nя ёбнусь если эти бляди посмеют потрогать моё воскресенье"
]


Pair = tp.Dict[str, tp.Union[str, dt.date, int]]  # Формат в котором возвращаются данные об парах
# для большей информации об работе библиотеке typing прошу посмотреть соответствующую документацию


def get_next_days_after(date: dt.datetime,
                        schedule: tp.Dict[dt.date, Pair],
                        deadline: dict,
                        count: int
                        ):
    if date > dt.datetime.today().replace(**deadline) and date not in schedule:
        key = sorted(list([date_schedule for date_schedule in schedule.keys()
                           if date_schedule - date > dt.timedelta()]))[:count]
    else:
        key = date
    schedule = {key: schedule[key]}
    return schedule


def pretty_print_days(days: tp.Dict[dt.date, Pair]):
    """
    Выводит пары в виде таблицы
    """
    separator_between_subjects = "-" * 10
    separator_between_days = "=" * 10

    for day, lessons in days.items():
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
                date_ = dt.date(date_.year, date_.month, date_.day)
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

    parser = ap(description="Вывод расписания на эту и следующую неделю")
    parser.add_argument("--next_day", "-N",
                        action="store_true",
                        help="показать расписание на следующий день")

    args = parser.parse_args()

    display_only_next_day: bool = args.next_day

    # получаем расписание с сервера:
    schedule = get_schedule_from_server()

    # проверяем что мы всё же получили ответ от сервера:
    if schedule is False:
        return

    schedule = grouping_by_days(schedule)

    if display_only_next_day:

        schedule = get_next_days_after(dt.datetime.now(), schedule.copy(), {"hour": 13, "minute": 55}, 1)

        # now = dt.date.today()
        # TODO: найти способ как можно автоматизировать ну или дать возможность для изменения переменной end_of_last_pair
        # end_of_last_pair = {"hour": 13, "minute": 55}
        # if dt.datetime.now() > dt.datetime.today().replace(**end_of_last_pair)\
           # and now not in schedule:
            # key = sorted(list([date for date in schedule.keys() if date - now > dt.timedelta()]))[0]
        # else:
            # key = now
        # schedule = {key: schedule[key]}

    # сортируем пары по дням и выводим после в виде красивой таблицы:
    pretty_print_days(schedule)


if __name__ == "__main__":
    main()
