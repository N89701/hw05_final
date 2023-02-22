from django import forms

from .models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['text', 'group', 'image']
        labels = {
            'text': 'Текст поста',
            'group': 'Группа поста',
            'image': 'Картинка к посту'
        }
        help_texts = {
            'text': 'Введите ваш текст поста',
            'group': 'Группа, к которой относится ваш пост',
            'image': 'Добавьте картинку к посту'
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        labels = {'text': 'Текст комментария'}
        help_texts = {'text': 'Введите ваш текст комментария'}
