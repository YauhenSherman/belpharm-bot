from utils.text import normalize_text


def get_user_name(telegram_id: int, user_map: dict):
    return user_map.get(telegram_id)


def build_pharmacy_card(row: dict) -> str:
    return (
        f"🏥 Карточка аптеки\n\n"
        f"Код: {row.get('КОД', '')}\n"
        f"Район: {row.get('Район', '')}\n"
        f"Адрес: {row.get('Адрес', '')}\n"
        f"Название: {row.get('Название', '')}\n"
        f"Телефон: {row.get('Телефон', '')}\n"
        f"Стенд: {row.get('ЕСТЬ СТЕНД (ГРУППА)', '')}\n"
        f"Ответственный: {row.get('ОТВЕТСТВЕННЫЙ', '')}\n"
        f"Статус: {row.get('Результаты согласования', '')}\n"
        f"Формат: {row.get('Формат стенда (А4 вертикаль.горизонт, А5, А6 наклейка)', '')}"
    )


def find_row_by_code(rows: list[dict], code_text: str):
    normalized = normalize_text(code_text)
    for row in rows:
        row_code = normalize_text(str(row.get("КОД", "")))
        if row_code == normalized:
            return row
    return None