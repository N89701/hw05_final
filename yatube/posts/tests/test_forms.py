from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post, User


class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Kolyan')
        cls.group = Group.objects.create(
            title='Группа поддержки Коляна',
            slug='gogo_ahead',
            description='Группа для тех, кто поддерживает Коляна',
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        Post.objects.all().delete()
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Пост, предназначенный для тестирования создания',
            'group': self.group.id,
        }
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        tested_post = Post.objects.first()
        self.assertEqual(tested_post.text, form_data.get('text'))
        self.assertEqual(tested_post.group, self.group)

    def test_change_post(self):
        """Валидная форма изменяет запись в Post."""
        Post.objects.all().delete()
        form_data = {
            'text': 'Пост, предназначенный для тестирования создания',
            'group': self.group.id,
        }
        form_data_changed = {
            'text': 'Пост, предназначенный для тестирования редактирования',
            'group': self.group.id,
        }
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        tested_post = Post.objects.first()
        self.authorized_client.post(
            reverse('posts:post_edit', args=[tested_post.id]),
            data=form_data_changed,
            follow=True)
        response = self.authorized_client.get(reverse('posts:post_detail',
                                                      args=[tested_post.id])
                                              )
        post = response.context.get('post')
        self.assertEqual(post.text, form_data_changed.get('text'))
        self.assertEqual(post.group, self.group)
