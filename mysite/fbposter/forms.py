from django import forms
from .models import Entry

class EntryForm(forms.ModelForm):
	class Meta:
		model = Entry
		fields = ('title','description','body','tags','public','post_to_fb','post_to_fb_public')
		