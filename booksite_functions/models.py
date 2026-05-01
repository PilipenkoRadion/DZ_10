from django.db import models

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
    author = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=150)
    stock = models.CharField(max_length=1, choices=STOCK_CHOICES, default="y")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="books", null=True)
