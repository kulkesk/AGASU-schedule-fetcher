# https://api.xn--80aai1dk.xn--p1ai/api/schedule?range=3&subdivision_cod=2&group_name=4562
import json
import typing as tp
import datetime as dt
import urllib.request as urll
import urllib.parse as uparse
# from pprint import pprint as pp
from operator import methodcaller
# from urllib.error import URLError
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


def get_next_days_after(date: dt.date,
                        schedule: tp.Dict[dt.date, tp.List[Pair]],
                        count: int
                        ):
    keys = sorted(list([date_schedule for date_schedule in schedule.keys()
                        if date_schedule - date > dt.timedelta()]))[:count]
    schedule_new = {}
    for key in keys:
        schedule_new.update({key: schedule[key]})
    return schedule_new


def pretty_print_days(days: tp.Dict[dt.date, tp.List[Pair]]):
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


def grouping_by_days(schedule: tp.List[Pair]) -> tp.Dict[dt.datetime, tp.List[Pair]]:
    """
    Группирует уроки по дате
    Возвращает данные по шаблону: {dt.datetime: [Pair, ...], ...]
    """
    lessons_grouped_by_days: tp.Dict[dt.datetime, tp.List[Pair]] = {}  # {dt.datetime: [lesson1, lesson2, lesson3]}

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


def get_data_from_server(options: tp.Tuple[str, tp.Dict[str, int]] =
                         ("schedule", {"range": 3, "subdivision_cod": 2, "group_name": 4562})
                         ):
    """
    Получаем информацию с api сервера
    """
    url = f"https://api.xn--80aai1dk.xn--p1ai/api/{options[0]}?{uparse.urlencode(options[1])}"
    response = urll.urlopen(url)
    response_text = response.read().decode("utf-8")
    return json.loads(response_text) if response_text else response_text


def get_list_of_options(*, get_list_of_subdivisions: bool = False, groups_in_subdivision_under_id: int = None):
    """
    Получение списка доступных опций для запросов к серверу.

    Возвращаются данные в виде словаря с опциями которые можно подать в качестве аргументов к функции
    get_schedule_from_server

    Ключи словаря это имена аргументов для подачи в get_schedule_from_server

    Значения (которые находятся под ключами) являются словарями чьи ключи обозначают смысл данных а значения ключей
    обозначают данные которые надо передавать в функцию get_schedule_from_server
    """

    def reformat(raw):
        done_ones = {}
        for item in raw:
            done_ones[remove_extra_spaces(item["title"])] = item["id"]
        return done_ones

    options = dict(
        range={"Эта неделя": 1, "Следующая неделя": 2, "Эта и следующая недели": 3},
        subdivision_cod={},
        group_name={},
    )

    # получаем список учреждений АГАСУ, Строительный колледж, и т.д.
    if get_list_of_subdivisions:
        options["subdivision_cod"] = reformat(get_data_from_server(("subdivisions", {})))

    # получаем список учебных групп в учереждении id которого мы задали, если мы задали ему значение
    if groups_in_subdivision_under_id is not None:
        options["group_name"] = reformat(
            get_data_from_server(("groups", {"subdivision_cod": groups_in_subdivision_under_id}))
        )

    return options


def get_schedule_from_server(**options) -> tp.Union[tp.List[Pair], bool]:
    """
    Получаем данные с сервера АГАСУ и форматируем данные в нужные нам объекты для более лёгкой работы
    """

    if not options:
        options = {"range": 3, "subdivision_cod": 2, "group_name": 4562}

    schedule = get_data_from_server(("schedule", options))

    for lesson in schedule:
        for key, value in lesson.items():
            if key == "date":
                date_ = dt.datetime.strptime(value, "%d.%m.%y")
                date_ = dt.date.fromtimestamp(date_.timestamp())
                # переводим текст с датой в объект даты, для более удобной работы
                lesson.update({key: date_})
                continue

            elif key == "pair":
                # переводим текст с номером пары в число
                lesson.update({key: int(value)})
                continue

            lesson.update({key: remove_extra_spaces(value)})
    return schedule


def main(display_only_next_day=False):
    # получаем расписание с сервера:
    schedule = get_schedule_from_server()

    # проверяем что мы всё же получили ответ от сервера:
    if schedule is False:
        return

    schedule = grouping_by_days(schedule)

    if display_only_next_day:
        now = dt.datetime.now()
        if now < now.replace(hour=13, minute=55) and dt.date.today() in schedule:
            schedule_new = {dt.date.today(): schedule[dt.date.today()]}
        else:
            schedule_new = get_next_days_after(dt.date.today(), schedule, 1)
        schedule = schedule_new
        del schedule_new

    # сортируем пары по дням и выводим после в виде красивой таблицы:
    pretty_print_days(schedule)


if __name__ == "__main__":
    parser = ap(description="Вывод расписания на эту и следующую неделю")
    parser.add_argument("--next_day", "-N",
                        action="store_true",
                        help="показать расписание на следующий день")
    args = parser.parse_args()

    main(args.next_day)
