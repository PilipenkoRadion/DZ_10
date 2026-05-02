from django.shortcuts import render, redirect, get_object_or_404
# Create your views here.
from .models import Book, Category
from django.contrib import messages as django_messages
from .forms import Step1Form
from django.db.models import Q, Count, Avg
def step1(request):
    form = Step1Form()
    if request.method == "POST":
        form = Step1Form(request.POST)
        if form.is_valid():
            request.session["reg_title"] = form.cleaned_data["title"]
            request.session["reg_author"] = form.cleaned_data["author"]
            request.session["reg_price"] = str(form.cleaned_data["price"])
            return redirect("step2")
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
        return redirect("step1")
    
    if request.method == "POST":
        description = request.POST.get("description")
        stock = request.POST.get("stock")
        category_id = request.POST.get("category")


        if not description:
            django_messages.error(request, "Введите описание книги")
            return redirect("step2")

        if not stock:
            django_messages.error(request, "Укажите наличее книг")
            return redirect("step2")
        
        if not category_id:
            django_messages.error(request, "Укажите категорию книг")
            return redirect("step2")
        
        try:
            category_obj = Category.objects.get(id=category_id)
        except Category.DoesNotExist:
            django_messages.error(request, "Выбранная категория не существует")
            return redirect("step2")
        
        if len(description) > 150:
            django_messages.error(request, "Описание не может превышать 150 символов")
            return redirect("step2")
        

        category_obj = get_object_or_404(Category, id=category_id)

        Book.objects.create(
            title=request.session["reg_title"],
            author=request.session["reg_author"],
            price=request.session["reg_price"],
            description=description,
            stock=stock,
            category=category_obj,
        )

        for i in steps_keys:
            del request.session[i]
        request.session.flush()
        django_messages.success(request, "Вы успешно добавили книгу в каталог!")
        return redirect("home")
    
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