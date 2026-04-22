import os
import json

import gspread
from oauth2client.service_account import ServiceAccountCredentials

from config import SPREADSHEET_NAME


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
    return sheet.get_all_records()


def _find_header(headers: list[str], candidates: list[str], field_name: str) -> str:
    for candidate in candidates:
        if candidate in headers:
            return candidate

    raise ValueError(
        f"Не найден столбец '{field_name}'. "
        f"Ожидаемые варианты: {candidates}. Фактические заголовки: {headers}"
    )


def update_pharmacy_result(
    code: str,
    status: str,
    comment: str,
    normalize_text_func,
    stand_format: str | None = None,
):
    sheet = get_sheet()
    headers = sheet.row_values(1)
    rows = sheet.get_all_records()

    required_headers = {
        "code": _find_header(headers, ["КОД"], "КОД"),
        "status": _find_header(
            headers,
            ["Результаты согласования"],
            "Результаты согласования",
        ),
        "format": _find_header(
            headers,
            [
                "Формат стенда",
                "Формат стенда (А4 вертикаль.горизонт, А5, А6 наклейка)",
            ],
            "Формат стенда",
        ),
        "comment": _find_header(headers, ["Комментарий"], "Комментарий"),
    }

    status_col = headers.index(required_headers["status"]) + 1
    format_col = headers.index(required_headers["format"]) + 1
    comment_col = headers.index(required_headers["comment"]) + 1

    saved_row = None

    for i, row in enumerate(rows, start=2):
        row_code = normalize_text_func(str(row.get(required_headers["code"], "")))

        if row_code == normalize_text_func(str(code)):
            sheet.update_cell(i, status_col, status)
            sheet.update_cell(i, format_col, stand_format or "")
            sheet.update_cell(i, comment_col, comment)

            saved_row = row.copy()
            saved_row[required_headers["status"]] = status
            saved_row[required_headers["format"]] = stand_format or ""
            saved_row[required_headers["comment"]] = comment
            break

    if not saved_row:
        raise ValueError(f"Не найдена строка для кода аптеки: {code}")

    return saved_row
