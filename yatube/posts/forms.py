from django import forms

from .models import Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group')
        labels = {'text': 'Текст поста',
                  'group': 'Группа поста'}
        help_texts = {
            'text': 'Введите ваш текст поста',
        }
