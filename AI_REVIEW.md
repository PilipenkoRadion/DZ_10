# AI Code Review — "Книжковий магазин"

Ревью проведено с помощью Claude (Anthropic). Рассмотрены 3 самые сложные view-функции проекта: `order_create`, `payment_process`, `step2`.

---

## 1. `order_create`

### Оригінальний код

```python
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
```

### Рекомендації AI

1. **Немає валідації вхідних даних.** `first_name`, `last_name`, `email` беруться напряму з `request.POST` без перевірки — потрібна форма (`ModelForm`) з валідацією, інакше можна створити замовлення з порожнім email.
2. **`except Exception` — занадто широкий.** Ловить будь-яку помилку (включно з `KeyboardInterrupt`-подібними чи баги в коді) і мовчки показує користувачу `str(e)`, що може «злити» деталі внутрішньої реалізації. Краще ловити конкретні винятки.
3. **`send_mail` викликається поза транзакцією, але без try/except.** Якщо поштовий сервер недоступний, замовлення вже створено, а користувач побачить помилку — неконсистентний стан. Відправку листа краще обгорнути окремим try/except (або винести в Celery-таск), щоб збій пошти не ламав оформлення замовлення.
4. **Немає перевірки, що кошик не порожній усередині циклу** (перевірка `if not cart` є, але після POST кошик міг змінитися паралельним запитом — рідкісний edge case, можна ігнорувати для MVP).
5. **`cart.clear()` викликається до відправки листа** — це нормально, але якщо впаде відправка листа, кошик вже очищено, а замовлення створено — це ок, головне обробити виняток пошти окремо (див. п.3).

### Фінальний код (застосовані рекомендації 1–3)

```python
def order_create(request):
    """Оформлення замовлення на основі поточного кошика."""
    cart = Cart(request)
    if not cart:
        return redirect('books:book-list')

    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()

        if not first_name or not last_name or not email:
            django_messages.error(request, "Заповніть усі обов'язкові поля")
            return render(request, 'order_create_form.html', {'cart': cart})

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
        except (Book.DoesNotExist, ValueError) as e:
            logger.exception("Помилка при створенні замовлення")
            return render(request, 'order_error.html', {'error': str(e)})

        try:
            subject = f'Замовлення №{order.id}'
            message = f'Шановний {order.first_name},\n\nВи успішно оформили замовлення №{order.id}.'
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [order.email])
        except Exception:
            logger.exception("Не вдалося надіслати email про замовлення №%s", order.id)

        return redirect('books:payment_process', order_id=order.id)

    return render(request, 'order_create_form.html', {'cart': cart})
```

---

## 2. `payment_process`

### Оригінальний код

```python
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
```

### Рекомендації AI

1. **Немає обробки помилок Stripe API.** Виклик `stripe.checkout.Session.create` може впасти (`stripe.error.StripeError`) при проблемах з мережею чи некоректними даними — зараз користувач побачить 500-у сторінку.
2. **Немає захисту від повторної оплати вже оплаченого замовлення.** Якщо `order.paid == True`, все одно створюється нова Stripe-сесія — варто одразу редіректити на `payment_success`.
3. **`line_items` будується через `.append` у циклі — можна замінити на list comprehension** для читабельності (незначна стилістична правка).
4. **Немає перевірки, що у замовлення взагалі є items** — Stripe поверне помилку на порожньому `line_items`, краще перевірити заздалегідь і показати зрозуміле повідомлення користувачу.

### Фінальний код (застосовані рекомендації 1, 2, 4)

```python
def payment_process(request, order_id):
    """Створення Stripe Checkout сесії та редірект користувача на оплату."""
    order = get_object_or_404(Order, id=order_id)

    if order.paid:
        return redirect('books:payment_success')

    if not order.items.exists():
        django_messages.error(request, "Замовлення порожнє")
        return redirect('books:book-list')

    success_url = request.build_absolute_uri(reverse('books:payment_success')) + f"?order_id={order.id}"
    cancel_url = request.build_absolute_uri(reverse('books:payment_cancel'))

    line_items = [
        {
            'price_data': {
                'unit_amount': int(item.price * 100),
                'currency': 'uah',
                'product_data': {'name': item.book.title},
            },
            'quantity': item.quantity,
        }
        for item in order.items.all()
    ]

    try:
        session = stripe.checkout.Session.create(
            mode='payment',
            success_url=success_url,
            cancel_url=cancel_url,
            line_items=line_items,
        )
    except stripe.error.StripeError:
        logger.exception("Помилка Stripe при створенні сесії для замовлення №%s", order.id)
        return render(request, 'order_error.html', {'error': "Не вдалося ініціювати оплату, спробуйте пізніше"})

    order.stripe_id = session.id
    order.save(update_fields=['stripe_id'])
    return redirect(session.url, code=303)
```

---

## 3. `step2`

### Оригінальний код

```python
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
```

### Рекомендації AI

1. **`redirect("books:step2")` після помилки валідації скидає всі введені дані форми** (файл, опис, категорію) — користувачу доведеться заповнювати форму заново. Краще одразу рендерити `step2.html` з помилкою, без редіректу.
2. **`category_id` не перевіряється на коректність типу** — `Category.objects.get(id=category_id)` впаде з `ValueError`, якщо передати нечислове значення (наприклад XSS-пейлоад у параметрі), а не тільки `DoesNotExist`.
3. **`stock` не перевіряється на допустимі значення** (`"y"`/`"n"`) — можна записати довільний рядок у поле з `choices`.
4. **Дублювання логіки валідації через кілька `if`** — краще використати Django `Form`/`ModelForm`, що дасть валідацію "з коробки" (обов'язково для production, але виходить за межі мінімального рев'ю).
5. **Немає обробки помилки, якщо `reg_price` в сесії пошкоджено** (наприклад, не число) — `Book.objects.create` впаде з `DecimalException`.

### Фінальний код (застосовані рекомендації 1, 2, 3)

```python
def step2(request):
    """Другий крок майстра додавання книги: опис, наявність, категорія, фото."""
    steps_keys = ["reg_title", "reg_author", "reg_price"]
    if not all(k in request.session for k in steps_keys):
        return redirect("books:step1")

    categories = Category.objects.all()

    if request.method == "POST":
        photo = request.FILES.get("photo")
        description = request.POST.get("description", "")
        stock = request.POST.get("stock")
        category_id = request.POST.get("category")

        errors = []
        if not description:
            errors.append("Введите описание книги")
        elif len(description) > 150:
            errors.append("Описание не может превышать 150 символов")

        if stock not in dict(Book.STOCK_CHOICES):
            errors.append("Укажите корректное наличие книг")

        category_obj = None
        if not category_id:
            errors.append("Укажите категорию книг")
        else:
            try:
                category_obj = Category.objects.get(id=category_id)
            except (Category.DoesNotExist, ValueError):
                errors.append("Выбранная категория не существует")

        if errors:
            for e in errors:
                django_messages.error(request, e)
            return render(request, "step2.html", {"categories": categories})

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

    return render(request, "step2.html", {"categories": categories})
```