from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
from functools import wraps
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
mysql = MySQL(app)

# Decorador para requerir login
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'loggedin' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Decorador para requerir roles específicos
def role_required(roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'loggedin' not in session:
                return redirect(url_for('login'))
            if session.get('id_rolsistema') not in roles:
                flash('No tiene permisos para acceder a esta página', 'danger')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.route('/')
def index():
    if 'loggedin' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        try:
            # Usar el procedimiento almacenado existente usuarioLogin
            cursor.callproc('usuarioLogin', [username, password])
            result = cursor.fetchone()
            cursor.close()
            
            if result:
                session['loggedin'] = True
                session['id_usuario'] = result['id_usuario']
                session['username'] = result['username']
                session['id_rolsistema'] = result['id_rolsistema']
                session['nom_rol'] = result.get('nom_rol', 'Usuario')
                flash('Inicio de sesión exitoso', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Usuario o contraseña incorrectos', 'danger')
        except Exception as e:
            cursor.close()
            # Fallback: consulta directa si el SP falla
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute(
                "SELECT u.id_usuario, u.username, u.id_rolsistema, rs.nom_rol "
                "FROM usuarios u JOIN roles_sistema rs ON u.id_rolsistema = rs.id_rolsistema "
                "WHERE u.username = %s AND u.hashed_pass = %s AND u.activo = 1", 
                (username, password)
            )
            result = cursor.fetchone()
            cursor.close()
            
            if result:
                session['loggedin'] = True
                session['id_usuario'] = result['id_usuario']
                session['username'] = result['username']
                session['id_rolsistema'] = result['id_rolsistema']
                session['nom_rol'] = result['nom_rol']
                flash('Inicio de sesión exitoso', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Usuario o contraseña incorrectos', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Sesión cerrada exitosamente', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Obtener estadísticas para el dashboard
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    try:
        # Usar vistas existentes en lugar de stored procedures
        cursor.execute("SELECT COUNT(*) as total FROM candidatos")
        total_candidatos = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(*) as total FROM vacantes WHERE id_estadovacante = 1")
        vacantes_activas = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(*) as total FROM vCandidatosEnProceso")
        en_proceso = cursor.fetchone()['total']
        
    except Exception as e:
        # Fallback si las vistas no existen
        cursor.execute("SELECT COUNT(*) as total FROM candidatos")
        total_candidatos = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(*) as total FROM vacantes")
        vacantes_activas = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(*) as total FROM postulaciones WHERE id_etapa NOT IN (11,12)")
        en_proceso = cursor.fetchone()['total']
    
    cursor.close()
    
    return render_template('dashboard.html', 
                         total_candidatos=total_candidatos,
                         vacantes_activas=vacantes_activas,
                         en_proceso=en_proceso)

# RUTAS PARA CANDIDATOS
@app.route('/candidatos')
@login_required
@role_required([1, 2, 9, 10])  # Admin, Reclutador, Recruiter, Hiring Manager
def candidatos():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        cursor.callproc('candidatoCrearActualizar', [None, None, None, None, None, 'SELECT'])
        candidatos = cursor.fetchall()
    except:
        # Fallback a consulta directa
        cursor.execute("SELECT c.*, f.nom_fuente FROM candidatos c LEFT JOIN fuentes f ON c.id_fuente = f.id_fuente")
        candidatos = cursor.fetchall()
    cursor.close()
    return render_template('candidatos.html', candidatos=candidatos)

@app.route('/candidatos/crear', methods=['POST'])
@login_required
@role_required([1, 2, 9])
def crear_candidato():
    if request.method == 'POST':
        identificacion = request.form['identificacion']
        nombre = request.form['nombre']
        email = request.form['email']
        telefono = request.form['telefono']
        id_fuente = request.form.get('id_fuente', 1)
        
        cursor = mysql.connection.cursor()
        try:
            cursor.callproc('candidatoCrearActualizar', 
                           [None, identificacion, nombre, email, telefono, id_fuente])
            mysql.connection.commit()
            flash('Candidato creado exitosamente', 'success')
        except Exception as e:
            mysql.connection.rollback()
            flash(f'Error al crear candidato: {str(e)}', 'danger')
        finally:
            cursor.close()
    
    return redirect(url_for('candidatos'))

# RUTAS PARA VACANTES
@app.route('/vacantes')
@login_required
def vacantes():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        cursor.callproc('svacanteCrearActualizar', [None, None, None, None, None, 'SELECT'])
        vacantes = cursor.fetchall()
    except:
        cursor.execute("SELECT v.*, d.nom_departamento, ev.nom_estado FROM vacantes v LEFT JOIN departamentos d ON v.id_departamento = d.id_departamento LEFT JOIN estados_vacantes ev ON v.id_estadovacante = ev.id_estadovacante")
        vacantes = cursor.fetchall()
    cursor.close()
    return render_template('vacantes.html', vacantes=vacantes)

@app.route('/vacantes/crear', methods=['POST'])
@login_required
@role_required([1, 2, 9, 10])
def crear_vacante():
    if request.method == 'POST':
        titulo = request.form['titulo']
        descripcion = request.form.get('descripcion', '')
        id_departamento = request.form.get('id_departamento', 1)
        id_estado = request.form.get('id_estado', 1)
        
        cursor = mysql.connection.cursor()
        try:
            cursor.callproc('svacanteCrearActualizar', 
                           [None, titulo, descripcion, id_departamento, id_estado, 'INSERT'])
            mysql.connection.commit()
            flash('Vacante creada exitosamente', 'success')
        except Exception as e:
            mysql.connection.rollback()
            flash(f'Error al crear vacante: {str(e)}', 'danger')
        finally:
            cursor.close()
    
    return redirect(url_for('vacantes'))

# RUTAS PARA POSTULACIONES
@app.route('/postulaciones')
@login_required
def postulaciones():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        cursor.execute("""
            SELECT p.*, c.nom_candidato, v.titulo_vacante, e.nom_etapa 
            FROM postulaciones p 
            JOIN candidatos c ON p.id_candidato = c.id_candidato 
            JOIN vacantes v ON p.id_vacante = v.id_vacante 
            JOIN etapas e ON p.id_etapa = e.id_etapa
        """)
        postulaciones = cursor.fetchall()
    except Exception as e:
        flash(f'Error al cargar postulaciones: {str(e)}', 'danger')
        postulaciones = []
    cursor.close()
    return render_template('postulaciones.html', postulaciones=postulaciones)

@app.route('/postulaciones/crear', methods=['POST'])
@login_required
@role_required([1, 2, 9])
def crear_postulacion():
    if request.method == 'POST':
        id_candidato = request.form['id_candidato']
        id_vacante = request.form['id_vacante']
        
        cursor = mysql.connection.cursor()
        try:
            cursor.callproc('postular', [id_candidato, id_vacante])
            mysql.connection.commit()
            flash('Postulación creada exitosamente', 'success')
        except Exception as e:
            mysql.connection.rollback()
            flash(f'Error al crear postulación: {str(e)}', 'danger')
        finally:
            cursor.close()
    
    return redirect(url_for('postulaciones'))

# RUTAS PARA REPORTES
@app.route('/reportes')
@login_required
def reportes():
    return render_template('reportes.html')

@app.route('/api/reporte/conversion-fuente')
@login_required
def api_conversion_fuente():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        cursor.callproc('conversionFuentes', ['2024-01-01', '2024-12-31'])
        data = cursor.fetchall()
    except:
        # Usar la vista existente
        cursor.execute("SELECT * FROM vConversionPorFuente")
        data = cursor.fetchall()
    cursor.close()
    
    # Formatear datos para Highcharts
    categorias = [item['nom_fuente'] for item in data]
    conversion_pct = [float(item['conversion_pct']) for item in data]
    
    return jsonify({
        'categorias': categorias,
        'series': [{
            'name': 'Tasa de Conversión (%)',
            'data': conversion_pct
        }]
    })

@app.route('/api/reporte/pipeline-vacante')
@login_required
def api_pipeline_vacante():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        cursor.callproc('funnelVacante', [1])  # Usar vacante ID 1 como ejemplo
        data = cursor.fetchall()
    except:
        # Usar la vista existente
        cursor.execute("SELECT * FROM vpipelinePorVacante")
        data = cursor.fetchall()
    cursor.close()
    
    return jsonify(list(data))

@app.route('/api/reporte/ofertas-mensuales')
@login_required
def api_ofertas_mensuales():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        cursor.execute("SELECT * FROM vOfertasEmitidasAceptadas")
        data = cursor.fetchall()
    except:
        data = []
    cursor.close()
    
    if data:
        meses = [f"{item['anio']}-{item['mes']}" for item in data]
        emitidas = [item['emitidas'] for item in data]
        aceptadas = [item['aceptadas'] for item in data]
    else:
        meses = []
        emitidas = []
        aceptadas = []
    
    return jsonify({
        'meses': meses,
        'series': [
            {'name': 'Ofertas Emitidas', 'data': emitidas},
            {'name': 'Ofertas Aceptadas', 'data': aceptadas}
        ]
    })

@app.route('/api/reporte/entrevistadores')
@login_required
def api_carga_entrevistadores():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        cursor.execute("SELECT * FROM vCargaEntrevistadores")
        data = cursor.fetchall()
    except:
        data = []
    cursor.close()
    
    entrevistadores = [item['nom_entrevistador'] for item in data]
    carga = [item['total_entrevistas'] for item in data]
    
    return jsonify({
        'entrevistadores': entrevistadores,
        'carga': carga
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)