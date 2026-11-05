import uvicorn

if __name__ == "__main__":
    print("🚀 Запускаем (API + Telegram Бот)...")
    uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=True)