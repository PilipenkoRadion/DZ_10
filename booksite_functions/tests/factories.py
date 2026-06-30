import factory
from factory.django import DjangoModelFactory
from django.contrib.auth import get_user_model
from booksite_functions.models import Book, Category, Order, OrderItem

User = get_user_model()


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User
        django_get_or_create = ('username',)

    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.LazyAttribute(lambda o: f'{o.username}@example.com')
    password = factory.PostGenerationMethodCall('set_password', 'TestPass123!')


class CategoryFactory(DjangoModelFactory):
    class Meta:
        model = Category
        django_get_or_create = ('slug',)

    name = factory.Sequence(lambda n: f'Category {n}')
    slug = factory.Sequence(lambda n: f'category-{n}')


class BookFactory(DjangoModelFactory):
    class Meta:
        model = Book

    title = factory.Faker('sentence', nb_words=3)
    author = factory.Faker('name')
    price = factory.Faker('pydecimal', left_digits=3, right_digits=2, positive=True)
    description = factory.Faker('text', max_nb_chars=100)
    stock = 10
    category = factory.SubFactory(CategoryFactory)


class OrderFactory(DjangoModelFactory):
    class Meta:
        model = Order

    user = None
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    email = factory.Faker('email')


class OrderItemFactory(DjangoModelFactory):
    class Meta:
        model = OrderItem

    order = factory.SubFactory(OrderFactory)
    book = factory.SubFactory(BookFactory)
    price = factory.SelfAttribute('book.price')
    quantity = 1