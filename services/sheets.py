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


def update_pharmacy_result(code: str, status: str, comment: str, normalize_text_func):
    sheet = get_sheet()
    rows = sheet.get_all_records()

    saved_row = None

    for i, row in enumerate(rows, start=2):
        row_code = normalize_text_func(str(row.get("КОД", "")))
        if row_code == normalize_text_func(str(code)):
            sheet.update_cell(i, 8, status)
            sheet.update_cell(i, 10, comment)
            saved_row = row
            break

    return saved_row