from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.paginator import Page
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


class TemplateTest(TestCase):
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
            text='Тестовый пост подлиннее',
            author=cls.user,
            group=cls.group
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_on_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_reverse_names = {
            reverse('posts:home'): 'posts/index.html',
            reverse('posts:groups', args=[873]): 'posts/group_list.html',
            reverse('posts:profile', args=['auth']): 'posts/profile.html',
            reverse('posts:post_detail', args=[1]): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/post_create.html',
            reverse('posts:post_edit', args=[1]): 'posts/post_create.html'
        }
        for reverse_name, template in templates_reverse_names.items():
            with self.subTest(address=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_create_edit_page_show_correct_context(self):
        """Шаблоны create и edit page сформирован с правильным контекстом."""
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        urls = {
            reverse('posts:post_create'),
            reverse('posts:post_edit', args=[1])
        }
        for value, expected in form_fields.items():
            for url in urls:
                with self.subTest(value=value, url=url):
                    response = self.authorized_client.get(url)
                    form_field = response.context.get('form').fields.get(value)
                    self.assertIsInstance(form_field, expected)

    def asserter(self, post):
        with self.subTest(post=post):
            self.assertEqual(post.text, self.post.text)
            self.assertEqual(post.author, self.post.author)
            self.assertEqual(post.group.id, self.post.group.id)

    def test_index_page_show_correct_context(self):
        """Шаблон index.html сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:home'))
        self.asserter(response.context['page_obj'][0])

    def test_groups_page_show_correct_context(self):
        """Шаблон group_list.html сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:groups',
                                                      args=[873])
                                              )
        self.asserter(response.context['page_obj'][0])
        with self.subTest(post=response.context['page_obj'][0]):
            self.assertEqual(
                response.context['page_obj'][0].text,
                self.post.text
            )

    def test_profile_page_show_correct_context(self):
        """Шаблон profile.html сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:profile',
                                                      args=['auth'])
                                              )
        self.asserter(response.context['page_obj'][0])
        with self.subTest(post=response.context['page_obj'][0]):
            self.assertEqual(response.context['author'], self.user)

    def test_detail_page_show_correct_context(self):
        """Шаблон post_detail.html сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_detail',
                                                      args=[1])
                                              )
        self.asserter(response.context['post'])


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='873',
            description='Новая группа для пагинатора',
        )
        Post.objects.bulk_create([
            Post(
                text=f'Текста поста №{i}', author=cls.user, group=cls.group
            ) for i in range(11)
        ])

    def test_paginator(self):
        urls_expected_post_number = [
            [reverse('posts:home'), Post.objects.all()[:settings.PAGE_SIZE]],
            [reverse('posts:profile', args=['auth']),
             self.group.posts.all()[:settings.PAGE_SIZE]
             ],
            [reverse('posts:groups', args=[873]),
             self.user.posts.all()[:settings.PAGE_SIZE]
             ],
        ]
        for url, queryset in urls_expected_post_number:
            with self.subTest(url=url):
                response = self.client.get(url)
                page_obj = response.context.get('page_obj')
                self.assertIsNotNone(page_obj)
                self.assertIsInstance(page_obj, Page)
                self.assertQuerysetEqual(
                    page_obj.object_list, queryset, transform=lambda x: x
                )
