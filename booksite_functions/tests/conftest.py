import pytest
from .factories import UserFactory, BookFactory, CategoryFactory


@pytest.fixture
def user(db):
    return UserFactory()


@pytest.fixture
def category(db):
    return CategoryFactory()


@pytest.fixture
def book(db, category):
    return BookFactory(category=category, stock=5)


@pytest.fixture
def cart_with_book(client, book):
    """Кладёт книгу в корзину через сессию — ПОДГОНИ под реальный Cart.add()."""
    session = client.session
    session['cart'] = {
        str(book.id): {'quantity': 1, 'price': str(book.price)}
    }
    session.save()
    return book