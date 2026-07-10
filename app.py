from flask import Flask, request, redirect, url_for, render_template, session
from werkzeug.security import generate_password_hash, check_password_hash
from PIL import Image
import os
import sqlite3

app = Flask(__name__)


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")
app.secret_key = '12345'


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            brand TEXT,
            category TEXT,
            category_label TEXT,
            price REAL,
            old_price REAL,
            sizes TEXT,
            color TEXT,
            sort_order INTEGER,
            description TEXT,
            image TEXT
        )
    """)
    conn.commit()
    conn.close()

def init_Users():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fname TEXT,
            lname TEXT,
            username TEXT NOT NULL UNIQUE,  -- UNIQUE не даст зарегистрировать один Email дважды
            pass TEXT
        )
    """)

def init_Orders():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor() # Было conn.connect()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT,
            adress TEXT,
            status TEXT,
            data TEXT,       -- Здесь нужна запятая
            comment TEXT,
            product_id TEXT
        )
    """)
    conn.commit()
    conn.close()

init_Users()
init_db()  # вызывается один раз при старте приложения

@app.context_processor
def inject_cart_count():
    cart_session = session.get('cart', {})
    # Считаем сумму всех quantity в корзине
    total_items = sum(int(qty) for qty in cart_session.values())
    return dict(cart_count=total_items)

# ---------- Публічні сторінки ----------

@app.route("/")
def index():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM products
        ORDER BY sort_order ASC, id DESC
    """)

    products = cursor.fetchall()

    conn.close()

    return render_template("index.html", products=products)


@app.route("/catalog")
@app.route("/catalog/<category>")
def catalog(category=None):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if category:
        cursor.execute("""
            SELECT *
            FROM products
            WHERE category=?
            ORDER BY sort_order ASC, id DESC
        """, (category,))
    else:
        cursor.execute("""
            SELECT *
            FROM products
            ORDER BY sort_order ASC, id DESC
        """)

    products = cursor.fetchall()

    conn.close()

    return render_template(
        "catalog.html",
        products=products,
        category=category
    )


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/product/<int:product_id>")
def product(product_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM products WHERE id=?",
        (product_id,)

    )
    product = cursor.fetchone()
    conn.close()


    if product is None:
        return "Товар не найден", 404
    else:
        sizes_string = product['sizes']  
        sizes_list = sizes_string.split(',')
        sizes_tuple = tuple(sizes_list)
        return render_template("product.html", product=product, sizes_tuple=sizes_tuple)


# ---------- Авторизація / кабінет ----------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("email")
        password = request.form.get("password")

        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()

        # Проверяем, существует ли юзер и совпадает ли хэш пароля
        if user and check_password_hash(user['pass'], password):
            session['user_id'] = user['id']       # Записываем в сессию ID
            session['username'] = user['username'] # Записываем имя
            return redirect(url_for("index"))     # Отправляем на главную
        else:
            return "Неверное имя пользователя или пароль", 401

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # Получаем данные из инпутов по их атрибутам name
        fname = request.form.get("fname")
        lname = request.form.get("lname")
        username = request.form.get("username")  # email используется как логин
        password = request.form.get("pass")
        password_confirm = request.form.get("pass2")

        # Простая проверка совпадения паролей
        if password != password_confirm:
            return "Паролі не співпадають!", 400

        # Хэшируем пароль для безопасности
        hashed_password = generate_password_hash(password)

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        try:
            # Если решишь сохранять имя и фамилию, добавь колонки fname и lname в таблицу users
            cursor.execute(
                "INSERT INTO users (username, pass) VALUES (?, ?)",
                (username, hashed_password)
            )
            conn.commit()
        except sqlite3.IntegrityError:
            return "Користувач з таким Email вже існує", 400
        finally:
            conn.close()

        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/cabinet")
def cabinet():
    return render_template("cabinet.html")



@app.route("/logout")
def logout():
    session.clear()  # Полностью очищаем сессию пользователя
    return redirect(url_for("index"))  # Отправляем на главную страницу


# ---------- Кошик / оформлення замовлення ----------

