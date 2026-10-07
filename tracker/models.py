import datetime
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError

class Category(models.Model):
    """Категории товаров со стандартными сроками годности (ГОСТ/ТУ)"""
    name = models.CharField(max_length=100, verbose_name="Название категории")
    default_shelf_life_days = models.PositiveIntegerField(verbose_name="Срок хранения по умолчанию (дней)")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"


class Product(models.Model):
    """Продвинутая модель товара с учетом температуры хранения и вскрытия упаковки"""
    TEMPERATURE_CHOICES = [
        ('REFRIGERATOR', 'Холодильник (0...+4°C)'),
        ('ROOM', 'Комнатная температура (+18...+22°C)'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='products', verbose_name="Пользователь")
    name = models.CharField(max_length=150, verbose_name="Наименование товара")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Категория")
    
    manufacture_date = models.DateField(verbose_name="Дата производства")
    expiration_date = models.DateField(blank=True, null=True, db_index=True, verbose_name="Дата окончания срока (расчетная)")
    
    storage_temperature = models.CharField(
        max_length=20, 
        choices=TEMPERATURE_CHOICES, 
        default='REFRIGERATOR', 
        verbose_name="Условия хранения"
    )
    
    is_opened = models.BooleanField(default=False, verbose_name="Упаковка вскрыта")
    opened_date = models.DateField(blank=True, null=True, verbose_name="Дата вскрытия упаковки")

    def clean(self):
        """Полная валидация бизнес-логики дат перед сохранением"""
        super().clean()
        today = timezone.localdate()

        # 1. Защита от дат производства из будущего
        if self.manufacture_date and self.manufacture_date > today:
            raise ValidationError({
                'manufacture_date': f"Критическая ошибка: дата производства не может быть в будущем! (Введено: {self.manufacture_date}, Сегодня: {today})"
            })

        # 2. Проверка даты вскрытия упаковки
        if self.opened_date:
            if self.opened_date < self.manufacture_date:
                raise ValidationError({
                    'opened_date': f"Дата вскрытия ({self.opened_date}) не может быть раньше даты производства ({self.manufacture_date})."
                })
            if self.opened_date > today:
                raise ValidationError({
                    'opened_date': "Дата вскрытия не может быть в будущем."
                })

    def save(self, *args, **kwargs):
        """Многофакторный алгоритм калькуляции с учетом температуры и вскрытия"""
        # Принудительно вызываем clean() перед записью в БД для отлова дат из будущего
        self.full_clean() 
        
        if self.category:
            days = self.category.default_shelf_life_days
            
            # Влияние температуры: при комнатной температуре срок сокращается в 2 раза
            if self.storage_temperature == 'ROOM':
                days = max(1, int(days / 2))
            
            # Базовый срок (для закрытого товара в выбранных температурных условиях)
            base_expiration = self.manufacture_date + datetime.timedelta(days=days)
            
            # Влияние вскрытия: годен 3 дня, но не дольше, чем базовый срок
            if self.is_opened and self.opened_date:
                opened_expiration = self.opened_date + datetime.timedelta(days=3)
                self.expiration_date = min(base_expiration, opened_expiration)
            else:
                self.expiration_date = base_expiration
        else:
            # Если категория не указана, не ломаем логику (например, ставим 1 день по умолчанию)
            if not self.expiration_date:
                self.expiration_date = self.manufacture_date + datetime.timedelta(days=1)
                
        super().save(*args, **kwargs)

    @property
    def days_left(self):
        """Динамический расчет оставшихся дней с учетом таймзон Django"""
        if self.expiration_date:
            delta = self.expiration_date - timezone.localdate()
            return delta.days
        return 0

    @property
    def total_days(self):
        """Общий срок хранения данного товара в днях от производства"""
        if self.expiration_date and self.manufacture_date:
            return max(1, (self.expiration_date - self.manufacture_date).days)
        return 1

    @property
    def freshness_percentage(self):
        """Математически гарантированный расчет остаточного ресурса продукта в % """
        today = timezone.localdate()
        manufacture = self.manufacture_date
        expiration = self.expiration_date
        
        if not expiration or not manufacture:
            return 100
            
        total_duration = (expiration - manufacture).days
        if total_duration <= 0:
            return 0
            
        if today > expiration:
            return 0
            
        if today < manufacture:
            return 100
            
        days_left = (expiration - today).days
        percent_left = int((days_left / total_duration) * 100)
        
        return max(0, min(100, percent_left))

    @property
    def status(self):
        """Индикатор свежести для UI и cron-скриптов"""
        left = self.days_left
        if left < 0:
            return "expired"
        elif left <= 2:
            return "warning"
        return "fresh"

    def __str__(self):
        return f"{self.name} (До: {self.expiration_date})"

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"
        # Сортировка по умолчанию: сначала просрочка и то, что скоро испортится
        ordering = ['expiration_date'] 


class Profile(models.Model):
    """Профиль пользователя для интеграции с Telegram-ботом оповещений"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    # db_index добавлен для быстрого поиска пользователя при обработке вебхуков Telegram
    telegram_chat_id = models.CharField(max_length=50, blank=True, null=True, db_index=True, verbose_name="Telegram Chat ID")

    def __str__(self):
        return f"Профиль {self.user.username}"

    class Meta:
        verbose_name = "Профиль пользователя"
        verbose_name_plural = "Профили пользователей"
