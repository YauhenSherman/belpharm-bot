from telegram import ReplyKeyboardMarkup

def get_main_keyboard():
    keyboard = [
        ["Мои аптеки", "Свободные аптеки"],
        ["По району", "Статистика"],
        ["Меню"],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_free_pharmacy_keyboard():
    return ReplyKeyboardMarkup(
        [["Закрепить за мной"], ["Меню"]],
        resize_keyboard=True,
    )


def get_locked_by_me_keyboard():
    return ReplyKeyboardMarkup(
        [
            ["Согласовано", "Отказ"],
            ["Повторный визит", "Не существует"],
            ["Снять закрепление"],
            ["Меню"],
        ],
        resize_keyboard=True,
    )


def get_readonly_pharmacy_keyboard():
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
