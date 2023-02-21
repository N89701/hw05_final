import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Group, Post

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
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

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small9999.gif',
            content=small_gif,
            content_type='image/gif'
        )
        Post.objects.all().delete()
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Пост, предназначенный для тестирования создания',
            'group': self.group.id,
            'image': uploaded
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
        self.assertEqual(tested_post.image, 'posts/small9999.gif')

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
        response = self.authorized_client.get(
            reverse('posts:post_detail', args=[tested_post.id])
        )
        post = response.context.get('post')
        self.assertEqual(post.text, form_data_changed.get('text'))
        self.assertEqual(post.group, self.group)


class CommentFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Kolyan')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост подлиннее',
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_on_correct_status_for_guest_user_for_public_pages(self):
        """При отправке комментария неавторизованным пользователям
        происходит редирект."""
        comment_url = reverse('posts:add_comment', args=[self.post.id])
        login_url = reverse('users:login')
        redirect_url = f'{login_url}?next=/posts/{self.post.id}/comment/'
        text = {
            'text': 'Пост, предназначенный для тестирования создания коммента',
        }
        response = self.guest_client.post(
            comment_url, data=text,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), 0)
        self.assertRedirects(response, redirect_url)

    def test_success_comment(self):
        """При отправке комментария авторизованным
        пользователем он сохраняется в БД."""
        Comment.objects.all().delete()
        text = {
            'text': 'Пост, предназначенный для тестирования создания',
        }
        self.authorized_client.post(
            reverse('posts:add_comment', args=[self.post.id]),
            data=text,
            follow=True
        )
        tested_comment = Comment.objects.last()
        self.assertEqual(tested_comment.text, text.get('text'))
        self.authorized_client.get(reverse(
            'posts:post_detail', args=[self.post.id]
        ))
        self.assertEqual(tested_comment.text, text.get('text'))
