from django import forms
from django.contrib.auth.models import User

class SignupForm(forms.ModelForm):
    password=forms.CharField(widget=forms.PasswordInput)
    confirmpassword=forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model=User
        fields=['username','email','password']

    def clean(self):
        cleaned_data=super().clean()
        if(cleaned_data.get('password')!=cleaned_data.get('confirmpassword')):
            raise forms.ValidationError("Passwords do not match")
        return cleaned_data