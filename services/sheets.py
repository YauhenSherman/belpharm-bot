import os
import json
from datetime import datetime

import gspread
from oauth2client.service_account import ServiceAccountCredentials

from config import SPREADSHEET_NAME
from services.pharmacy import enrich_pharmacy_rows, build_pharmacy_uid, normalize_text


RESPONSIBLE_HEADERS = [
    "ОТВЕТСТВЕННЫЙ",
    "Ответственный/СЛУЖИТЕЛЬ",
    "Ответственный",
    "СЛУЖИТЕЛЬ",
]

STATUS_HEADERS = [
    "Результаты согласования",
    "Статус",
]

FORMAT_HEADERS = [
    "Формат стенда",
    "Формат стенда (А4 вертикаль.горизонт, А5, А6 наклейка)",
]

DATE_HEADERS = [
    "Дата",
    "Дата обновления",
    "Дата согласования",
]


def get_sheet():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]

    credentials_json = os.getenv("GOOGLE_CREDENTIALS_JSON")
    if not credentials_json:
        raise ValueError("GOOGLE_CREDENTIALS_JSON не найден в переменных окружения")

    creds_dict = json.loads(credentials_json)

    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        creds_dict,
        scope,
    )

    client = gspread.authorize(creds)
    return client.open(SPREADSHEET_NAME).sheet1


def get_rows():
    sheet = get_sheet()
    return enrich_pharmacy_rows(sheet.get_all_records())


def _is_blank(value) -> bool:
    return value is None or str(value).strip() == ""


def _safe_get(mapping: dict, key: str, default: str = ""):
    if not isinstance(mapping, dict):
        return default
    value = mapping.get(key, default)
    return default if value is None else value


def _safe_get_list(items: list, index: int, default=""):
    if index < 0 or index >= len(items):
        return default
    value = items[index]
    return default if value is None else value


def _find_header(headers: list[str], candidates: list[str], field_name: str) -> str:
    for candidate in candidates:
        if candidate in headers:
            return candidate
    raise ValueError(
        f"Не найден столбец '{field_name}'. "
        f"Ожидаемые варианты: {candidates}. Фактические заголовки: {headers}"
    )


def _find_optional_header(headers: list[str], candidates: list[str]) -> str | None:
    for candidate in candidates:
        if candidate in headers:
            return candidate
    return None


def _resolve_headers(headers: list[str]) -> dict:
    return {
        "responsible": _find_header(headers, RESPONSIBLE_HEADERS, "Ответственный"),
        "status": _find_header(headers, STATUS_HEADERS, "Статус"),
        "format": _find_header(headers, FORMAT_HEADERS, "Формат стенда"),
        "date": _find_optional_header(headers, DATE_HEADERS),
        "comment": _find_optional_header(headers, ["Комментарий"]),
    }


def _update_row_by_uid(uid: str, values: dict[str, str], clear_format: bool = False):
    sheet = get_sheet()
    headers = sheet.row_values(1)
    resolved = _resolve_headers(headers)
    rows = enrich_pharmacy_rows(sheet.get_all_records())

    row_index = None
    row_data = None
    for index, row in enumerate(rows, start=2):
        row_uid = build_pharmacy_uid(row)
        if row_uid == normalize_text(str(uid)):
            row_index = index
            row_data = row
            break

    if row_index is None or row_data is None:
        raise ValueError(f"Не найдена строка для UID аптеки: {uid}")

    for header, value in values.items():
        col = headers.index(header) + 1
        sheet.update_cell(row_index, col, value)
        row_data[header] = value

    if clear_format:
        format_header = resolved["format"]
        col = headers.index(format_header) + 1
        sheet.update_cell(row_index, col, "")
        row_data[format_header] = ""

    return row_data


def assign_pharmacy(uid: str, responsible_name: str):
    sheet = get_sheet()
    headers = sheet.row_values(1)
    resolved = _resolve_headers(headers)
    values = {
        resolved["responsible"]: responsible_name,
        resolved["status"]: "Закреплена",
    }
    return _update_row_by_uid(uid, values=values, clear_format=False)


def unassign_pharmacy(uid: str):
    sheet = get_sheet()
    headers = sheet.row_values(1)
    resolved = _resolve_headers(headers)
    values = {
        resolved["responsible"]: "",
        resolved["status"]: "",
    }
    return _update_row_by_uid(uid, values=values, clear_format=True)


def finalize_pharmacy(uid: str, status: str, stand_format: str | None = None):
    sheet = get_sheet()
    headers = sheet.row_values(1)
    resolved = _resolve_headers(headers)
    date_value = datetime.utcnow().strftime("%Y-%m-%d")

    values = {
        resolved["status"]: status,
    }

    if status == "Согласовано":
        values[resolved["format"]] = stand_format or ""
    else:
        values[resolved["format"]] = ""

    if resolved["date"]:
        values[resolved["date"]] = date_value

    if resolved["comment"]:
        values[resolved["comment"]] = _safe_get(values, resolved["comment"], "")

    return _update_row_by_uid(uid, values=values, clear_format=False)
