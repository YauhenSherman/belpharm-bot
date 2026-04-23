from utils.text import normalize_text as _normalize_text

FREE_STATE = "free"
LOCKED_STATE = "locked"
DONE_STATE = "done"
OTHER_STATE = "other"

LOCKED_STATUS = "Закреплена"
FINAL_STATUSES = ["Согласовано", "Отказ", "Повторный визит", "Не существует"]

RESPONSIBLE_KEYS = [
    "ОТВЕТСТВЕННЫЙ",
    "Ответственный/СЛУЖИТЕЛЬ",
    "Ответственный",
    "СЛУЖИТЕЛЬ",
]

STATUS_KEYS = [
    "Результаты согласования",
    "Статус",
]


def normalize_text(text: str) -> str:
    return _normalize_text(text)


def get_user_name(telegram_id: int, user_map: dict):
    return user_map.get(telegram_id)


def build_pharmacy_uid(row: dict) -> str:
    code = normalize_text(str(row.get("КОД", "")))
    address = normalize_text(str(row.get("Адрес", "")))
    return f"{code}|{address}"


def build_pharmacy_label(row: dict) -> str:
    code = normalize_text(str(row.get("КОД", "")))
    address = normalize_text(str(row.get("Адрес", "")))
    return f"{code} — {address}"


def enrich_pharmacy_row(row: dict) -> dict:
    enriched = row.copy()
    enriched["UID"] = build_pharmacy_uid(row)
    enriched["LABEL"] = build_pharmacy_label(row)
    return enriched


def enrich_pharmacy_rows(rows: list[dict]) -> list[dict]:
    return [enrich_pharmacy_row(row) for row in rows]


def get_row_value(row: dict, keys: list[str]) -> str:
    for key in keys:
        value = str(row.get(key, "") or "").strip()
        if value:
            return value
    return ""


def normalize_user_name(value: str) -> str:
    return (
        str(value or "")
        .strip()
        .lower()
        .replace("ё", "е")
        .replace(".", "")
        .replace("  ", " ")
    )


def get_row_responsible(row: dict) -> str:
    return get_row_value(row, RESPONSIBLE_KEYS)


def get_row_status(row: dict) -> str:
    return get_row_value(row, STATUS_KEYS)


def get_pharmacy_state(row: dict) -> str:
    responsible = get_row_responsible(row)
    status = get_row_status(row)

    if not responsible and not status:
        return FREE_STATE
    # Переходный период: есть ответственный, но статус ещё не проставлен.
    if responsible and not status:
        return LOCKED_STATE
    if responsible and status == LOCKED_STATUS:
        return LOCKED_STATE
    if responsible and status in FINAL_STATUSES:
        return DONE_STATE
    return OTHER_STATE


def is_locked_by_user(row: dict, user_name: str) -> bool:
    return (
        get_pharmacy_state(row) == LOCKED_STATE
        and normalize_user_name(get_row_responsible(row)) == normalize_user_name(user_name)
    )


def build_pharmacy_card(row: dict) -> str:
    format_value = row.get("Формат стенда", "")
    if not format_value:
        format_value = row.get("Формат стенда (А4 вертикаль.горизонт, А5, А6 наклейка)", "")

    return (
        f"🏥 Карточка аптеки\n\n"
        f"Код: {row.get('КОД', '')}\n"
        f"Район: {row.get('Район', '')}\n"
        f"Адрес: {row.get('Адрес', '')}\n"
        f"Название: {row.get('Название', '')}\n"
        f"Телефон: {row.get('Телефон', '')}\n"
        f"Стенд: {row.get('ЕСТЬ СТЕНД (ГРУППА)', '')}\n"
        f"Ответственный: {get_row_responsible(row)}\n"
        f"Статус: {get_row_status(row)}\n"
        f"Формат: {format_value}"
    )


def find_row_by_uid(rows: list[dict], uid_text: str):
    normalized = normalize_text(uid_text)
    for row in rows:
        row_uid = normalize_text(str(row.get("UID", "")))
        if row_uid == normalized:
            return row
    return None


def find_row_by_label(rows: list[dict], label_text: str):
    normalized = normalize_text(label_text)
    for row in rows:
        row_label = normalize_text(str(row.get("LABEL", "")))
        if row_label == normalized:
            return row
    return None
