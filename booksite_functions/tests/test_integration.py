import pytest
from unittest.mock import patch, MagicMock
from django.urls import reverse
from booksite_functions.models import Order
from .factories import BookFactory, CategoryFactory, UserFactory, OrderFactory


@pytest.mark.django_db
def test_async_book_list_view(client, book):
    response = client.get(reverse('books:book-list'))
    assert response.status_code == 200
    assert book in response.context['books_l']


@pytest.mark.django_db
def test_async_book_list_filter_by_category(client, category):
    matching = BookFactory(category=category)
    other_cat = CategoryFactory()
    BookFactory(category=other_cat)
    response = client.get(reverse('books:book-list'), {'category': category.slug})
    assert matching in response.context['books_l']


@pytest.mark.django_db
def test_async_book_detail_view(client, book):
    response = client.get(reverse('books:book-detail', kwargs={'pk': book.pk}))
    assert response.status_code == 200
    assert response.context['books_d'] == book


@pytest.mark.django_db
def test_async_book_detail_view_404(client):
    response = client.get(reverse('books:book-detail', kwargs={'pk': 99999}))
    assert response.status_code == 404


@pytest.mark.django_db
def test_home_view_search(client, category):
    target = BookFactory(category=category, title='Unique Searchable Title')
    other = BookFactory(category=category, title='Something Else')
    response = client.get(reverse('books:home'), {'search': 'Unique Searchable'})
    assert target in response.context['books']
    assert other not in response.context['books']


@pytest.mark.django_db
def test_home_view_filter_by_stock(client, category):
    in_stock = BookFactory(category=category, stock=5)
    out_of_stock = BookFactory(category=category, stock=0)
    response = client.get(reverse('books:home'), {'stock': 0})
    assert out_of_stock in response.context['books']
    assert in_stock not in response.context['books']


@pytest.mark.django_db
def test_register_view_creates_user_and_logs_in(client):
    response = client.post(reverse('books:register'), {
        'username': 'flowuser',
        'email': 'flowuser@example.com',
        'password1': 'StrongPass123!',
        'password2': 'StrongPass123!',
    })
    assert response.status_code == 302
    from django.contrib.auth import get_user_model
    assert get_user_model().objects.filter(username='flowuser').exists()


@pytest.mark.django_db
def test_register_view_redirects_authenticated_user(client, user):
    client.force_login(user)
    response = client.get(reverse('books:register'))
    assert response.status_code == 302


@pytest.mark.django_db
def test_login_view_success(client, user):
    response = client.post(reverse('books:login'), {
        'username': user.username,
        'password': 'TestPass123!',
    })
    assert response.status_code == 302


@pytest.mark.django_db
def test_login_view_invalid_credentials(client, user):
    response = client.post(reverse('books:login'), {
        'username': user.username,
        'password': 'WrongPass',
    })
    assert response.status_code == 200


@pytest.mark.django_db
def test_logout_view(client, user):
    client.force_login(user)
    response = client.post(reverse('books:logout'))
    assert response.status_code == 302


@pytest.mark.django_db
def test_cart_add_view(client, book):
    response = client.get(reverse('books:cart_add', kwargs={'book_id': book.id}))
    assert response.status_code == 302
    response2 = client.get(reverse('books:cart_detail'))
    assert response2.status_code == 200


@pytest.mark.django_db
def test_cart_remove_view(client, book):
    client.get(reverse('books:cart_add', kwargs={'book_id': book.id}))
    response = client.get(reverse('books:cart_remove', kwargs={'book_id': book.id}))
    assert response.status_code == 302


@pytest.mark.django_db
def test_cart_detail_view_empty(client):
    response = client.get(reverse('books:cart_detail'))
    assert response.status_code == 200


@pytest.mark.django_db
def test_order_create_redirects_when_cart_empty(client):
    response = client.post(reverse('books:order_create'), {
        'first_name': 'Radion',
        'last_name': 'Pylypenko',
        'email': 'radion@example.com',
    })
    assert response.status_code == 302
    assert response.url == reverse('books:book-list')


@pytest.mark.django_db
@patch('booksite_functions.views.send_mail')
def test_order_create_creates_order_and_sends_email(mock_email, client, cart_with_book):
    response = client.post(reverse('books:order_create'), {
        'first_name': 'Radion',
        'last_name': 'Pylypenko',
        'email': 'radion@example.com',
    })
    assert response.status_code == 302
    assert Order.objects.filter(email='radion@example.com').exists()
    assert mock_email.called


@pytest.mark.django_db
@patch('stripe.checkout.Session.create')
@patch('booksite_functions.views.send_mail')
def test_full_checkout_flow_calls_stripe(mock_email, mock_stripe_session, client, cart_with_book):
    mock_stripe_session.return_value = MagicMock(
        id='cs_test_123',
        url='https://checkout.stripe.com/test',
    )

    create_response = client.post(reverse('books:order_create'), {
        'first_name': 'Radion',
        'last_name': 'Pylypenko',
        'email': 'radion@example.com',
    })
    assert create_response.status_code == 302

    payment_response = client.get(create_response.url)
    assert mock_stripe_session.called
    assert payment_response.status_code == 302
    assert payment_response.url == 'https://checkout.stripe.com/test'


@pytest.mark.django_db
def test_payment_success_marks_order_paid(client):
    order = OrderFactory(paid=False)
    response = client.get(reverse('books:payment_success'), {'order_id': order.id})
    order.refresh_from_db()
    assert order.paid is True
    assert response.status_code == 200


@pytest.mark.django_db
def test_payment_cancel_view(client):
    response = client.get(reverse('books:payment_cancel'))
    assert response.status_code == 200