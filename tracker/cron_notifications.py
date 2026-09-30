import os
import django
import requests


# ---------------------------------------------------------
# Инициализация Django
# ---------------------------------------------------------

os.environ.setdefault(
    'DJANGO_SETTINGS_MODULE',
    'expiration_calculator.settings'
)

django.setup()


from django.conf import settings
from tracker.models import Product


def send_telegram_alert():
    """
    Проверяет сроки годности продуктов и отправляет
    Telegram-уведомления пользователям.
    """

    # -----------------------------------------------------
    # Получаем токен Telegram-бота
    # -----------------------------------------------------

    bot_token = getattr(
        settings,
        'TELEGRAM_BOT_TOKEN',
        None
    )

    if not bot_token:
        print(
            "❌ Ошибка: TELEGRAM_BOT_TOKEN "
            "не указан в settings.py"
        )
        return


    # -----------------------------------------------------
    # Правильный URL Telegram Bot API
    # -----------------------------------------------------

    url = (
        f"https://t.me/expiration_calculator_bot"
        f"bot{8596050453:AAHPBG44A6XCM0WniYSzhKY0NXVfhR2ZejY}/sendMessage"
    )


    # -----------------------------------------------------
    # Получаем продукты вместе с пользователями и профилями
    # -----------------------------------------------------

    products_queryset = (
        Product.objects
        .select_related('user__profile')
        .all()
    )


    # -----------------------------------------------------
    # Отбираем продукты, срок которых истекает
    # в течение ближайших двух дней
    # -----------------------------------------------------

    urgent_products = []

    for product in products_queryset:

        # Проверяем статус продукта
        if product.status != 'warning':
            continue

        # Проверяем наличие профиля
        if not hasattr(product.user, 'profile'):
            continue

        # Получаем Chat ID
        chat_id = product.user.profile.telegram_chat_id

        if not chat_id:
            continue

        urgent_products.append(product)


    # -----------------------------------------------------
    # Если уведомлять некого
    # -----------------------------------------------------

    if not urgent_products:

        print(
            "ℹ️ Нет продуктов с истекающим "
            "сроком годности."
        )

        return


    # -----------------------------------------------------
    # Группируем продукты по пользователям
    # -----------------------------------------------------

    user_notifications = {}

    for product in urgent_products:

        chat_id = product.user.profile.telegram_chat_id

        if chat_id not in user_notifications:
            user_notifications[chat_id] = []

        user_notifications[chat_id].append(product)


    # -----------------------------------------------------
    # Отправляем уведомления
    # -----------------------------------------------------

    for chat_id, products in user_notifications.items():

        product_lines = []

        for product in products:

            product_lines.append(
                f"🔸 {product.name} — "
                f"осталось {product.days_left} дн."
            )


        products_text = "\n".join(product_lines)


        message = (
            "⚠️ *Внимание! Срок годности истекает!*\n\n"
            "Следующие продукты необходимо "
            "использовать в ближайшее время:\n\n"
            f"{products_text}\n\n"
            "Откройте веб-приложение для подробной информации."
        )


        payload = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'Markdown'
        }


        try:

            response = requests.post(
                url,
                json=payload,
                timeout=10
            )


            if response.ok:

                print(
                    f"✅ Уведомление успешно отправлено "
                    f"в чат {chat_id}"
                )

            else:

                print(
                    f"❌ Telegram API вернул ошибку.\n"
                    f"Chat ID: {chat_id}\n"
                    f"Код: {response.status_code}\n"
                    f"Ответ: {response.text}"
                )


        except requests.RequestException as error:

            print(
                f"❌ Ошибка соединения с Telegram API: "
                f"{error}"
            )


# ---------------------------------------------------------
# Запуск скрипта
# ---------------------------------------------------------

if __name__ == '__main__':

    print(
        "🚀 Автоматический сканер сроков "
        "годности запущен..."
    )

    send_telegram_alert()