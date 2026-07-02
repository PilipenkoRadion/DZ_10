from decimal import Decimal

from django.test import TestCase
from django.contrib.auth import get_user_model

from booksite_functions.models import Category, Book, Order, OrderItem

User = get_user_model()


class CategoryModelTest(TestCase):
    # Generated with AI, reviewed and modified

    def setUp(self):
        # Настройка тестовых данных для категории
        self.category = Category.objects.create(name="Ð¤Ð°Ð½Ñ‚Ð°ÑÑ‚Ð¸ÐºÐ°", slug="fantasy")

    def test_str_returns_name(self):
        # Generated with AI, reviewed and modified
        # Проверка, что строковое представление категории возвращает ее название
        self.assertEqual(str(self.category), "Ð¤Ð°Ð½Ñ‚Ð°ÑÑ‚Ð¸ÐºÐ°")

    def test_slug_is_unique(self):
        # Generated with AI, reviewed and modified
        # Проверка уникальности поля slug (повторный slug должен вызывать ошибку)
        with self.assertRaises(Exception):
            Category.objects.create(name="Ð†Ð½ÑˆÐ°", slug="fantasy")

    def test_verbose_name_plural(self):
        # Generated with AI, reviewed and modified
        # Проверка правильности отображения множественного числа имени модели в админке
        self.assertEqual(Category._meta.verbose_name_plural, "Categories")


class BookModelTest(TestCase):
    # Generated with AI, reviewed and modified

    def setUp(self):
        # Настройка тестовой категории и книги с базовыми параметрами
        self.category = Category.objects.create(name="Ð”ÐµÑ‚ÐµÐºÑ‚Ð¸Ð²", slug="detective")
        self.book = Book.objects.create(
            title="Ð¢ÐµÑÑ‚Ð¾Ð²Ð° ÐºÐ½Ð¸Ð³Ð°",
            author="Ð¢ÐµÑÑ‚Ð¾Ð²Ð¸Ð¹ Ð°Ð²Ñ‚Ð¾Ñ€",
            price=Decimal("199.99"),
            description="ÐšÐ¾Ñ€Ð¾Ñ‚ÐºÐ¸Ð¹ Ð¾Ð¿Ð¸Ñ ÐºÐ½Ð¸Ð³Ð¸",
            stock="y",
            category=self.category,
        )

    def test_str_returns_title(self):
        # Generated with AI, reviewed and modified
        # Проверка, что строковое представление книги возвращает ее название
        self.assertEqual(str(self.book), "Ð¢ÐµÑÑ‚Ð¾Ð²Ð° ÐºÐ½Ð¸Ð³Ð°")

    def test_default_stock_is_in_stock(self):
        # Generated with AI, reviewed and modified
        # Проверка, что по умолчанию книга создается со статусом "в наличии" ('y')
        book = Book.objects.create(
            title="Ð”Ñ€ÑƒÐ³Ð° ÐºÐ½Ð¸Ð³Ð°",
            author="ÐÐ²Ñ‚Ð¾Ñ€ 2",
            price=Decimal("50.00"),
            description="ÐžÐ¿Ð¸Ñ",
            category=self.category,
        )
        self.assertEqual(book.stock, "y")

    def test_price_is_decimal(self):
        # Generated with AI, reviewed and modified
        # Проверка, что цена книги сохраняется и считывается как объект Decimal
        self.assertEqual(self.book.price, Decimal("199.99"))

    def test_book_linked_to_category(self):
        # Generated with AI, reviewed and modified
        # Проверка связи "многие к одному": книга должна присутствовать в выборке связанной категории
        self.assertIn(self.book, self.category.books.all())

    def test_category_can_be_null(self):
        # Generated with AI, reviewed and modified
        # Проверка, что книга может существовать без указания категории (поле может быть null)
        book = Book.objects.create(
            title="Ð‘ÐµÐ· ÐºÐ°Ñ‚ÐµÐ³Ð¾Ñ€Ñ–Ñ—",
            author="ÐÐ²Ñ‚Ð¾Ñ€",
            price=Decimal("10.00"),
            description="ÐžÐ¿Ð¸Ñ",
            category=None,
        )
        self.assertIsNone(book.category)


