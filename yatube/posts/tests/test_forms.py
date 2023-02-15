from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()
test_username = 'Kolyan'
test_title = 'Группа поддержки Коляна'
test_slug = 'gogo_ahead'
test_description = 'Группа для тех, кто поддерживает Коляна в его начинаниях'
test_text = 'Пост, предназначенный для тестирования создания'
test_text_changed = 'Пост, предназначенный для тестирования редактирования'


class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=test_username)
        cls.group = Group.objects.create(
            title=test_title,
            slug=test_slug,
            description=test_description,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        objects = Post.objects.all()
        objects.delete()
        posts_count = Post.objects.count()
        form_data = {
            'text': test_text,
            'group': self.group.id,
        }
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        tested_post = Post.objects.first()
        self.assertEqual(tested_post.text, test_text)
        self.assertEqual(tested_post.group, self.group)

    def test_change_post(self):
        """Валидная форма изменяет запись в Post."""
        objects = Post.objects.all()
        objects.delete()
        form_data = {
            'text': test_text,
            'group': self.group.id,
        }
        form_data_changed = {
            'text': test_text_changed,
            'group': self.group.id,
        }
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.authorized_client.post(
            reverse('posts:post_edit', args=[1]),
            data=form_data_changed,
            follow=True)
        response = self.authorized_client.get(reverse('posts:post_detail',
                                                      args=[1])
                                              )
        post = response.context.get('post')
        self.assertEqual(post.text, test_text_changed)
        self.assertEqual(post.group, self.group)
