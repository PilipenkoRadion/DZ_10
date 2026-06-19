from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

# Create your models here.


class Category(models.Model):
    name = models.CharField(max_length=20)
    slug = models.SlugField(max_length=20, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Categories" 

class Book(models.Model):
    STOCK_CHOICES = [
        ("y", "in_stock"),
        ("n", "out_of_stock")
    ]
    title = models.CharField(max_length=20)
    photo = models.ImageField(upload_to="books/", blank=True, null=True)
    author = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=150)
    stock = models.CharField(max_length=1, choices=STOCK_CHOICES, default="y")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="books", null=True)


class CustomUser(AbstractUser):
    class Role(models.TextChoices):
        VIEWER = "viewer", "Читатель"
        EDITOR = "editor", "Редактор"
        ADMIN  = "admin",  "Админ"

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.VIEWER,
    )

    @property
    def is_editor(self):
        return self.role in (self.Role.EDITOR, self.Role.ADMIN)

    def __str__(self):
        return self.username


class Order(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='orders'
    )
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid = models.BooleanField(default=False)
    stripe_id = models.CharField(max_length=250, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f'Замовлення №{self.id}'

    def get_total_cost(self):
        return sum(item.get_cost() for item in self.items.all())


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='order_items')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return str(self.id)

    def get_cost(self):
        return self.price * self.quantity