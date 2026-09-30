import os
import django
import telebot


# =========================================================
# Инициализация Django
# =========================================================

os.environ.setdefault(
    'DJANGO_SETTINGS_MODULE',
    'expiration_calculator.settings'
)

django.setup()


from django.conf import settings


# =========================================================
# Telegram token
# =========================================================

TOKEN = settings.TELEGRAM_BOT_TOKEN


if not TOKEN:
    raise RuntimeError(
        'TELEGRAM_BOT_TOKEN не найден в .env'
    )


bot = telebot.TeleBot(TOKEN)


# =========================================================
# Команда /start
# =========================================================

@bot.message_handler(commands=['start'])
def send_welcome(message):

    chat_id = message.chat.id

    response_text = (
        "🍏 *Добро пожаловать в FreshManager!*\n\n"
        "Ваш Telegram Chat ID:\n\n"
        f"`{chat_id}`\n\n"
        "Скопируйте это число и вставьте его "
        "в поле Telegram Chat ID на сайте."
    )

    bot.reply_to(
        message,
        response_text,
        parse_mode='Markdown'
    )


# =========================================================
# Другие команды /help
# =========================================================

@bot.message_handler(commands=['help'])
def send_help(message):

    bot.reply_to(
        message,
        "Нажмите /start, чтобы получить ваш Telegram Chat ID."
    )


# =========================================================
# Запуск
# =========================================================

if __name__ == '__main__':

    print(
        "🤖 Telegram-бот запущен."
    )

    bot.infinity_polling(
        skip_pending=True
    )

