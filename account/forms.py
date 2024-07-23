from django import forms
from django.contrib.auth.models import User
from .models import Profile


class LoginForm(forms.Form):
    username = forms.CharField(max_length=100)
    password = forms.CharField(widget=forms.PasswordInput)


class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Repeat password', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'email')

    def clean_password2(self):
        # проверка паролей на совпадения
        password = self.cleaned_data.get('password')
        password2 = self.cleaned_data.get('password2')
        if password != password2:
            raise forms.ValidationError('Passwords must match')
        return password

    def clean_email(self):
        # проверка уникальности email-адреса
        data = self.cleaned_data['email']
        if User.objects.filter(email=data).exists():
            raise forms.ValidationError('Адрес электронной почты уже существует')
        return data


class UserEditForm(forms.ModelForm):
    """
    Форма редактирования профиля пользователя.
    """
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')

    def clean_email(self):
        # проверка уникальности email-адреса
        data = self.cleaned_data['email']
        if User.objects.filter(email=data).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('Адрес электронной почты уже существует')
        return data


class ProfileEditForm(forms.ModelForm):
    """
    Форма редактирования профиля пользователя.
    """
    class Meta:
        model = Profile
        fields = ('date_of_birth', 'photo')

