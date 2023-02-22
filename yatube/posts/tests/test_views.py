
import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.paginator import Page
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..forms import PostForm, CommentForm
from ..models import Follow, Group, Post, User, Comment

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Kolyan')
        cls.group = Group.objects.create(
            title='Группа поддержки Коляна',
            slug='gogo_ahead',
            description='Группа для тех, кто поддерживает Коляна',
        )
        cls.another_group = Group.objects.create(
            title='Пост, предназначенный для тестирования',
            slug='gogo_down',
            description='Группа для тех, кто поддерживает Коляна',
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small1.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            text='Текст для тестирования, просто текст',
            author=cls.user,
            group=cls.group,
            image=uploaded
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='Текст комментария'
        )
        cls.urls_with_paginator = {
            '/': reverse('posts:home'),
            f'/group/{cls.group.slug}/': reverse(
                'posts:groups', args=[cls.group.slug]
            ),
            f'/profile/{cls.user.username}/': reverse(
                'posts:profile', args=[cls.user.username]
            ),
        }
        cls.urls_post_detail = {
            f'/posts/{cls.post.id}/': reverse(
                'posts:post_detail', args=[cls.post.id]
            )
        }
        cls.public_urls = dict(
            cls.urls_with_paginator,
            **cls.urls_post_detail
        )
        cls.private_urls = {
            f'/posts/{cls.post.id}/edit/': reverse(
                'posts:post_edit', args=[cls.post.id]
            ),
            '/create/': reverse('posts:post_create'),
        }
        cls.all_urls = dict(cls.public_urls, **cls.private_urls)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_on_correct_URL(self):
        """Reverse использует соответствующий URL-адрес."""
        for url, reverse_name in self.all_urls.items():
            with self.subTest():
                self.assertEqual(url, reverse_name)

    def test_create_edit_page_show_correct_context(self):
        """Шаблоны create и edit page сформирован с правильным контекстом."""
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for url in self.private_urls:
            for value, expected in form_fields.items():
                with self.subTest(value=value, url=url):
                    response = self.authorized_client.get(url)
                    form_field = response.context.get('form')
                    self.assertIsInstance(form_field, PostForm)
                    value_field = form_field.fields.get(value)
                    self.assertIsInstance(value_field, expected)

    def test_for_correct_work_cache(self):
        """Тест на корректное сохранение информации в кэше"""
        content = self.client.get(reverse('posts:home')).content
        Post.objects.all().delete()
        content_after_delete = self.client.get(reverse('posts:home')).content
        self.assertEqual(content, content_after_delete)
        cache.clear()
        content_empty_cache = self.client.get(reverse('posts:home')).content
        self.assertNotEqual(content, content_empty_cache)

    def checking_for_attributes(self, context, is_page=True):
        if is_page:
            page = context.get('page_obj')
            self.assertIsInstance(page, Page)
            post = page[0]
        else:
            post = context.get('post')
        self.assertIsInstance(post, Post)
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.author, self.post.author)
        self.assertEqual(post.group.id, self.post.group.id)
        self.assertEqual(post.image, self.post.image)

    def test_index_page_show_correct_context(self):
        """Шаблон index.html сформирован с правильным контекстом."""
        context = self.client.get(self.all_urls.get('/')).context
        self.checking_for_attributes(context)

    def test_groups_page_show_correct_context(self):
        """Шаблон group_list.html сформирован с правильным контекстом."""
        context = self.client.get(
            self.all_urls.get(f'/group/{self.group.slug}/')
        ).context
        self.checking_for_attributes(context)
        self.assertEqual(context.get('group'), self.group)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile.html сформирован с правильным контекстом."""
        context = self.client.get(self.all_urls.get(
            f'/profile/{self.user.username}/'
        )).context
        self.checking_for_attributes(context)
        self.assertEqual(context.get('author'), self.user)

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail.html сформирован с правильным контекстом."""
        context = self.client.get(self.all_urls.get(
            f'/posts/{self.post.id}/'
        )).context
        self.checking_for_attributes(context, False)
        self.assertIsInstance(context.get('form'), CommentForm)
        self.assertEqual(context.get('comments').first(), self.comment)

    def test_on_empty_another_group(self):
        """Пост не публикуется в других группах."""
        url = f'/group/{self.another_group.slug}/'
        response = self.authorized_client.get(url)
        page = response.context.get('page_obj')
        self.assertNotIn(self.post, page)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Kolyan')
        cls.group = Group.objects.create(
            title='Группа поддержки Коляна',
            slug='gogo_ahead',
            description='Группа для тех, кто поддерживает Коляна',
        )
        cls.RANGE_CREATE = settings.PAGE_SIZE + 3
        Post.objects.bulk_create([
            Post(
                text=f'Текста поста №{i}', author=cls.user, group=cls.group
            ) for i in range(cls.RANGE_CREATE)
        ])
        cls.urls_with_paginator = [
            '/',
            f'/group/{cls.group.slug}/',
            f'/profile/{cls.user.username}/',
        ]

    def setUp(self):
        cache.clear()

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
                    self.RANGE_CREATE - settings.PAGE_SIZE
                )


class FollowsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Kolyan')
        cls.author = User.objects.create_user(username='Vovan')
        cls.post = Post.objects.create(
            text='Текст для тестирования, просто текст',
            author=cls.author,
        )
        cls.follow = Follow.objects.create(
            user=cls.user,
            author=cls.author
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_follow_for_authorized_user(self):
        """Тестируем возможность подписки авторизованным пользователем"""
        Follow.objects.all().delete()
        url = reverse('posts:profile_follow', args=[self.author.username])
        self.authorized_client.get(url)
        self.assertTrue(Follow.objects.filter(
            user=self.user,
            author=self.author
        ))

    def test_unfollow_for_authorized_user(self):
        """Тестируем возможность отписки авторизованным пользователем"""
        url_unfollow = reverse(
            'posts:profile_unfollow', args=[self.author.username]
        )
        self.authorized_client.get(url_unfollow)
        self.assertFalse(Follow.objects.all())

    def test_for_posts_from_following_authors(self):
        """Тестируем, что на странице подписок появляется пост автора,
        на которого подписан пользователь"""
        url = reverse('posts:follow_index')
        context = self.authorized_client.get(url).context.get('page_obj')
        self.assertIn(self.post, context)

    def test_for_none_if_unfollowing(self):
        """Тестируем, что на странице подписок  не появляется пост автора,
        на которого неподписан пользователь"""
        Follow.objects.all().delete()
        url = reverse('posts:follow_index')
        context = self.authorized_client.get(url).context.get('page_obj')
        self.assertNotIn(self.post, context)
    
    def test_for_follow_self(self):
        """Тестируем, что нельзя подписаться на самого себя"""
        url = reverse('posts:follow_index')
        following = self.authorized_client.get(url).context.get('following')
        self.assertFalse(following)
