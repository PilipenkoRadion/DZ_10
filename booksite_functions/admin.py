from django.contrib import admin
# Register your models here.
from .models import Book, Category

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    model = Book

    fieldsets = (
        ("Основное", {"fields": ("title", "author", "category")}),
        ("Детали", {"fields": ("price", "stock", "description")}),
    )

class BookInline(admin.TabularInline):
    model = Book
    extra = 1

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    model = Category
    list_display = ["name", "slug"]
    prepopulated_fields = {"slug": ("name", )}
    inlines = [BookInline]


