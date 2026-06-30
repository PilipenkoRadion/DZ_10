from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

app_name = "books"

urlpatterns = [
    path("step1/", views.async_step1, name="step1"),
    path("step2/", views.step2, name="step2"),
    path("", views.home, name="home"),
    path("books/", views.async_book_list, name="book-list"),
    path("books/<int:pk>/", views.async_book_detail, name="book-detail"),
    path("books/create/", views.BookCreateView.as_view(), name="book-create"),
    path("books/<int:pk>/update/", views.BookUpdateView.as_view(), name="book-update"),
    path("books/<int:pk>/delete/", views.BookDeleteView.as_view(), name="book-delete"),
    path("login/", views.login_views, name="login"),
    path("register/", views.register_views, name="register"),
    path("logout/", views.logout_views, name="logout"),
    path("cart/", views.cart_detail, name="cart_detail"),
    path("cart/add/<int:book_id>/", views.cart_add, name="cart_add"),
    path("cart/remove/<int:book_id>/", views.cart_remove, name="cart_remove"),
    path("order/create/", views.order_create, name="order_create"),
    path("payment/process/<int:order_id>/", views.payment_process, name="payment_process"),
    path("payment/success/", views.payment_success, name="payment_success"),
    path("payment/cancel/", views.payment_cancel, name="payment_cancel"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)