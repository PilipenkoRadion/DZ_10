from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

app_name = "books"

urlpatterns = [
    path("step1/", views.step1, name="step1"),
    path("step2/", views.step2, name="step2"),
    path("", views.home, name="home"),
    path("books/", views.BookListView.as_view(), name="book-list"),
    path("books/<int:pk>/", views.BookDetailView.as_view(), name="book-detail"),
    path("books/create/", views.BookCreateView.as_view(), name="book-create"),
    path("books/<int:pk>/update/", views.BookUpdateView.as_view(), name="book-update"),
    path("books/<int:pk>/delete/", views.BookDeleteView.as_view(), name="book-delete"),
    path("login/", views.login_views, name="login"),
    path("register/", views.register_views, name="register"),
    path("logout/", views.logout_views, name="logout"),
] 

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)