from django.test import TestCase

from ..models import Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Моя любимая группа',
            slug='fav_group',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост подлиннее',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__"""
        str_dict = {
            str(PostModelTest.group): self.group.title,
            str(PostModelTest.post): self.post.text[:15]
        }
        for method_result, expected_value in str_dict.items():
            with self.subTest():
                self.assertEqual(method_result, expected_value)
