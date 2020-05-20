from django import forms
from .models import ArticlePost

class ArticlePosrForm(forms.ModelForm):
    class Meta:

        model = ArticlePost

        fields = ('title', 'body')
