from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings

import telebot

from .models import Product, Profile
from .forms import ProductForm


# =========================================================
# Telegram
# =========================================================

BOT_TOKEN = settings.TELEGRAM_BOT_TOKEN

bot = (
    telebot.TeleBot(BOT_TOKEN)
    if BOT_TOKEN
    else None
)


# =========================================================
# Список продуктов
# =========================================================

@login_required
def products_list(request):

    profile, created = Profile.objects.get_or_create(
        user=request.user
    )

    # =====================================================
    # Привязка Telegram
    # =====================================================

    if (
        request.method == 'POST'
        and 'save_profile' in request.POST
    ):

        chat_id = request.POST.get(
            'telegram_chat_id',
            ''
        ).strip()

        if not chat_id:

            messages.error(
                request,
                "Введите Telegram Chat ID."
            )

            return redirect('products_list')

        # Проверяем, что ID состоит из цифр
        if not chat_id.lstrip('-').isdigit():

            messages.error(
                request,
                "Telegram Chat ID должен быть числовым."
            )

            return redirect('products_list')

        # Сохраняем
        profile.telegram_chat_id = chat_id
        profile.save()

        # =================================================
        # Проверяем Telegram
        # =================================================

        if bot:

            try:

                bot.send_message(
                    chat_id,
                    "✅ Telegram успешно привязан!\n\n"
                    "Теперь FreshManager сможет "
                    "отправлять вам предупреждения "
                    "об истекающих сроках годности."
                )

                messages.success(
                    request,
                    "Telegram успешно привязан! "
                    "Проверьте сообщение от бота."
                )

            except Exception as error:

                print(
                    f"Telegram error: {error}"
                )

                messages.warning(
                    request,
                    "ID сохранён, но Telegram "
                    "не смог получить сообщение. "
                    "Сначала нажмите /start в боте."
                )

        else:

            messages.warning(
                request,
                "Telegram-бот не настроен."
            )

        return redirect('products_list')

    # =====================================================
    # Продукты
    # =====================================================

    user_products = (
        Product.objects
        .filter(user=request.user)
        .select_related('category')
        .order_by('expiration_date')
    )

    search_query = request.GET.get(
        'search',
        ''
    )

    if search_query:

        user_products = user_products.filter(
            name__icontains=search_query
        )

    total_count = user_products.count()

    expired_count = sum(
        1
        for product in user_products
        if product.status == 'expired'
    )

    warning_count = sum(
        1
        for product in user_products
        if product.status == 'warning'
    )

    context = {
        'products': user_products,
        'total_count': total_count,
        'expired_count': expired_count,
        'warning_count': warning_count,
        'search_query': search_query,
        'profile': profile,
    }

    return render(
        request,
        'tracker/products.html',
        context
    )


# =========================================================
# Добавление продукта
# =========================================================

@login_required
def add_product(request):

    if request.method == 'POST':

        form = ProductForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():

            product = form.save(
                commit=False
            )

            product.user = request.user

            product.save()

            messages.success(
                request,
                f"Продукт «{product.name}» успешно добавлен."
            )

            return redirect('products_list')

    else:

        form = ProductForm()

    context = {
        'form': form,
    }

    return render(
        request,
        'tracker/add_product.html',
        context
    )