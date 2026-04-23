from telegram import ReplyKeyboardMarkup

from services.pharmacy import FREE_STATE, LOCKED_STATE

FINAL_STATUSES = [
    "Согласовано",
    "Отказ",
    "Повторный визит",
    "Не существует",
]


def get_main_keyboard():
    keyboard = [
        ["Мои аптеки", "Свободные аптеки"],
        ["По району", "Статистика"],
        ["Меню"],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_status_keyboard():
    return get_final_status_keyboard()


def get_final_status_keyboard():
    keyboard = [
        ["Согласовано", "Отказ"],
        ["Повторный визит", "Не существует"],
        ["Меню"],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_pharmacy_actions_keyboard(pharmacy_state: str, is_owner: bool):
    if pharmacy_state == FREE_STATE:
        return ReplyKeyboardMarkup(
            [["Закрепить за мной"], ["Меню"]],
            resize_keyboard=True,
        )

    if pharmacy_state == LOCKED_STATE and is_owner:
        return ReplyKeyboardMarkup(
            [
                ["Согласовано", "Отказ"],
                ["Повторный визит", "Не существует"],
                ["Снять закрепление"],
                ["Меню"],
            ],
            resize_keyboard=True,
        )

    return ReplyKeyboardMarkup([["Меню"]], resize_keyboard=True)


def build_codes_keyboard(items: list[str]):
    keyboard = []
    row = []

    for item in items[:20]:
        row.append(item)
        if len(row) == 2:
            keyboard.append(row)
            row = []

    if row:
        keyboard.append(row)

    keyboard.append(["Меню"])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def build_districts_keyboard(districts: list[str]):
    keyboard = []
    row = []

    for district in districts:
        row.append(district)
        if len(row) == 2:
            keyboard.append(row)
            row = []

    if row:
        keyboard.append(row)

    keyboard.append(["Меню"])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_stand_format_keyboard():
    keyboard = [
        ["А4 вертикаль", "А4 горизонт"],
        ["А5", "А6 наклейка"],
        ["Отмена"],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
