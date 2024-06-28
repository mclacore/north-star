import os
import pyodbc
import struct
from azure import identity

from typing import Union
from fastapi import FastAPI
from pydantic import BaseModel

from dotenv import load_dotenv

load_dotenv()

class AutoPay(BaseModel):
    auto_pay_name: str
    auto_pay_amount: int
    auto_pay_draft_date: str
    
connection_string = os.environ["AZURE_SQL_CONNECTIONSTRING"]

app = FastAPI()

@app.get("/")
def root():
    print("Root of AutoPay API")
    try:
        conn = get_conn()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE AutoPay (
                ID int NOT NULL PRIMARY KEY IDENTITY,
                AutoPayName varchar(255),
                AutoPayAmount money,
                AutoPayDraftDate date
            );
        """)

        conn.commit()
    except Exception as e:
        print(e)
    return "AutoPay API"

@app.get("/all")
def get_autopays():
    rows = []
    with get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM AutoPay")

        for row in cursor.fetchall():
            print(row.AutoPayName, row.AutoPayAmount, row.AutoPayDraftDate)
            rows.append(f"{row.ID}, { row.AutoPayName }, { row.AutoPayAmount }, { row.AutoPayDraftDate }")
    return rows

@app.get("/autopay/{auto_pay_id}")
def get_autopay(auto_pay_id: int):
    with get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM AutoPay WHERE ID = ?", auto_pay_id)

        row = cursor.fetchone()
        return f"{row.ID}, { row.AutoPayName }, { row.AutoPayAmount }, { row.AutoPayDraftDate }"

@app.post("/autopay")
def create_autopay(item: AutoPay):
    with get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute(f"INSERT INTO AutoPay (AutoPayName, AutoPayAmount, AutoPayDraftDate) VALUES (?, ?)", item.auto_pay_name, item.auto_pay_amount, item.auto_pay_draft_date)
        conn.commit()

    return item

def get_conn():
    credential = identity.DefaultAzureCredential(exclude_interactive_browser_credential=False)
    token_bytes = credential.get_token("https://database.windows.net/.default").token.encode("UTF-16-LE")
    token_struct = struct.pack(f'<I{len(token_bytes)}s', len(token_bytes), token_bytes)
    SQL_COPT_SS_ACCESS_TOKEN = 1256  # This connection option is defined by microsoft in msodbcsql.h
    conn = pyodbc.connect(connection_string, attrs_before={SQL_COPT_SS_ACCESS_TOKEN: token_struct})
    return conn
