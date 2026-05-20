from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import random
import string
import sqlite3

app = FastAPI()

# Инициализация базы данных
def init_db():
    conn = sqlite3.connect("urls.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS urls (
            short_code TEXT PRIMARY KEY,
            long_url TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

init_db()

class ShortenRequest(BaseModel):
    url: str

def generate_short_code(length=6):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

@app.post("/shorten")
def shorten_url(request: ShortenRequest):
    conn = sqlite3.connect("urls.db")
    cursor = conn.cursor()
    
    # Проверяем, есть ли уже такая ссылка
    cursor.execute("SELECT short_code FROM urls WHERE long_url = ?", (request.url,))
    existing = cursor.fetchone()
    
    if existing:
        conn.close()
        return {"short_url": f"http://localhost:8000/{existing[0]}"}
    
    # Создаём новый короткий код
    short_code = generate_short_code()
    cursor.execute("INSERT INTO urls (short_code, long_url) VALUES (?, ?)", (short_code, request.url))
    conn.commit()
    conn.close()
    
    return {"short_url": f"http://localhost:8000/{short_code}"}

@app.get("/{short_code}")
def redirect_to_url(short_code: str):
    conn = sqlite3.connect("urls.db")
    cursor = conn.cursor()
    cursor.execute("SELECT long_url FROM urls WHERE short_code = ?", (short_code,))
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        raise HTTPException(status_code=404, detail="Short URL not found")
    
    return {"redirect_to": result[0]}

@app.get("/")
def root():
    return {"message": "URL Shortener is running"}