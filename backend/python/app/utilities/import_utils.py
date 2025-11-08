import io

import pandas as pd
from fastapi import UploadFile

MAX_CSV_ROWS = 250
CSV_FILE_TYPES = ["text/csv", "application/csv"]
XLSX_FILE_TYPES = [
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-excel",
]


async def get_df(file: UploadFile) -> pd.DataFrame:
    file_data = await file.read()

    df = pd.DataFrame()
    filename = str(file.filename)
    if filename.endswith(".csv"):
        df = pd.read_csv(io.BytesIO(file_data))
    elif filename.endswith((".xlsx", ".xls")):
        df = pd.read_excel(io.BytesIO(file_data))
    else:
        raise ValueError("Unsupported file type")
    return df
