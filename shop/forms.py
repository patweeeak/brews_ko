from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from .models import Order, CustomerProfile, Review


class CustomerAuthenticationForm(AuthenticationForm):
    """Branded login form for the customer user type (separate from /admin/login/)."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control', 'autocomplete': 'username', 'autofocus': True})
        self.fields['password'].widget.attrs.update({'class': 'form-control', 'autocomplete': 'current-password'})


class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['customer_name', 'contact_number', 'dining_option', 'notes']
        widgets = {
            'customer_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Juan Dela Cruz',
                'autocomplete': 'name',
            }),
            'contact_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. 0917 123 4567',
                'autocomplete': 'tel',
            }),
            'dining_option': forms.RadioSelect(),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Any special requests? (optional)',
                'rows': 3,
            }),
        }
        labels = {
            'customer_name': 'Full Name',
            'contact_number': 'Contact Number',
            'dining_option': 'For Here or To Go?',
            'notes': 'Special Instructions',
        }


class AddToCartForm(forms.Form):
    quantity = forms.IntegerField(
        min_value=1, max_value=50, initial=1,
        widget=forms.NumberInput(attrs={'class': 'form-control text-center', 'min': 1, 'max': 50})
    )


class CustomerSignupForm(UserCreationForm):
    """
    Signup for the 'customer' user type (as opposed to guests, who never
    create an account, and staff/admin, who never use this form).
    """
    full_name = forms.CharField(
        max_length=150, label='Full Name',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Juan Dela Cruz', 'autocomplete': 'name'})
    )
    mobile_number = forms.CharField(
        max_length=20, label='Mobile Number',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '0917 123 4567', 'autocomplete': 'tel'})
    )

    class Meta:
        model = User
        fields = ['username', 'full_name', 'mobile_number', 'email', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'username'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'autocomplete': 'email'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = False
        for name in ['password1', 'password2']:
            self.fields[name].widget.attrs.update({'class': 'form-control'})

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            CustomerProfile.objects.create(
                user=user,
                full_name=self.cleaned_data['full_name'],
                mobile_number=self.cleaned_data['mobile_number'],
            )
        return user


class CustomerProfileForm(forms.ModelForm):
    class Meta:
        model = CustomerProfile
        fields = ['full_name', 'mobile_number', 'photo']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'mobile_number': forms.TextInput(attrs={'class': 'form-control'}),
            'photo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment', 'image']
        widgets = {
            'rating': forms.RadioSelect(choices=[(i, i) for i in range(5, 0, -1)]),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Share your experience...'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['image'].required = False
