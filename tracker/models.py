import datetime
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Category(models.Model):
    """Категории товаров со стандартными сроками годности (ГОСТ/ТУ)"""
    name = models.CharField(max_length=100, verbose_name="Название категории")
    default_shelf_life_days = models.IntegerField(verbose_name="Срок хранения по умолчанию (дней)")

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

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    name = models.CharField(max_length=150, verbose_name="Наименование товара")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, verbose_name="Категория")
    
    manufacture_date = models.DateField(verbose_name="Дата производства")
    expiration_date = models.DateField(blank=True, null=True, verbose_name="Дата окончания срока (расчетная)")
    
    storage_temperature = models.CharField(
        max_length=20, 
        choices=TEMPERATURE_CHOICES, 
        default='REFRIGERATOR', 
        verbose_name="Условия хранения"
    )
    
    is_opened = models.BooleanField(default=False, verbose_name="Упаковка вскрыта")
    opened_date = models.DateField(blank=True, null=True, verbose_name="Дата вскрытия упаковки")

    def save(self, *args, **kwargs):
        """Многофакторный алгоритм калькуляции сроков хранения для ВКР"""
        if self.category:
            days = self.category.default_shelf_life_days
            
            # Влияние температуры: при комнатной температуре срок сокращается в 2 раза
            if self.storage_temperature == 'ROOM':
                days = max(1, int(days / 2))
            
            # Влияние фактора вскрытия герметичности (по бизнес-логике: годен 3 дня после вскрытия)
            if self.is_opened and self.opened_date:
                self.expiration_date = self.opened_date + datetime.timedelta(days=3)
            else:
                self.expiration_date = self.manufacture_date + datetime.timedelta(days=days)
                
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
        """Общий срок хранения данного товара в днях от производства до дедлайна"""
        if self.expiration_date and self.manufacture_date:
            return max(1, (self.expiration_date - self.manufacture_date).days)
        return 1

    @property
    def freshness_percentage(self):
        """Математически гарантированный расчет остаточного ресурса продукта в % для ВКР"""
        today = timezone.localdate()
        manufacture = self.manufacture_date
        expiration = self.expiration_date
        
        if not expiration or not manufacture:
            return 100
            
        total_duration = (expiration - manufacture).days
        
        if total_duration <= 0:
            return 0
            
        # Если продукт уже просрочен
        if today > expiration:
            return 0
            
        # Если продукт еще не произведен (ситуация из будущего)
        if today < manufacture:
            return 100
            
        days_left = (expiration - today).days
        percent_left = int((days_left / total_duration) * 100)
        
        # Гарантируем рамки от 0 до 100
        return max(0, min(100, percent_left))

    @property
    def status(self):
        """Индикатор свежести для UI (согласовано со скриптом cron_notifications.py)"""
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


class Profile(models.Model):
    """Профиль пользователя для интеграции с Telegram-ботом оповещений"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    telegram_chat_id = models.CharField(max_length=50, blank=True, null=True, verbose_name="Telegram Chat ID")

    def __str__(self):
        return f"Профиль {self.user.username}"

    class Meta:
        verbose_name = "Профиль пользователя"
        verbose_name_plural = "Профили пользователей"
