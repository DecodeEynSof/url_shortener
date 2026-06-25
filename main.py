from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from fastapi.responses import RedirectResponse
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
        return {"short_url": f"https://url-shortener-rt9y.onrender.com/{existing[0]}"}
    # Создаём новый короткий код
    short_code = generate_short_code()
    cursor.execute("INSERT INTO urls (short_code, long_url) VALUES (?, ?)", (short_code, request.url))
    conn.commit()
    conn.close()
    return {"short_url": f"https://url-shortener-rt9y.onrender.com/{short_code}"}
@app.get("/{short_code}")
def redirect_to_url(short_code: str):
    conn = sqlite3.connect("urls.db")
    cursor = conn.cursor()
    cursor.execute("SELECT long_url FROM urls WHERE short_code = ?", (short_code,))
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        raise HTTPException(status_code=404, detail="Short URL not found")
    
    return RedirectResponse(url=result[0])

@app.get("/", response_class=HTMLResponse)
def form():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>URL Shortener</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 600px;
                margin: 50px auto;
                padding: 20px;
                background: #f4f4f4;
            }
            .container {
                background: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            input {
                width: 70%;
                padding: 10px;
                font-size: 16px;
                border: 1px solid #ddd;
                border-radius: 5px;
            }
            button {
                padding: 10px 20px;
                font-size: 16px;
                background: #007bff;
                color: white;
                border: none;
                border-radius: 5px;
                cursor: pointer;
            }
            button:hover {
                background: #0056b3;
            }
            .result {
                margin-top: 20px;
                padding: 10px;
                background: #e9ecef;
                border-radius: 5px;
                display: none;
            }
            .result a {
                color: #007bff;
                text-decoration: none;
            }
            .error {
                color: red;
                margin-top: 10px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔗 URL Shortener</h1>
            <input type="url" id="longUrl" placeholder="Вставьте длинную ссылку..." style="width: 100%; margin-bottom: 10px;">
            <button onclick="shorten()">Сократить</button>
            <div class="result" id="result">
                <strong>Короткая ссылка:</strong><br>
                <a href="#" id="shortUrl" target="_blank"></a><br><br>
                <button onclick="copyToClipboard()">📋 Копировать</button>
            </div>
            <div class="error" id="error"></div>
        </div>

        <script>
            async function shorten() {
                const url = document.getElementById('longUrl').value;
                const resultDiv = document.getElementById('result');
                const errorDiv = document.getElementById('error');
                errorDiv.innerHTML = '';

                if (!url) {
                    errorDiv.innerHTML = 'Введите ссылку';
                    return;
                }

                try {
                    const response = await fetch('/shorten', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({url: url})
                    });

                    if (!response.ok) throw new Error('Ошибка сервера');

                    const data = await response.json();
                    const shortUrl = data.short_url;

                    document.getElementById('shortUrl').href = shortUrl;
                    document.getElementById('shortUrl').textContent = shortUrl;
                    resultDiv.style.display = 'block';
                } catch (err) {
                    errorDiv.innerHTML = 'Не удалось сократить ссылку';
                }
            }

            function copyToClipboard() {
                const shortUrl = document.getElementById('shortUrl').textContent;
                navigator.clipboard.writeText(shortUrl);
                alert('Ссылка скопирована!');
            }
        </script>
    </body>
    </html>
    """
