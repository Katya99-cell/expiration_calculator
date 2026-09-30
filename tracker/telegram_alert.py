import os
import django
import requests


os.environ.setdefault(
    'DJANGO_SETTINGS_MODULE',
    'expiration_calculator.settings'
)

django.setup()


from django.conf import settings
from tracker.models import Product


def send_telegram_message(chat_id, text):

    token = settings.TELEGRAM_BOT_TOKEN

    if not token:
        print("❌ TELEGRAM_BOT_TOKEN не найден")
        return False

    url = (
        f"https://api.telegram.org/"
        f"bot{token}/sendMessage"
    )

    payload = {
        "chat_id": str(chat_id),
        "text": text,
        "parse_mode": "Markdown"
    }

    try:
        response = requests.post(
            url,
            json=payload,
            timeout=10
        )

        data = response.json()

        if response.ok and data.get("ok"):
            print(
                f"✅ Telegram сообщение отправлено "
                f"в чат {chat_id}"
            )
            return True

        print(
            f"❌ Telegram API ошибка: {data}"
        )

        return False


    except requests.RequestException as error:

        print(
            f"❌ Ошибка соединения с Telegram: {error}"
        )

        return False

def send_telegram_alert():

    print(
        "🔎 Проверяем продукты "
        "с истекающим сроком..."
    )

    products = (
        Product.objects
        .select_related('user__profile')
        .all()
    )

    user_notifications = {}


    for product in products:

        # Проверяем вычисляемый статус из models.py
        if product.status not in ['warning', 'expired']:
             continue


        user = product.user


        if not hasattr(user, 'profile'):
            continue


        chat_id = user.profile.telegram_chat_id


        if not chat_id:
            continue


        if chat_id not in user_notifications:
            user_notifications[chat_id] = []


        user_notifications[chat_id].append(product)



    if not user_notifications:

        print(
            "ℹ️ Нет продуктов с предупреждением "
            "или пользователей Telegram."
        )

        return



    for chat_id, products_list in user_notifications.items():

        product_lines = []


        for product in products_list:

            product_lines.append(
                f"🔸 *{product.name}* — "
                f"осталось {product.days_left} дн."
            )


        products_text = "\n".join(product_lines)


        message = (
            "⚠️ *Внимание!*\n\n"
            "Срок годности следующих продуктов "
            "истекает в ближайшее время:\n\n"
            f"{products_text}\n\n"
            "Откройте FreshManager для подробной информации."
        )


        send_telegram_message(
            chat_id,
            message
        )


if __name__ == "__main__":

    print(
        "🚀 Запуск проверки Telegram уведомлений"
    )

    send_telegram_alert()