class OrderModelTest(TestCase):
    # Generated with AI, reviewed and modified

    def setUp(self):
        # Подготовка данных для заказа: создание категории, книг, самого заказа и позиций внутри него
        self.category = Category.objects.create(name="Ð Ð¾Ð¼Ð°Ð½", slug="roman")
        self.book1 = Book.objects.create(
            title="ÐšÐ½Ð¸Ð³Ð° 1", author="ÐÐ²Ñ‚Ð¾Ñ€ 1", price=Decimal("100.00"),
            description="ÐžÐ¿Ð¸Ñ 1", category=self.category,
        )
        self.book2 = Book.objects.create(
            title="ÐšÐ½Ð¸Ð³Ð° 2", author="ÐÐ²Ñ‚Ð¾Ñ€ 2", price=Decimal("50.00"),
            description="ÐžÐ¿Ð¸Ñ 2", category=self.category,
        )
        self.order = Order.objects.create(
            first_name="Ð†Ð²Ð°Ð½", last_name="ÐŸÐµÑ‚Ñ€ÐµÐ½ÐºÐ¾", email="ivan@example.com"
        )
        OrderItem.objects.create(order=self.order, book=self.book1, price=Decimal("100.00"), quantity=2)
        OrderItem.objects.create(order=self.order, book=self.book2, price=Decimal("50.00"), quantity=1)

    def test_str_returns_order_number(self):
        # Generated with AI, reviewed and modified
        # Проверка, что строковое представление заказа возвращает корректную форму с ID заказа
        self.assertEqual(str(self.order), f"Замовлення №{self.order.id}")

    def test_default_paid_is_false(self):
        # Generated with AI, reviewed and modified
        # Проверка, что новый заказ по умолчанию создается со статусом "не оплачен"
        self.assertFalse(self.order.paid)

    def test_get_total_cost(self):
        # Generated with AI, reviewed and modified
        # Проверка расчета общей стоимости заказа: (100 * 2) + (50 * 1) = 250
        self.assertEqual(self.order.get_total_cost(), Decimal("250.00"))

    def test_order_ordering_by_created_at_desc(self):
        # Generated with AI, reviewed and modified
        # Проверка сортировки заказов: более новые заказы должны идти первыми (сортировка по убыванию даты)
        second_order = Order.objects.create(
            first_name="ÐœÐ°Ñ€Ñ–Ñ", last_name="ÐšÐ¾Ð²Ð°Ð»ÑŒ", email="maria@example.com"
        )
        orders = list(Order.objects.all())
        self.assertEqual(orders[0], second_order)

    def test_user_is_optional(self):
        # Generated with AI, reviewed and modified
        # Проверка, что поле пользователя в заказе является необязательным (может быть совершено гостем)
        self.assertIsNone(self.order.user)


class OrderItemModelTest(TestCase):
    # Generated with AI, reviewed and modified

    def setUp(self):
        # Подготовка данных для тестирования отдельной позиции в заказе
        self.category = Category.objects.create(name="ÐÐ°ÑƒÐºÐ°", slug="science")
        self.book = Book.objects.create(
            title="ÐšÐ½Ð¸Ð³Ð°", author="ÐÐ²Ñ‚Ð¾Ñ€", price=Decimal("30.00"),
            description="ÐžÐ¿Ð¸Ñ", category=self.category,
        )
        self.order = Order.objects.create(
            first_name="ÐžÐ»ÐµÐ³", last_name="Ð¡Ð¸Ð´Ð¾Ñ€ÐµÐ½ÐºÐ¾", email="oleg@example.com"
        )
        self.item = OrderItem.objects.create(
            order=self.order, book=self.book, price=Decimal("30.00"), quantity=3
        )

    def test_get_cost(self):
        # Generated with AI, reviewed and modified
        # Проверка расчета стоимости одной позиции: цена книги * количество (30.00 * 3 = 90.00)
        self.assertEqual(self.item.get_cost(), Decimal("90.00"))

    def test_default_quantity_is_one(self):
        # Generated with AI, reviewed and modified
        # Проверка, что если количество книг в позиции не указано, оно автоматически становится равным 1
        item = OrderItem.objects.create(order=self.order, book=self.book, price=Decimal("30.00"))
        self.assertEqual(item.quantity, 1)

    def test_str_returns_id(self):
        # Generated with AI, reviewed and modified
        # Проверка, что строковое представление позиции заказа возвращает строковый ID этой записи
        self.assertEqual(str(self.item), str(self.item.id))

    def test_item_linked_to_order(self):
        # Generated with AI, reviewed and modified
        # Проверка связи позиции с главным заказом через связанное имя (related_name)
        self.assertIn(self.item, self.order.items.all())