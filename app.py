from flask import Flask, render_template, redirect, url_for, request

app = Flask(__name__)


# ---------- Публічні сторінки ----------

@app.route("/")
def index():
    return render_template("index.html")


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
