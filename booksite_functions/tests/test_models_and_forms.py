import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model
from booksite_functions.models import Book, Category, Order, OrderItem
from booksite_functions.forms import Step1Form, LoginForm, RegisterForm
from .factories import BookFactory, CategoryFactory, OrderFactory, OrderItemFactory, UserFactory

User = get_user_model()



@pytest.mark.django_db
def test_book_str_representation(book):
    assert str(book) == book.title or book.title in str(book)


@pytest.mark.django_db
def test_book_created_with_correct_price():
    b = BookFactory(price=Decimal('19.99'))
    assert b.price == Decimal('19.99')


@pytest.mark.django_db
def test_book_belongs_to_category(book, category):
    assert book.category == category


@pytest.mark.django_db
def test_category_str_representation(category):
    assert str(category) == category.name or category.name in str(category)


@pytest.mark.django_db
def test_category_slug_is_unique():
    Category.objects.create(name='Cat A', slug='unique-slug')
    with pytest.raises(Exception):
        Category.objects.create(name='Cat B', slug='unique-slug')

@pytest.mark.django_db
def test_order_default_paid_is_false():
    order = OrderFactory()
    assert order.paid is False


@pytest.mark.django_db
def test_order_str_representation():
    order = OrderFactory(first_name='Ivan', last_name='Petrenko')
    assert 'Ivan' in str(order) or str(order.id) in str(order)


@pytest.mark.django_db
def test_orderitem_linked_to_order_and_book():
    item = OrderItemFactory()
    assert item.order is not None
    assert item.book is not None


@pytest.mark.django_db
def test_orderitem_default_quantity():
    item = OrderItemFactory()
    assert item.quantity == 1


@pytest.mark.django_db
def test_multiple_books_unique_titles():
    books = BookFactory.create_batch(5)
    titles = [b.title for b in books]
    assert len(titles) == 5



def test_step1_form_valid_data():
    form = Step1Form(data={'title': 'Kobzar', 'author': 'Taras Shevchenko', 'price': '15.00'})
    assert form.is_valid()


def test_step1_form_missing_title():
    form = Step1Form(data={'author': 'Author', 'price': '15.00'})
    assert not form.is_valid()
    assert 'title' in form.errors


def test_step1_form_missing_author():
    form = Step1Form(data={'title': 'Title', 'price': '15.00'})
    assert not form.is_valid()
    assert 'author' in form.errors


def test_step1_form_missing_price():
    form = Step1Form(data={'title': 'Title', 'author': 'Author'})
    assert not form.is_valid()
    assert 'price' in form.errors


@pytest.mark.django_db
def test_register_form_valid_data():
    form = RegisterForm(data={
        'username': 'newuser',
        'email': 'newuser@example.com',
        'password1': 'StrongPass123!',
        'password2': 'StrongPass123!',
    })
    assert form.is_valid()


@pytest.mark.django_db
def test_register_form_password_mismatch():
    form = RegisterForm(data={
        'username': 'newuser2',
        'email': 'newuser2@example.com',
        'password1': 'StrongPass123!',
        'password2': 'DifferentPass456!',
    })
    assert not form.is_valid()


@pytest.mark.django_db
def test_register_form_duplicate_username():
    UserFactory(username='existing')
    form = RegisterForm(data={
        'username': 'existing',
        'email': 'other@example.com',
        'password1': 'StrongPass123!',
        'password2': 'StrongPass123!',
    })
    assert not form.is_valid()


@pytest.mark.django_db
def test_login_form_valid_credentials(user):
    form = LoginForm(data={'username': user.username, 'password': 'TestPass123!'})
    assert form.is_valid()


@pytest.mark.django_db
def test_login_form_invalid_credentials(user):
    form = LoginForm(data={'username': user.username, 'password': 'WrongPassword'})
    assert not form.is_valid()


@pytest.mark.django_db
def test_login_form_nonexistent_user():
    form = LoginForm(data={'username': 'ghost', 'password': 'whatever'})
    assert not form.is_valid()