from django import forms

class UploadForm(forms.Form):
    slide = forms.IntegerField(label='Slide Number:')
    file = forms.FileField(label='File (Stiched Image):')

class CaptureForm(forms.Form):
    slide = forms.IntegerField(label='Slide Number:')
    only_wbc = forms.BooleanField(label='WBC Only:', initial=True)
    wbc_count = forms.IntegerField(label='WBC Count:', initial=100)
    field_limit = forms.IntegerField(label='Field Limit:', initial=100)
    microscope_ip = forms.CharField(label='Microscope IP Address:', initial='192.168.1.210:5000')
