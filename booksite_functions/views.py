from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from .models import Book, Category
from django.contrib import messages as django_messages
from django.db.models import Q, Count, Avg
from django.urls import reverse_lazy
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from .forms import Step1Form, LoginForm, RegisterForm
import logging
import stripe
from .models import Order, OrderItem, Book
from .cart import Cart
from django.conf import settings
from django.db import transaction
from django.urls import reverse
from django.core.mail import send_mail
from django.http import Http404, JsonResponse
from django.db import connections
from django.db.utils import OperationalError

logger = logging.getLogger("booksite_functions")

stripe.api_key = settings.STRIPE_SECRET_KEY


def health_check(request):
    db_ok = True
    try:
        connections['default'].cursor()
    except OperationalError:
        db_ok = False

    status = 200 if db_ok else 503
    return JsonResponse(
        {
            "status": "ok" if db_ok else "error",
            "database": db_ok,
        },
        status=status,
    )


class BookListView(ListView):
    model = Book
    template_name = "book_list.html"
    context_object_name = "books_l"
    paginate_by = 67

    def get_queryset(self):
        queryset = Book.objects.select_related("category").all()
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

    def get_queryset(self):
        return Book.objects.select_related("category")


class BookCreateView(PermissionRequiredMixin, CreateView):
    permission_required = "booksite_functions.create_book"
    model = Book
    template_name = "book_create.html"
    fields = ["title", "author", "price", "description", "stock", "category"]
    success_url = reverse_lazy("books:book-list")


class BookUpdateView(PermissionRequiredMixin, UpdateView):
    permission_required = "booksite_functions.update_book"
    model = Book
    template_name = "book_update.html"
    fields = ["title", "author", "price", "description", "stock", "category", "photo"]
    success_url = reverse_lazy("books:book-list")


class BookDeleteView(PermissionRequiredMixin, DeleteView):
    permission_required = "booksite_functions.delete_book"
    model = Book
    template_name = "book_delete.html"
    success_url = reverse_lazy("books:book-list")


async def async_book_list(request):
    category_slug = request.GET.get("category")
    if category_slug:
        books_queryset = Book.objects.select_related("category").filter(category__slug=category_slug)
    else:
        books_queryset = Book.objects.select_related("category").all()

    books = [b async for b in books_queryset]
    categories = [c async for c in Category.objects.all()]

    return render(request, "book_list.html", {
        "books_l": books,
        "categories": categories
    })


async def async_book_detail(request, pk):
    try:
        book = await Book.objects.select_related("category").aget(pk=pk)
    except Book.DoesNotExist:
        raise Http404("Book not found")

    return render(request, "book_detail.html", {"books_d": book})


async def async_step1(request):
    if request.method == "POST":
        form = Step1Form(request.POST)
        if form.is_valid():
            request.session["reg_title"] = form.cleaned_data["title"]
            request.session["reg_author"] = form.cleaned_data["author"]
            request.session["reg_price"] = str(form.cleaned_data["price"])
            return redirect("books:step2")
    else:
        form = Step1Form()

    return render(request, "step1.html", {"form": form})


def register_views(request):
    if request.user.is_authenticated:
        return redirect("books:home")
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        user.backend = 'django.contrib.auth.backends.ModelBackend'
        login(request, user)
        logger.info("Новый пользователь зарегестрирован: %s", user.username)
        return redirect("books:home")
    return render(request, "register.html", {"form": form})


def login_views(request):
    if request.user.is_authenticated:
        return redirect("books:home")
    form = LoginForm(data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        logger.info("Вы успешно вошли %s", form.get_user())
        return redirect(request.GET.get("next", "books:home"))
    return render(request, "login.html", {"form": form})


def logout_views(request):
    if request.method == "POST":
        logger.info("Вы успешно вышли из вашего аккаунта! %s", request.user)
        logout(request)
    return redirect("books:home")


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
    books = Book.objects.select_related("category").all()

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


def cart_add(request, book_id):
    cart = Cart(request)
    book = get_object_or_404(Book, id=book_id)
    cart.add(book=book, quantity=1, override_quantity=False)
    return redirect('books:cart_detail')


def cart_remove(request, book_id):
    cart = Cart(request)
    book = get_object_or_404(Book, id=book_id)
    cart.remove(book)
    return redirect('books:cart_detail')


def cart_detail(request):
    cart = Cart(request)
    return render(request, 'cart_detail.html', {'cart': cart})


def order_create(request):
    cart = Cart(request)
    if not cart:
        return redirect('books:book-list')

    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')

        try:
            with transaction.atomic():
                order = Order.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    first_name=first_name,
                    last_name=last_name,
                    email=email
                )
                for item in cart:
                    OrderItem.objects.create(
                        order=order,
                        book=item['book'],
                        price=item['price'],
                        quantity=item['quantity']
                    )
                cart.clear()

            subject = f'Замовлення №{order.id}'
            message = f'Шановний {order.first_name},\n\nВи успішно оформили замовлення №{order.id}.'
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [order.email])

            return redirect('books:payment_process', order_id=order.id)

        except Exception as e:
            return render(request, 'order_error.html', {'error': str(e)})

    return render(request, 'order_create_form.html', {'cart': cart})


def payment_process(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    success_url = request.build_absolute_uri(reverse('books:payment_success')) + f"?order_id={order.id}"
    cancel_url = request.build_absolute_uri(reverse('books:payment_cancel'))

    session_data = {
        'mode': 'payment',
        'success_url': success_url,
        'cancel_url': cancel_url,
        'line_items': []
    }

    for item in order.items.all():
        session_data['line_items'].append({
            'price_data': {
                'unit_amount': int(item.price * 100),
                'currency': 'uah',
                'product_data': {
                    'name': item.book.title,
                },
            },
            'quantity': item.quantity,
        })

    session = stripe.checkout.Session.create(**session_data)
    order.stripe_id = session.id
    order.save()
    return redirect(session.url, code=303)


def payment_success(request):
    order_id = request.GET.get('order_id')
    if order_id:
        order = get_object_or_404(Order, id=order_id)
        order.paid = True
        order.save()
    return render(request, 'payment_success.html')


def payment_cancel(request):
    return render(request, 'payment_cancel.html')


# dz 33.1