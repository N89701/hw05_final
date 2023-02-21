from http import HTTPStatus
from django.core.cache import cache

from django.test import Client, TestCase

from ..models import Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Kolyan')
        cls.another_user = User.objects.create_user(username='strange')
        cls.group = Group.objects.create(
            title='Группа поддержки Коляна',
            slug='gogo_ahead',
            description='Группа для тех, кто поддерживает Коляна',
        )
        cls.my_post = Post.objects.create(
            author=cls.user,
            text='Пост, предназначенный для тестирования',
        )
        cls.another_post = Post.objects.create(
            author=cls.another_user,
            text='Пост, предназначенный для тестирования',
        )
        cls.public_urls_dict = {
            '/': 'posts/index.html',
            f'/group/{cls.group.slug}/': 'posts/group_list.html',
            f'/profile/{cls.user.username}/': 'posts/profile.html',
            f'/posts/{cls.my_post.id}/': 'posts/post_detail.html',
        }
        cls.private_urls_dict = {
            f'/posts/{cls.my_post.id}/edit/': 'posts/post_create.html',
            '/create/': 'posts/post_create.html',
        }
        cls.all_urls_dict = dict(cls.public_urls_dict, **cls.private_urls_dict)
        cls.nonexistent_address = 'nesuschestvuyuschiy_address'

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_on_correct_status_for_authorized_user(self):
        """URL-адрес выдает соответствующий HTTP.Response
        для авторизованного пользователя."""
        for address in self.all_urls_dict:
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_on_correct_status_for_guest_user_for_public_pages(self):
        """URL-адрес выдает соответствующий HTTP.Response для
        неавторизованного пользователя для публичных страниц."""
        for address in self.public_urls_dict:
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_on_correct_status_for_guest_user_for_private_pages(self):
        """URL-адрес выдает соответствующий HTTP.Response для
        неавторизованного пользователя для приватных страниц."""
        for address in self.private_urls_dict:
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_on_correct_status_for_redact_strange_post(self):
        """URL-адрес выдает соответствующий HTTP.Response для авторизованного
        пользователя при попытке редактирования чужого поста."""
        address = f'/posts/{self.another_post.id}/edit'
        response = self.guest_client.get(address)
        self.assertEqual(response.status_code, HTTPStatus.MOVED_PERMANENTLY)

    def test_on_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for address, template in self.all_urls_dict.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_on_correct_status_for_nonexistent_address(self):
        """URL-адрес выдает соответствующий HTTP.Response для авторизованного
        пользователя при попытке запроса несуществующего URL."""
        address = self.nonexistent_address
        response = self.guest_client.get(address)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, 'core/404.html')
