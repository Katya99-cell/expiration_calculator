from django.apps import AppConfig
from django.db.models.signals import post_migrate

def create_default_categories(sender, **kwargs):
    """Автоматическое наполнение базы данных категориями ГОСТ/ТУ для ВКР"""
    # Ленивый импорт модели внутри функции обязателен, чтобы избежать AppRegistryNotReady
    from tracker.models import Category
    
    # Проверяем, есть ли уже категории в БД, чтобы не дублировать при каждом запуске migrate
    if not Category.objects.exists():
        Category.objects.bulk_create([
            Category(name="Молочные продукты", default_shelf_life_days=7),
            Category(name="Консервы мясные/рыбные", default_shelf_life_days=730),
            Category(name="Хлебобулочные изделия", default_shelf_life_days=3),
            Category(name="Фрукты и овощи", default_shelf_life_days=14),
            Category(name="Замороженные полуфабрикаты", default_shelf_life_days=180),
        ])
        print(" Справочник категорий ГОСТ успешно загружен в базу данных!")

class TrackerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tracker'
    verbose_name = 'Контроль сроков годности' # Красивое отображение в админке для диплома

    def ready(self):
        # 1. Подключаем автоматический триггер наполнения категорий после миграций
        post_migrate.connect(create_default_categories, sender=self)
        
        # 2. ОБЯЗАТЕЛЬНО: Подключаем сигналы профилей (создание Profile при регистрации User)
        import tracker.signals
