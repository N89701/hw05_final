from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.paginator import Page
from django.test import Client, TestCase
from django.urls import reverse
from django.core.paginator import Page

from ..models import Group, Post
from ..forms import PostForm

User = get_user_model()
test_username = 'Kolyan'
test_title = 'Группа поддержки Коляна'
test_slug = 'gogo_ahead'
test_another_slug = 'gogo_down'
test_description = 'Группа для тех, кто поддерживает Коляна в его начинаниях'
test_text = 'Пост, предназначенный для тестирования'
strange_username = 'strange'
test_nonexistent_address = 'nesuschestvuyuschiy_address'
RANGE_CREATE = settings.PAGE_SIZE + 3


class TemplateTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=test_username)
        cls.group = Group.objects.create(
            title=test_title,
            slug=test_slug,
            description=test_description,
        )
        cls.another_group = Group.objects.create(
            title=test_title,
            slug=test_another_slug,
            description=test_description,
        )
        cls.post = Post.objects.create(
            text=test_text,
            author=cls.user,
            group=cls.group
        )
        cls.reverse_list = [[reverse('posts:home'),
                            '/'],
                            [reverse('posts:groups', args=[cls.group.slug]),
                            f'/group/{cls.group.slug}/'],
                            [reverse('posts:profile',
                                     args=[cls.user.username]),
                            f'/profile/{cls.user.username}/'],
                            [reverse('posts:post_detail', args=[cls.post.id]),
                            f'/posts/{cls.post.id}/'],
                            [reverse('posts:post_create'),
                            'posts/post_create.html'],
                            [reverse('posts:post_edit', args=[cls.post.id]),
                            f'/posts/{cls.post.id}/edit/']
                            ]

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_on_correct_template(self):
        """Reverse использует соответствующий URL-адрес."""
        for reverse_name, url in enumerate(self.reverse_list):
            with self.subTest():
                reverse_response = self.authorized_client.get(
                    reverse_name).__init__()
                url_response = self.authorized_client.get(url).__init__()
                self.assertEqual(reverse_response, url_response)

    def test_create_edit_page_show_correct_context(self):
        """Шаблоны create и edit page сформирован с правильным контекстом."""
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for i in range(4, 6):
            url = self.reverse_list[i][0]
            for value, expected in form_fields.items():
                with self.subTest(value=value, url=url):
                    response = self.authorized_client.get(url)
                    form_field = response.context.get('form')
                    self.assertIsInstance(form_field, PostForm)
                    value_field = form_field.fields.get(value)
                    self.assertIsInstance(value_field, expected)

    def checking_for_attributes(self, i):
        url = self.reverse_list[i][0]
        response = self.authorized_client.get(url)
        page = response.context['page_obj']
        if isinstance(page, Page):
            post = page[0]
        elif isinstance(page, Post):
            post = page
        else:
            self.assertEqual(True, False, 'Что то пошло не так')
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.author, self.post.author)
        self.assertEqual(post.group.id, self.post.group.id)
        if 'group' in response.context.keys():
            self.assertEqual(self.group, post.group)
        if 'author' in response.context.keys():
            self.assertEqual(self.user, post.author)

    def test_index_page_show_correct_context(self):
        """Шаблон index.html сформирован с правильным контекстом."""
        self.checking_for_attributes(0)

    def test_groups_page_show_correct_context(self):
        """Шаблон group_list.html сформирован с правильным контекстом."""
        self.checking_for_attributes(1)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile.html сформирован с правильным контекстом."""
        self.checking_for_attributes(2)

    def test_on_empty_another_group(self):
        """Пост не публикуется в других группах."""
        url = f'/group/{self.another_group.slug}/'
        response = self.authorized_client.get(url)
        page = response.context['page_obj']
        if isinstance(page, Page):
            self.assertEqual(len(page), 0)
        else:
            self.assertEqual(True, False, 'Что то пошло не так')


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=test_username)
        cls.group = Group.objects.create(
            title=test_title,
            slug=test_slug,
            description=test_description,
        )
        Post.objects.bulk_create([
            Post(
                text=f'Текста поста №{i}', author=cls.user, group=cls.group
            ) for i in range(RANGE_CREATE)
        ])
        cls.urls_with_paginator = ['/',
                                   f'/group/{cls.group.slug}/',
                                   f'/profile/{cls.user.username}/',
                                   ]

    def test_paginator(self):
        """Количество постов на 1й и 2й странице соответствует ожидаемому."""
        for url in self.urls_with_paginator:
            with self.subTest():
                response = self.client.get(url)
                page_obj = response.context.get('page_obj')
                self.assertIsInstance(page_obj, Page)
                self.assertEqual(len(page_obj), settings.PAGE_SIZE)
                response2 = self.client.get(url + '?page=2')
                page_obj2 = response2.context.get('page_obj')
                self.assertIsInstance(page_obj2, Page)
                self.assertEqual(
                    len(page_obj2),
                    RANGE_CREATE - settings.PAGE_SIZE
                )
