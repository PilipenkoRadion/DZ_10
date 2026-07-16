from django.db.models import Count
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, permissions, status, filters as drf_filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle, ScopedRateThrottle
from django_filters.rest_framework import DjangoFilterBackend

from .models import Book, Category, Order
from .cart import Cart
from .api_serializers import (
    BookSerializer,
    CategorySerializer,
    OrderSerializer,
    OrderListSerializer,
    CartItemInSerializer,
    CartItemOutSerializer,
    CartRemoveSerializer,
)
from .api_permissions import IsOwnerOrReadOnly, IsAdminOrReadOnly
from .api_filters import BookFilter, OrderFilter


class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [drf_filters.SearchFilter, drf_filters.OrderingFilter]
    search_fields = ["name"]
    ordering_fields = ["name"]
    lookup_field = "slug"

    def get_queryset(self):
        return Category.objects.annotate(book_count=Count("books")).order_by("name")


class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.select_related("category").all()
    serializer_class = BookSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, drf_filters.SearchFilter, drf_filters.OrderingFilter]
    filterset_class = BookFilter
    search_fields = ["title", "author", "description"]
    ordering_fields = ["price", "title"]
    throttle_classes = [UserRateThrottle, AnonRateThrottle]


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = OrderFilter

    def get_queryset(self):
        user = self.request.user
        qs = Order.objects.prefetch_related("items__book")
        if user.is_staff:
            return qs
        return qs.filter(user=user)

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer
        return OrderSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAdminUser])
    def mark_paid(self, request, pk=None):
        order = self.get_object()
        order.paid = True
        order.save()
        return Response(OrderSerializer(order, context={"request": request}).data)


class CartViewSet(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "cart"

    def list(self, request):
        cart = Cart(request)
        items = [
            {
                "book": item["book"],
                "price": item["price"],
                "quantity": item["quantity"],
                "total_price": item["price"] * item["quantity"],
            }
            for item in cart
        ]
        serializer = CartItemOutSerializer(items, many=True)
        total_price = sum(i["total_price"] for i in items)
        return Response({"items": serializer.data, "total_price": total_price})

    @action(detail=False, methods=["post"])
    def add(self, request):
        serializer = CartItemInSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        book = get_object_or_404(Book, id=serializer.validated_data["book_id"])
        cart = Cart(request)
        cart.add(
            book=book,
            quantity=serializer.validated_data["quantity"],
            override_quantity=False,
        )
        return Response(status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["post"])
    def remove(self, request):
        serializer = CartRemoveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        book = get_object_or_404(Book, id=serializer.validated_data["book_id"])
        cart = Cart(request)
        cart.remove(book)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["post"])
    def clear(self, request):
        cart = Cart(request)
        cart.clear()
        return Response(status=status.HTTP_204_NO_CONTENT)