@app.route("/cart")
def cart():
    # Получаем корзину из сессии. Структура: { "id_товара": количество }
    cart_session = session.get('cart', {})
    cart_items = []
    total_sum = 0

    if cart_session:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Формируем плейсхолдеры для SQL-запроса, например: ?, ?, ?
        placeholders = ', '.join(['?'] * len(cart_session))
        # Извлекаем ключи (id товаров) из сессии
        product_ids = list(cart_session.keys())

        # Запрашиваем из базы только те товары, которые лежат в корзине
        cursor.execute(f"SELECT * FROM products WHERE id IN ({placeholders})", product_ids)
        products = cursor.fetchall()
        conn.close()

        # Соединяем информацию из БД с количеством из сессии
        for product in products:
            prod_id = str(product['id'])
            quantity = int(cart_session[prod_id])
            subtotal = product['price'] * quantity
            total_sum += subtotal

            cart_items.append({
                'id': product['id'],
                'name': product['name'],
                'price': product['price'],
                'image': product['image'],
                'quantity': quantity,
                'subtotal': subtotal
            })

    return render_template("cart.html", items=cart_items, total=total_sum)


@app.route("/cart/add", methods=["POST"])
def add_to_cart():
    product_id = request.form.get("product_id")
    # Считываем "qty", так как в HTML написано name="qty"
    quantity = int(request.form.get("qty", 1)) 
    next_url = request.form.get("next", url_for("cart"))

    if not product_id:
        return "Неправильний ID товару", 400

    if 'cart' not in session:
        session['cart'] = {}

    cart_session = session['cart']

    if product_id in cart_session:
        cart_session[product_id] = int(cart_session[product_id]) + quantity
    else:
        cart_session[product_id] = quantity

    session['cart'] = cart_session
    session.modified = True

    # Вместо жесткого редиректа в корзину, возвращаем пользователя туда, откуда он пришел
    return redirect(next_url)


@app.route("/cart/update", methods=["POST"])
def update_cart():
    product_id = request.form.get("product_id")
    quantity = int(request.form.get("quantity", 1))

    if 'cart' in session and product_id in session['cart']:
        if quantity > 0:
            session['cart'][product_id] = quantity
        else:
            # Если количество выставили в 0 или меньше, удаляем товар
            session['cart'].pop(product_id, None)
        
        session.modified = True

    return redirect(url_for("cart"))


@app.route("/cart/remove", methods=["POST"])
def remove_from_cart():
    product_id = request.form.get("product_id")

    if 'cart' in session and product_id in session['cart']:
        session['cart'].pop(product_id, None)
        session.modified = True

    return redirect(url_for("cart"))


@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    if request.method == "POST":
        return redirect(url_for("order_success"))
    return render_template("checkout.html")


@app.route("/order-success")
def order_success():
    return render_template("order-success.html")


# ---------- Адмін-панель ----------

@app.route("/admin")
def admin_dashboard():
    return render_template("admin-dashboard.html")


@app.route("/admin/products")
def admin_products():
    return render_template("admin-products.html")


@app.route("/admin/products/new", methods=["GET", "POST"])
def admin_product_new():
    if request.method == "POST":
        prod_name = request.form["name"]
        prod_brand = request.form["brand"]
        prod_category = request.form.get("category")
        prod_category_label = request.form.get("category_label")
        prod_price = request.form["price"]
        prod_old_price = request.form.get("old_price")
        prod_sizes = request.form.get("sizes")
        prod_color = request.form.get("color")
        prod_sort_order = request.form.get("sort_order")
        prod_description = request.form.get("description")

        image = request.files.get("image")

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO products(
                name, brand, category, category_label,
                price, old_price, sizes, color,
                sort_order, description, image
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            prod_name,
            prod_brand,
            prod_category,
            prod_category_label,
            prod_price,
            prod_old_price,
            prod_sizes,
            prod_color,
            prod_sort_order,
            prod_description,
            ""  # Пока изображение пустое
        ))

        conn.commit()

        product_id = cursor.lastrowid

        if image and image.filename:
            img = Image.open(image)
            filename = f"{product_id}.webp"

            img_dir = os.path.join(BASE_DIR, "static", "img")
            os.makedirs(img_dir, exist_ok=True)

            img.save(os.path.join(img_dir, filename), "WEBP", quality=90)

            cursor.execute(
                "UPDATE products SET image=? WHERE id=?",
                (filename, product_id)
            )
            conn.commit()

        conn.close()

        return redirect(url_for("admin_products"))

    return render_template("admin-product-new.html")


@app.route("/admin/products/<int:product_id>/delete", methods=["POST"])
def admin_product_delete(product_id):
    return redirect(url_for("admin_products"))


@app.route("/admin/orders")
def admin_orders():
    return render_template("admin-orders.html")


@app.route("/admin/orders/<int:order_id>")
def admin_order_detail(order_id):
    return render_template(f"admin-order-{order_id}.html")


@app.route("/admin/orders/<int:order_id>/status", methods=["POST"])
def admin_order_status(order_id):
    return redirect(url_for("admin_order_detail", order_id=order_id))


if __name__ == "__main__":
    app.run(debug=True)
