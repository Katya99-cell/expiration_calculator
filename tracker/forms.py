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
            'manufacture_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'storage_temperature': forms.Select(attrs={'class': 'form-select'}),
            'is_opened': forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'id_is_opened'}),
            # Изначально блокируем поле даты вскрытия через disabled
            'opened_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'id': 'id_opened_date', 'disabled': 'disabled'}),
        }

    def clean(self):
        """Продвинутая комплексная валидация бизнес-логики дат для ВКР"""
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
            if not opened_date:
                self.add_error('opened_date', "Укажите дату вскрытия упаковки!")
            elif manufacture_date and opened_date < manufacture_date:
                self.add_error('opened_date', "Упаковка не могла быть вскрыта раньше, чем произведен продукт!")
            elif opened_date > today:
                self.add_error('opened_date', "Дата вскрытия не может быть в будущем!")
        
        return cleaned_data
