import os
import sqlite3
from flask import Flask, request, redirect, url_for, render_template
from PIL import Image

app = Flask(__name__)


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")


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


init_db()  # вызывается один раз при старте приложения


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
def catalog():
    category = request.args.get("category", "all")
    return render_template("catalog.html", category=category)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/product/<int:product_id>")
def product(product_id):
    return render_template("product-1.html", product_id=product_id)


# ---------- Авторизація / кабінет ----------

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        return redirect(url_for("cabinet"))
    return render_template("vhod.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        return redirect(url_for("cabinet"))
    return render_template("register.html")


@app.route("/cabinet")
def cabinet():
    return render_template("cabinet.html")


# ---------- Кошик / оформлення замовлення ----------

@app.route("/cart")
def cart():
    return render_template("cart.html")


@app.route("/cart/add", methods=["POST"])
def add_to_cart():
    return redirect(url_for("cart"))


@app.route("/cart/update", methods=["POST"])
def update_cart():
    return redirect(url_for("cart"))


@app.route("/cart/remove", methods=["POST"])
def remove_from_cart():
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
