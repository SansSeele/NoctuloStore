from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL
import os

app = Flask(__name__)

# Configuración de la clave secreta
app.secret_key = os.urandom(24)

# Configuración de conexión a MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'NoctuloBD'

mysql = MySQL(app)

@app.before_request
def initialize_db():
    cursor = mysql.connection.cursor()

    # Crear la base de datos si no existe
    cursor.execute('CREATE DATABASE IF NOT EXISTS NoctuloBD')
    cursor.execute('USE NoctuloBD')

    # Crear la tabla 'usuarios' si no existe
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nombre VARCHAR(100) NOT NULL,
            apellido VARCHAR(100) NOT NULL,
            email VARCHAR(100) NOT NULL UNIQUE,
            password VARCHAR(100) NOT NULL
        );
    ''')

    # Crear la tabla 'items' si no existe
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS items (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            description TEXT,
            price FLOAT NOT NULL,
            image_url VARCHAR(255) NOT NULL,
            category VARCHAR(50) NOT NULL
        );
    ''')

    # Insertar usuario admin si no existe
    cursor.execute("SELECT * FROM usuarios WHERE email = 'admin@admin'")
    admin = cursor.fetchone()
    if not admin:
        cursor.execute("INSERT INTO usuarios (nombre, apellido, email, password) VALUES ('Admin', 'Admin', 'admin@admin', 'admin')")

    mysql.connection.commit()
    cursor.close()

@app.route('/')
def index():
    cur = mysql.connection.cursor()
    cur.execute("USE NoctuloBD")
    cur.execute("SELECT name, description, price, image_url FROM items LIMIT 3")
    productos_destacados = cur.fetchall()
    cur.close()
    return render_template('index.html', productos_destacados=productos_destacados)


@app.route('/<category>')
def show_category(category):
    cur = mysql.connection.cursor()
    cur.execute("USE NoctuloBD")
    cur.execute("SELECT * FROM items WHERE category = %s", (category,))
    items = cur.fetchall()
    cur.close()
    return render_template(f'{category}.html', items=items)



