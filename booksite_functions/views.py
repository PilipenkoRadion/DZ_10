from django.shortcuts import render, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
# Create your views here.
from .models import Book, Category
from django.contrib import messages as django_messages
from django.db.models import Q, Count, Avg
from django.urls import reverse_lazy
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from .forms import Step1Form, LoginForm, RegisterForm
import logging
logger = logging.getLogger("booksite_functions")


class BookListView(ListView):
    model = Book
    template_name = "book_list.html"
    context_object_name = "books_l"
    paginate_by = 67

    def get_queryset(self):
        queryset = Book.objects.all()
        category = self.request.GET.get("category")
        if category:
            queryset = queryset.filter(category__slug=category)
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.objects.all()
        return context

class BookDetailView(DetailView):
    model = Book
    template_name = "book_detail.html"
    context_object_name = "books_d"

class BookCreateView(CreateView):
    permission_required = "booksite_functions.create_book"
    model = Book
    template_name = "book_create.html"
    fields = ["title", "author", "price", "description", "stock", "category"]
    success_url = reverse_lazy("books:book-list")

class BookUpdateView(UpdateView):
    permission_required = "booksite_functions.update_book"
    model = Book
    template_name = "book_update.html"
    fields = ["title", "author", "price", "description", "stock", "category", "photo"]
    success_url = reverse_lazy("books:book-list")

class BookDeleteView(DeleteView):
    permission_required = "booksite_functions.delete_book"
    model = Book
    template_name = "book_delete.html"
    success_url = reverse_lazy("books:book-list")



def register_views(request):
    if request.user.is_authenticated:
        return redirect("books:home")
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        logger.info("Новый пользователь зарегестрирован: %s", user.username)
        return redirect("books:home")
    return render(request, "register.html", {"form": form})

def login_views(request):
    if request.user.is_authenticated:
        return redirect("books:home")
    form = LoginForm(data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request,  form.get_user())
        logger.info("Вы успешно вошли %s", form.get_user())
        return redirect(request.GET.get("next", "books:home"))
    return render(request, "login.html", {"form": form})
def logout_views(request):
    if request.method == "POST":
        logger.info("Вы успешно вышли из вашего аккаунта! %s", request.user)
        logout(request)
    return redirect("books:home")
    pass






def step1(request):
    form = Step1Form()
    if request.method == "POST":
        form = Step1Form(request.POST)
        if form.is_valid():
            request.session["reg_title"] = form.cleaned_data["title"]
            request.session["reg_author"] = form.cleaned_data["author"]
            request.session["reg_price"] = str(form.cleaned_data["price"])
            return redirect("books:step2")
    return render(request, "step1.html", {"form": form})












# def step1(request):
#     if request.method == "POST":
#         title = request.POST.get("title")
#         author = request.POST.get("author")
#         price = request.POST.get("price")
        
#         if not title:
#             django_messages.error(request, "Введие названия книги")
#             return redirect("step1")
        
#         if not author:
#             django_messages.error(request, "Введите автора книги")
#             return redirect("step1")
        
#         if not price:
#             django_messages.error(request, "Введите цену")
#             return redirect("step1")
        
#         if len(title) > 20:
#             django_messages.error(request, "Название книги может иметь макс. 20 символов")
#             return redirect("step1")
        
#         request.session["reg_title"] = title
#         request.session["reg_author"] = author
#         request.session["reg_price"] = price
#         return redirect("step2")
#     return render(request, "step1.html")



def step2(request):
    steps_keys = ["reg_title", "reg_author", "reg_price"]
    if not all(k in request.session for k in steps_keys):
        return redirect("books:step1")
    
    if request.method == "POST":
        photo = request.FILES.get("photo")
        description = request.POST.get("description")
        stock = request.POST.get("stock")
        category_id = request.POST.get("category")


        if not description:
            django_messages.error(request, "Введите описание книги")
            return redirect("books:step2")

        if not stock:
            django_messages.error(request, "Укажите наличее книг")
            return redirect("books:step2")
        
        if not category_id:
            django_messages.error(request, "Укажите категорию книг")
            return redirect("books:step2")
        
        try:
            category_obj = Category.objects.get(id=category_id)
        except Category.DoesNotExist:
            django_messages.error(request, "Выбранная категория не существует")
            return redirect("books:step2")
        
        if len(description) > 150:
            django_messages.error(request, "Описание не может превышать 150 символов")
            return redirect("books:step2")
        

    

        Book.objects.create(
            title=request.session["reg_title"],
            author=request.session["reg_author"],
            price=request.session["reg_price"],
            description=description,
            stock=stock,
            category=category_obj,
            photo=photo
        )

        for i in steps_keys:
            del request.session[i]
        django_messages.success(request, "Вы успешно добавили книгу в каталог!")
        return redirect("books:home")
    
    categories = Category.objects.all()
    return render(request, "step2.html", {"categories": categories})


def home(request):
    books = Book.objects.all()

    stock_filter = request.GET.get("stock")
    if stock_filter:
        books = books.filter(stock=stock_filter)

    category_filter = request.GET.get("category")
    if category_filter:
        books = books.filter(category__id=category_filter)

    search = request.GET.get("search")
    if search:
        books = books.filter(Q(title__icontains=search) | Q(author__icontains=search))
    
    categories = Category.objects.annotate(book_count=Count("books"))
    return render(request, "home.html", {"books": books, "categories": categories})















