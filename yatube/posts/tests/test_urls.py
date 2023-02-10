from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug=873,
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост подлиннее',
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_on_correct_status(self):
        """URL-адрес выдает соответствующий HTTP.Response."""
        code_200_url_names = ['/',
                              '/group/873/',
                              '/profile/auth/',
                              '/posts/1/',
                              '/posts/1/edit/',
                              '/create/']
        for address in code_200_url_names:
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, 200)
        code_302_url_names = ['/posts/1/edit/', '/create/']
        for address in code_302_url_names:
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, 302)
        code_404_url_names = 'nesuschestvuyushshiy_adress'
        response = self.guest_client.get(code_404_url_names)
        self.assertEqual(response.status_code, 404)

    def test_on_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/': 'posts/index.html',
            '/group/873/': 'posts/group_list.html',
            '/profile/auth/': 'posts/profile.html',
            '/posts/1/': 'posts/post_detail.html',
            '/posts/1/edit/': 'posts/post_create.html',
            '/create/': 'posts/post_create.html'
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)
