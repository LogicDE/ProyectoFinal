import os
from flask import Flask, render_template, redirect, url_for, flash, session, request, jsonify
from flask_mysqldb import MySQL
from functools import wraps
from config import config

# Inicialización de la aplicación
app = Flask(__name__)
app.config.from_object(config['development'])

# Configuración de la base de datos
mysql = MySQL(app)

# Decorador para verificar si el usuario está autenticado
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Por favor inicie sesión para acceder a esta página.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Decorador para verificar roles de usuario
def role_required(roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_role' not in session or session['user_role'] not in roles:
                flash('No tiene permisos para acceder a esta página.', 'danger')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Rutas de autenticación
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        try:
            cursor = mysql.connection.cursor()
            cursor.callproc('sp_authenticate_user', (username, password))
            user = cursor.fetchone()
            cursor.close()
            
            if user:
                session['user_id'] = user[0]
                session['username'] = user[1]
                session['user_role'] = user[3]  # Asumiendo que el rol está en la posición 3
                flash('Inicio de sesión exitoso!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Usuario o contraseña incorrectos', 'danger')
        except Exception as e:
            flash(f'Error al iniciar sesión: {str(e)}', 'danger')
    
    return render_template('auth/login.html')

@app.route('/logout')
@login_required
def logout():
    session.clear()
    flash('Ha cerrado sesión correctamente.', 'info')
    return redirect(url_for('login'))

# Rutas principales
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

# API Endpoint para datos de Highcharts
@app.route('/api/chart-data')
@login_required
def chart_data():
    try:
        cursor = mysql.connection.cursor()
        cursor.callproc('sp_get_chart_data')
        data = cursor.fetchall()
        cursor.close()
        
        # Procesar datos para Highcharts
        chart_data = [{'name': item[0], 'y': float(item[1])} for item in data]
        return jsonify(chart_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Manejo de errores
@app.errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('errors/500.html'), 500

# Inicialización de la aplicación
if __name__ == '__main__':
    # Crear carpeta de subidas si no existe
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    
    app.run(debug=True, host='0.0.0.0')
