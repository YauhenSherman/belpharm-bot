import gspread
from oauth2client.service_account import ServiceAccountCredentials

from config import SPREADSHEET_NAME, GOOGLE_CREDENTIALS_FILE


def get_sheet():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(
        GOOGLE_CREDENTIALS_FILE,
        scope,
    )
    client = gspread.authorize(creds)
    return client.open(SPREADSHEET_NAME).sheet1


def get_rows():
    sheet = get_sheet()
    return sheet.get_all_records()


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

    code_col = headers.index("КОД") + 1
    status_col = headers.index("Результаты согласования") + 1
    format_col = headers.index("Формат стендов") + 1
    comment_col = headers.index("Комментарий") + 1

    saved_row = None

    for i, row in enumerate(rows, start=2):
        row_code = normalize_text_func(str(row.get("КОД", "")))

        if row_code == normalize_text_func(str(code)):
            sheet.update_cell(i, status_col, status)

            if status == "Согласовано":
                sheet.update_cell(i, format_col, stand_format or "")

            sheet.update_cell(i, comment_col, comment)

            saved_row = row.copy()
            saved_row["Результаты согласования"] = status
            saved_row["Формат стендов"] = stand_format or ""
            saved_row["Комментарий"] = comment
            break

    return saved_row