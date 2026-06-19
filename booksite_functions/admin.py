from django.contrib import admin
# Register your models here.
from .models import Book, Category, Order, OrderItem

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



class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['book']
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'first_name', 'last_name', 'email', 'paid', 'created_at', 'updated_at']
    list_filter = ['paid', 'created_at', 'updated_at']
    inlines = [OrderItemInline]