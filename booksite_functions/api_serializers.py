from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Book, Category, Order, OrderItem

User = get_user_model()


class UserShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email"]


class CategorySerializer(serializers.ModelSerializer):
    book_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Category
        fields = ["id", "name", "slug", "book_count"]


class BookSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), source="category", write_only=True
    )
    stock_display = serializers.CharField(source="get_stock_display", read_only=True)

    class Meta:
        model = Book
        fields = [
            "id",
            "title",
            "photo",
            "author",
            "price",
            "description",
            "stock",
            "stock_display",
            "category",
            "category_id",
        ]


class BookShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ["id", "title", "author", "price"]


class OrderItemSerializer(serializers.ModelSerializer):
    book = BookShortSerializer(read_only=True)
    book_id = serializers.PrimaryKeyRelatedField(
        queryset=Book.objects.all(), source="book", write_only=True
    )
    cost = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ["id", "book", "book_id", "price", "quantity", "cost"]

    def get_cost(self, obj):
        return obj.get_cost()


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    user = UserShortSerializer(read_only=True)
    total_cost = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id",
            "user",
            "first_name",
            "last_name",
            "email",
            "created_at",
            "updated_at",
            "paid",
            "stripe_id",
            "items",
            "total_cost",
        ]
        read_only_fields = ["paid", "stripe_id", "created_at", "updated_at"]

    def get_total_cost(self, obj):
        return obj.get_total_cost()

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("Замовлення повинно містити хоча б один товар")
        return value

    def create(self, validated_data):
        items_data = validated_data.pop("items")
        order = Order.objects.create(**validated_data)
        for item_data in items_data:
            OrderItem.objects.create(order=order, **item_data)
        return order

    def update(self, instance, validated_data):
        items_data = validated_data.pop("items", None)
        instance = super().update(instance, validated_data)
        if items_data is not None:
            instance.items.all().delete()
            for item_data in items_data:
                OrderItem.objects.create(order=instance, **item_data)
        return instance


class OrderListSerializer(serializers.ModelSerializer):
    total_cost = serializers.SerializerMethodField()
    items_count = serializers.IntegerField(source="items.count", read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "first_name",
            "last_name",
            "email",
            "created_at",
            "paid",
            "items_count",
            "total_cost",
        ]

    def get_total_cost(self, obj):
        return obj.get_total_cost()


class CartItemInSerializer(serializers.Serializer):
    book_id = serializers.IntegerField()
    quantity = serializers.IntegerField(default=1, min_value=1)


class CartItemOutSerializer(serializers.Serializer):
    book = BookShortSerializer()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    quantity = serializers.IntegerField()
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2)


class CartRemoveSerializer(serializers.Serializer):
    book_id = serializers.IntegerField()