from django import forms
from django.utils import timezone
from .models import Product

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'category', 'manufacture_date', 'storage_temperature', 'is_opened', 'opened_date']
        
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Например: Йогурт клубничный'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            # Поле даты производства теперь по умолчанию будет иметь текущую дату в календаре
            'manufacture_date': forms.DateInput(attrs={
                'class': 'form-control', 
                'type': 'date',
                'value': timezone.localdate
            }),
            'storage_temperature': forms.Select(attrs={'class': 'form-select'}),
            'is_opened': forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'id_is_opened'}),
            # Используем readonly вместо disabled, чтобы браузер отправлял данные на сервер
            'opened_date': forms.DateInput(attrs={
                'class': 'form-control', 
                'type': 'date', 
                'id': 'id_opened_date', 
                'readonly': 'readonly'
            }),
        }

    def clean(self):
        """Продвинутая комплексная валидация бизнес-логики дат"""
        cleaned_data = super().clean()
        manufacture_date = cleaned_data.get('manufacture_date')
        is_opened = cleaned_data.get('is_opened')
        opened_date = cleaned_data.get('opened_date')
        today = timezone.localdate()

        # 1. Проверка даты производства
        if manufacture_date and manufacture_date > today:
            self.add_error('manufacture_date', "Дата производства не может быть в будущем!")

        # 2. Проверка логики вскрытия упаковки
        if is_opened:
            # АВТОМАТИЗАЦИЯ: если галочка стоит, а дата пустая — подставляем сегодня автоматически
            if not opened_date:
                opened_date = today
                cleaned_data['opened_date'] = today
            
            # Проверки корректности дат
            if manufacture_date and opened_date < manufacture_date:
                self.add_error('opened_date', "Упаковка не могла быть вскрыта раньше, чем произведен продукт!")
            elif opened_date > today:
                self.add_error('opened_date', "Дата вскрытия не может быть в будущем!")
        else:
            # Если галочку сняли, то дату вскрытия нужно очистить
            cleaned_data['opened_date'] = None
        
        return cleaned_data
