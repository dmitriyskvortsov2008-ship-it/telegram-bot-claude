import os
for key in ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY', 'all_proxy', 'ALL_PROXY']:
    os.environ.pop(key, None)


from anthropic import Anthropic
import logging
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Сохранение истории разговоров
conversations = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ... (ваш код без изменений)
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    conversations[user_id] = []
    await update.message.reply_text(f"Привет, {user_name}! 👋")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ... (ваш код без изменений)
    user_id = update.effective_user.id
    if user_id not in conversations:
        conversations[user_id] = []
    conversations[user_id].append({"role": "user", "content": update.message.text})
    await update.message.chat.send_action("typing")

    # Клиент передаём через context или глобально — но создаём его только после проверки ключа
    client = context.bot.data["anthropic_client"]

    try:
        response = client.messages.create(
            model="claude-3-5-sonnet",  # используем стабильную версию
            max_tokens=1024,
            messages=conversations[user_id]
        )
        assistant_message = response.content.text
        conversations[user_id].append({"role": "assistant", "content": assistant_message})

        if len(assistant_message) > 4096:
            for i in range(0, len(assistant_message), 4096):
                await update.message.reply_text(assistant_message[i:i+4096])
        else:
            await update.message.reply_text(assistant_message)
    except Exception as e:
        await update.message.reply_text(f"❌ Произошла ошибка:\n{str(e)}")

async def clear_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conversations[user_id] = []
    await update.message.reply_text("✅ История разговора очищена")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📖 /start — начать, /clear — очистить, /help — справка")

def main():
    if not TELEGRAM_TOKEN:
        print("❌ ОШИБКА: Не найден TELEGRAM_TOKEN в файле .env")
        return
    if not ANTHROPIC_API_KEY:
        print("❌ ОШИБКА: Не найден ANTHROPIC_API_KEY в файле .env")
        return

    print("✅ Переменные окружения найдены")

    # Импортируем здесь, чтобы избежать ошибки при отсутствии библиотеки
    from anthropic import Anthropic
    client = Anthropic(api_key=ANTHROPIC_API_KEY)  # ✅ правильно


    app = Application.builder().token(TELEGRAM_TOKEN).build()

    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("clear", clear_history))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Бот активен и готов к работе!")
    app.run_polling()

if __name__ == '__main__':
    main()
