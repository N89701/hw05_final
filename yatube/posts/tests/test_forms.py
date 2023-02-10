from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug=873,
            description='Тестовое описание',
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст',
            'group': PostFormTests.group.id,
        }
        form_data_change = {
            'text': 'Тестовый текст222',
            'group': PostFormTests.group.id,
        }
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый текст',
                group=PostFormTests.group.id
            ).exists()
        )
        self.authorized_client.post(
            reverse('posts:post_edit', args=[1]),
            data=form_data_change,
            follow=True)
        self.assertTrue(Post.objects.filter(
            text='Тестовый текст222',
            group=PostFormTests.group.id
        ).exists())
        self.assertFalse(
            Post.objects.filter(
                text='Тестовый текст',
                group=PostFormTests.group.id
            ).exists())
