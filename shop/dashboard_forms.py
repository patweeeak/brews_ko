from django import forms
from .models import Product, Category, Order, ShopSettings, HomePageContent, GamificationSettings


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'category', 'name', 'slug', 'description', 'ingredients',
            'price', 'price_large', 'points', 'image', 'available', 'featured',
        ]
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Caramel Latte'}),
            'slug': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Leave blank to auto-generate'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Short description shown on the menu'}),
            'ingredients': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Comma-separated, e.g. Espresso, Steamed Milk, Caramel Syrup'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'price_large': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'points': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'price': 'Regular Price (₱)',
            'price_large': 'Large Price (₱)',
        }
        help_texts = {
            'points': 'Gamification points a customer earns per unit ordered.',
            'price_large': 'Required for drink categories — Regular and Large are both always offered to customers.',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['slug'].required = False
        self.fields['description'].required = False
        self.fields['price_large'].required = False

    def clean(self):
        cleaned = super().clean()
        category = cleaned.get('category')
        if category and category.is_drink and not cleaned.get('price_large'):
            self.add_error('price_large', "Large price is required for drink-category products — both sizes must be available.")
        return cleaned
        self.fields['ingredients'].required = False
        self.fields['image'].required = False


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'slug', 'description', 'icon', 'is_drink']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Espresso'}),
            'slug': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Leave blank to auto-generate'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'icon': forms.TextInput(attrs={'class': 'form-control', 'placeholder': "e.g. bi-cup-hot"}),
            'is_drink': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['slug'].required = False
        self.fields['description'].required = False
        self.fields['icon'].required = False


class OrderStatusForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['status']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
        }


class ShopSettingsForm(forms.ModelForm):
    class Meta:
        model = ShopSettings
        fields = ['name', 'address', 'phone', 'email', 'hours', 'facebook', 'instagram']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': "e.g. Brew's Ko"}),
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Street, Barangay, City'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+63 917 123 4567'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'hello@brewsko.ph'}),
            'hours': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Mon–Sun: 6:00 AM – 10:00 PM'}),
            'facebook': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://facebook.com/yourpage'}),
            'instagram': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://instagram.com/yourpage'}),
        }


class HomePageContentForm(forms.ModelForm):
    class Meta:
        model = HomePageContent
        fields = [
            'hero_eyebrow', 'hero_title', 'hero_subtitle', 'hero_image',
            'about_eyebrow', 'about_title', 'about_text_1', 'about_text_2', 'about_image',
            'feature_1_icon', 'feature_1_title', 'feature_1_text',
            'feature_2_icon', 'feature_2_title', 'feature_2_text',
        ]
        widgets = {
            'hero_eyebrow': forms.TextInput(attrs={'class': 'form-control'}),
            'hero_title': forms.TextInput(attrs={'class': 'form-control'}),
            'hero_subtitle': forms.TextInput(attrs={'class': 'form-control'}),
            'hero_image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'about_eyebrow': forms.TextInput(attrs={'class': 'form-control'}),
            'about_title': forms.TextInput(attrs={'class': 'form-control'}),
            'about_text_1': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'about_text_2': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'about_image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'feature_1_icon': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'bi-flower1'}),
            'feature_1_title': forms.TextInput(attrs={'class': 'form-control'}),
            'feature_1_text': forms.TextInput(attrs={'class': 'form-control'}),
            'feature_2_icon': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'bi-house-heart'}),
            'feature_2_title': forms.TextInput(attrs={'class': 'form-control'}),
            'feature_2_text': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name not in ('hero_image', 'about_image'):
                field.required = False


class GamificationSettingsForm(forms.ModelForm):
    class Meta:
        model = GamificationSettings
        fields = ['enabled', 'program_name']
        widgets = {
            'enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'program_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': "e.g. Brew's Ko Rewards"}),
        }
