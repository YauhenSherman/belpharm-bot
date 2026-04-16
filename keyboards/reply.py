from telegram import ReplyKeyboardMarkup


def get_main_keyboard():
    keyboard = [
        ["Мои аптеки", "Свободные аптеки"],
        ["По району", "Статистика"],
        ["Меню"],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_status_keyboard():
    keyboard = [
        ["Согласовано", "Отказ"],
        ["Повторный визит", "Не существует"],
        ["Обслуживается"],
        ["Меню"],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def build_codes_keyboard(codes: list[str]):
    keyboard = []
    row = []

    for code in codes[:20]:
        row.append(code)
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