@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Obtener los datos del formulario
        nombre = request.form['nombre']
        apellido = request.form['apellido']
        email = request.form['email']
        password = request.form['password']

        # Conectar a la base de datos y verificar si el email ya está en uso
        cur = mysql.connection.cursor()
        cur.execute("USE NoctuloBD")
        cur.execute("SELECT * FROM usuarios WHERE email = %s", (email,))
        user = cur.fetchone()

        if user:
            flash("El email ya está en uso. Por favor, elige otro.")
            return redirect(url_for('register'))
        else:
            # Agregar el nuevo usuario a la tabla "usuarios"
            cur.execute("INSERT INTO usuarios (nombre, apellido, email, password) VALUES (%s, %s, %s, %s)", (nombre, apellido, email, password))
            mysql.connection.commit()
            cur.close()
            flash("Registro exitoso. Ahora puedes iniciar sesión con tu nuevo usuario.")
            return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Obtener los datos del formulario
        email = request.form['email']
        password = request.form['password']

        # Conectar a la base de datos y verificar las credenciales
        cur = mysql.connection.cursor()
        cur.execute("USE NoctuloBD")
        cur.execute("SELECT * FROM usuarios WHERE email = %s AND password = %s", (email, password))
        user = cur.fetchone()

        if user:
            # Iniciar la sesión del usuario
            session['user_id'] = user[0]
            session['user_name'] = user[1]
            
            # Verificar si es el administrador
            if email == 'admin@admin' and password == 'admin':
                flash("Inicio de sesión de administrador exitoso.")
                return redirect(url_for('sistema_stock'))
            
            flash("Inicio de sesión exitoso.")
            return redirect(url_for('index'))
        else:
            flash("Correo electrónico o contraseña incorrectos.")
            return redirect(url_for('index'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    # Cerrar la sesión del usuario
    session.pop('user_id', None)
    session.pop('user_name', None)
    flash("Sesión cerrada exitosamente.")
    return redirect(url_for('login'))

@app.route('/sistema_stock')
def sistema_stock():
    if 'user_id' not in session:
        flash("Por favor, inicia sesión primero.")
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()
    cur.execute("USE NoctuloBD")
    cur.execute("SELECT * FROM items")
    items = cur.fetchall()
    cur.close()
    return render_template('sistema_stock.html', items=items)

@app.route('/add_item', methods=['GET', 'POST'])
def add_item():
    if 'user_id' not in session:
        flash("Por favor, inicia sesión primero.")
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = request.form['price']
        image_url = request.form['image_url']
        category = request.form['category']

        cur = mysql.connection.cursor()
        cur.execute("USE NoctuloBD")
        cur.execute("INSERT INTO items (name, description, price, image_url, category) VALUES (%s, %s, %s, %s, %s)", (name, description, price, image_url, category))
        mysql.connection.commit()
        cur.close()

        flash("Artículo agregado exitosamente.")
        return redirect(url_for('sistema_stock'))

    return render_template('add_item.html')

@app.route('/update_item/<int:id>', methods=['GET', 'POST'])
def update_item(id):
    if 'user_id' not in session:
        flash("Por favor, inicia sesión primero.")
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()
    cur.execute("USE NoctuloBD")
    cur.execute("SELECT * FROM items WHERE id = %s", (id,))
    item = cur.fetchone()

    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = request.form['price']
        image_url = request.form['image_url']
        category = request.form['category']

        cur.execute("UPDATE items SET name = %s, description = %s, price = %s,image_url=%s, category = %s WHERE id = %s", (name, description, price,image_url, category, id))
        mysql.connection.commit()
        cur.close()

        flash("Artículo actualizado exitosamente.")
        return redirect(url_for('sistema_stock'))

    return render_template('update_item.html', item=item)

@app.route('/delete_item/<int:id>')
def delete_item(id):
    if 'user_id' not in session:
        flash("Por favor, inicia sesión primero.")
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()
    cur.execute("USE NoctuloBD")
    cur.execute("DELETE FROM items WHERE id = %s", (id,))
    mysql.connection.commit()
    cur.close()

    flash("Artículo eliminado exitosamente.")
    return redirect(url_for('sistema_stock'))

# Función para registrar rutas con nombres de función únicos
def register_route(url, template_name, endpoint):
    try:
        def route():
            cur = mysql.connection.cursor()
            cur.execute("USE NoctuloBD")
            cur.execute("SELECT * FROM items WHERE category = %s", (endpoint,))
            items = cur.fetchall()
            cur.close()
            return render_template(template_name, items=items)
        route.__name__ = endpoint  # Asegura que el nombre de la función sea único
        app.add_url_rule(url, endpoint, route)
    except AssertionError:
        print(f"Error: La ruta {url} con el endpoint {endpoint} ya existe y no se puede sobrescribir.")

# Registrar las rutas
routes = [
    ('/producto', 'productos.html', 'productos'),
    ('/gabinetes', 'gabinetes.html', 'gabinetes'),
    ('/almacenamiento', 'almacenamiento.html', 'almacenamiento'),
    ('/alimentacion', 'alimentacion.html', 'alimentacion'),
    ('/placas-madre', 'placas-madre.html', 'placas_madre'), 
    ('/procesadores', 'procesadores.html', 'procesadores'),
    ('/ram', 'ram.html', 'ram'),
    ('/tarjetas-graficas', 'tarjetas-graficas.html', 'tarjetas_graficas'),
    ('/ventiladores', 'ventiladores.html', 'ventiladores'),
    ('/ventilacion', 'ventilacion.html', 'ventilacion'),
]

for route in routes:
    register_route(route[0], route[1], route[2])

if __name__ == "__main__":
    app.run(debug=True, port=5000)
