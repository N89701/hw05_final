from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост подлиннее',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        expected_result_for_group = 'Тестовая группа'
        expected_result_for_post = 'Тестовый пост п'
        self.assertEqual(
            PostModelTest.group.__str__(),
            expected_result_for_group, 'no'
        )
        self.assertEqual(
            PostModelTest.post.__str__(),
            expected_result_for_post, 'no'
        )
