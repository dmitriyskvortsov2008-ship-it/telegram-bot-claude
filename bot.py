import os

# Удаляем переменные из .env и proxy
os.environ.pop('TELEGRAM_TOKEN', None)
os.environ.pop('ANTHROPIC_API_KEY', None)
for key in ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY', 'all_proxy', 'ALL_PROXY']:
    os.environ.pop(key, None)

import logging
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from anthropic import Anthropic
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Глобальный клиент Anthropic
client = None

# Логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Сохранение истории разговоров
conversations = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    
    conversations[user_id] = []
    
    await update.message.reply_text(
        f"Привет, {user_name}! 👋\n\n"
        f"Я бот на основе Claude AI\n"
        f"Просто напиши мне сообщение 💬"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка текстовых сообщений"""
    global client
    
    user_id = update.effective_user.id
    user_message = update.message.text
    
    # Инициализируем историю если её нет
    if user_id not in conversations:
        conversations[user_id] = []
    
    # Добавляем сообщение пользователя
    conversations[user_id].append({
        "role": "user",
        "content": user_message
    })
    
    # Показываем "печатается..."
    await update.message.chat.send_action("typing")
    
    try:
        # Запрос к Claude
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            messages=conversations[user_id]
        )
        
        assistant_message = response.content[0].text
        
        # Добавляем ответ в историю
        conversations[user_id].append({
            "role": "assistant",
            "content": assistant_message
        })
        
        # Если сообщение слишком длинное, разбиваем на части
        if len(assistant_message) > 4096:
            for i in range(0, len(assistant_message), 4096):
                await update.message.reply_text(assistant_message[i:i+4096])
        else:
            await update.message.reply_text(assistant_message)
        
    except Exception as e:
        await update.message.reply_text(
            f"❌ Произошла ошибка:\n{str(e)}"
        )

async def clear_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /clear для очистки истории"""
    user_id = update.effective_user.id
    conversations[user_id] = []
    await update.message.reply_text("✅ История разговора очищена")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help"""
    await update.message.reply_text(
        "📖 Доступные команды:\n\n"
        "/start - Начать работу\n"
        "/clear - Очистить историю\n"
        "/help - Показать эту справку"
    )

def main():
    """Запуск бота"""
    global client
    
    # Проверка токена
    if not TELEGRAM_TOKEN:
        print("❌ ОШИБКА: Не найден TELEGRAM_TOKEN в файле .env")
        return
    
    if not ANTHROPIC_API_KEY:
        print("❌ ОШИБКА: Не найден ANTHROPIC_API_KEY в файле .env")
        return
    
    print("✅ Переменные окружения найдены")
    
    # Инициализируем Claude клиент
    client = Anthropic(api_key=ANTHROPIC_API_KEY)
    
    # Создаем приложение
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Добавляем обработчики команд
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("clear", clear_history))
    app.add_handler(CommandHandler("help", help_command))
    
    # Обработчик текстовых сообщений
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Запускаем бота
    print("🤖 Бот активен и готов к работе!")
    app.run_polling()

if __name__ == '__main__':
    main()
