from django import forms

class UploadForm(forms.Form):
    slide = forms.IntegerField(label='Slide Number:')
    file = forms.ImageField(label='File (Stiched Image):')
