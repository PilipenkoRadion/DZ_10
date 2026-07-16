from decimal import Decimal

from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Book, Category, Order, OrderItem

User = get_user_model()


class BaseAPITestCase(APITestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Фантастика", slug="fantasy")
        self.other_category = Category.objects.create(name="Проза", slug="prose")

        self.book1 = Book.objects.create(
            title="Дюна",
            author="Френк Герберт",
            price=Decimal("250.00"),
            description="Класика наукової фантастики",
            stock="y",
            category=self.category,
        )
        self.book2 = Book.objects.create(
            title="1984",
            author="Джордж Орвелл",
            price=Decimal("150.00"),
            description="Антиутопія",
            stock="n",
            category=self.other_category,
        )

        self.user = User.objects.create_user(
            username="reader", password="StrongPass123", email="reader@example.com"
        )
        self.other_user = User.objects.create_user(
            username="reader2", password="StrongPass123", email="reader2@example.com"
        )
        self.admin = User.objects.create_superuser(
            username="admin", password="AdminPass123", email="admin@example.com"
        )


class CategoryAPITests(BaseAPITestCase):
    def test_list_categories_public(self):
        url = reverse("category-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)

    def test_retrieve_category_by_slug(self):
        url = reverse("category-detail", args=[self.category.slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Фантастика")

    def test_create_category_anonymous_forbidden(self):
        url = reverse("category-list")
        response = self.client.post(url, {"name": "Детектив", "slug": "detective"})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_category_regular_user_forbidden(self):
        self.client.force_authenticate(user=self.user)
        url = reverse("category-list")
        response = self.client.post(url, {"name": "Детектив", "slug": "detective"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_category_admin_allowed(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse("category-list")
        response = self.client.post(url, {"name": "Детектив", "slug": "detective"})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Category.objects.count(), 3)

    def test_delete_category_admin_allowed(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse("category-detail", args=[self.other_category.slug])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class BookAPITests(BaseAPITestCase):
    def test_list_books(self):
        url = reverse("book-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)

    def test_retrieve_book(self):
        url = reverse("book-detail", args=[self.book1.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Дюна")

    def test_create_book_anonymous_forbidden(self):
        url = reverse("book-list")
        response = self.client.post(
            url,
            {
                "title": "Нова книга",
                "author": "Автор",
                "price": "100.00",
                "description": "Опис",
                "stock": "y",
                "category_id": self.category.id,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_book_admin_allowed(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse("book-list")
        response = self.client.post(
            url,
            {
                "title": "Нова книга",
                "author": "Автор",
                "price": "100.00",
                "description": "Опис",
                "stock": "y",
                "category_id": self.category.id,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Book.objects.count(), 3)

    def test_update_book_admin_allowed(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse("book-detail", args=[self.book1.id])
        response = self.client.patch(url, {"price": "300.00"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.book1.refresh_from_db()
        self.assertEqual(self.book1.price, Decimal("300.00"))

    def test_delete_book_regular_user_forbidden(self):
        self.client.force_authenticate(user=self.user)
        url = reverse("book-detail", args=[self.book1.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_filter_books_by_category(self):
        url = reverse("book-list")
        response = self.client.get(url, {"category": "fantasy"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["title"], "Дюна")

    def test_filter_books_by_stock(self):
        url = reverse("book-list")
        response = self.client.get(url, {"stock": "n"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["title"], "1984")

    def test_filter_books_by_price_range(self):
        url = reverse("book-list")
        response = self.client.get(url, {"min_price": "200", "max_price": "300"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["title"], "Дюна")

    def test_search_books(self):
        url = reverse("book-list")
        response = self.client.get(url, {"search": "Орвелл"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_pagination_page_size(self):
        for i in range(25):
            Book.objects.create(
                title=f"Книга {i}",
                author="Автор",
                price=Decimal("50.00"),
                description="Опис",
                stock="y",
                category=self.category,
            )
        url = reverse("book-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 20)
        self.assertIsNotNone(response.data["next"])


class OrderAPITests(BaseAPITestCase):
    def _order_payload(self):
        return {
            "first_name": "Іван",
            "last_name": "Іваненко",
            "email": "ivan@example.com",
            "items": [
                {"book_id": self.book1.id, "price": "250.00", "quantity": 2},
            ],
        }

    def test_create_order_requires_authentication(self):
        url = reverse("order-list")
        response = self.client.post(url, self._order_payload(), format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_order_authenticated(self):
        self.client.force_authenticate(user=self.user)
        url = reverse("order-list")
        response = self.client.post(url, self._order_payload(), format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        order = Order.objects.get(id=response.data["id"])
        self.assertEqual(order.user, self.user)
        self.assertEqual(order.items.count(), 1)

    def test_user_sees_only_own_orders(self):
        Order.objects.create(user=self.user, first_name="A", last_name="B", email="a@b.com")
        Order.objects.create(user=self.other_user, first_name="C", last_name="D", email="c@d.com")
        self.client.force_authenticate(user=self.user)
        url = reverse("order-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_admin_sees_all_orders(self):
        Order.objects.create(user=self.user, first_name="A", last_name="B", email="a@b.com")
        Order.objects.create(user=self.other_user, first_name="C", last_name="D", email="c@d.com")
        self.client.force_authenticate(user=self.admin)
        url = reverse("order-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)

    def test_user_cannot_update_other_users_order(self):
        order = Order.objects.create(
            user=self.other_user, first_name="C", last_name="D", email="c@d.com"
        )
        self.client.force_authenticate(user=self.user)
        url = reverse("order-detail", args=[order.id])
        response = self.client.patch(url, {"first_name": "Змінено"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_owner_can_update_own_order(self):
        order = Order.objects.create(
            user=self.user, first_name="Іван", last_name="Іваненко", email="ivan@example.com"
        )
        self.client.force_authenticate(user=self.user)
        url = reverse("order-detail", args=[order.id])
        response = self.client.patch(url, {"first_name": "Петро"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        order.refresh_from_db()
        self.assertEqual(order.first_name, "Петро")

    def test_filter_orders_by_paid_status(self):
        Order.objects.create(
            user=self.user, first_name="A", last_name="B", email="a@b.com", paid=True
        )
        Order.objects.create(
            user=self.user, first_name="C", last_name="D", email="c@d.com", paid=False
        )
        self.client.force_authenticate(user=self.user)
        url = reverse("order-list")
        response = self.client.get(url, {"paid": "true"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_mark_paid_action_admin_only(self):
        order = Order.objects.create(
            user=self.user, first_name="A", last_name="B", email="a@b.com"
        )
        self.client.force_authenticate(user=self.user)
        url = reverse("order-mark-paid", args=[order.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.admin)
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        order.refresh_from_db()
        self.assertTrue(order.paid)


class CartAPITests(BaseAPITestCase):
    def test_cart_starts_empty(self):
        url = reverse("cart-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["items"], [])

    def test_add_item_to_cart(self):
        add_url = reverse("cart-add")
        response = self.client.post(add_url, {"book_id": self.book1.id, "quantity": 2})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        list_url = reverse("cart-list")
        response = self.client.get(list_url)
        self.assertEqual(len(response.data["items"]), 1)
        self.assertEqual(response.data["items"][0]["quantity"], 2)

    def test_remove_item_from_cart(self):
        add_url = reverse("cart-add")
        self.client.post(add_url, {"book_id": self.book1.id, "quantity": 1})

        remove_url = reverse("cart-remove")
        response = self.client.post(remove_url, {"book_id": self.book1.id})
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        list_url = reverse("cart-list")
        response = self.client.get(list_url)
        self.assertEqual(response.data["items"], [])

    def test_clear_cart(self):
        add_url = reverse("cart-add")
        self.client.post(add_url, {"book_id": self.book1.id, "quantity": 1})
        self.client.post(add_url, {"book_id": self.book2.id, "quantity": 3})

        clear_url = reverse("cart-clear")
        response = self.client.post(clear_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        list_url = reverse("cart-list")
        response = self.client.get(list_url)
        self.assertEqual(response.data["items"], [])


class JWTAuthTests(BaseAPITestCase):
    def test_obtain_token_pair_valid_credentials(self):
        url = reverse("token_obtain_pair")
        response = self.client.post(
            url, {"username": "reader", "password": "StrongPass123"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_obtain_token_invalid_credentials(self):
        url = reverse("token_obtain_pair")
        response = self.client.post(
            url, {"username": "reader", "password": "WrongPassword"}
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_token(self):
        obtain_url = reverse("token_obtain_pair")
        obtain_response = self.client.post(
            obtain_url, {"username": "reader", "password": "StrongPass123"}
        )
        refresh_url = reverse("token_refresh")
        response = self.client.post(
            refresh_url, {"refresh": obtain_response.data["refresh"]}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_verify_token(self):
        obtain_url = reverse("token_obtain_pair")
        obtain_response = self.client.post(
            obtain_url, {"username": "reader", "password": "StrongPass123"}
        )
        verify_url = reverse("token_verify")
        response = self.client.post(
            verify_url, {"token": obtain_response.data["access"]}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_access_protected_endpoint_with_jwt(self):
        obtain_url = reverse("token_obtain_pair")
        obtain_response = self.client.post(
            obtain_url, {"username": "reader", "password": "StrongPass123"}
        )
        access_token = obtain_response.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        url = reverse("order-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_access_protected_endpoint_without_token(self):
        url = reverse("order-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)