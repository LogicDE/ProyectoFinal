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
    cursor = None
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        user_role = session.get('id_rolsistema')
        
        if user_role == 1:  # Admin
            return render_admin_dashboard(cursor)
        elif user_role in [2, 9]:  # Reclutador/Recruiter
            return render_recruiter_dashboard(cursor)
        elif user_role == 10:  # Hiring Manager
            return render_hiring_manager_dashboard(cursor)
        elif user_role == 3:  # Entrevistador
            return render_entrevistador_dashboard(cursor)
        elif user_role == 11:  # Auditor
            return render_auditor_dashboard(cursor)
        else:
            return render_generic_dashboard(cursor)
            
    except Exception as e:
        print(f"Error en dashboard: {str(e)}")
        import traceback
        print(f"Traceback completo: {traceback.format_exc()}")
        flash('Error al cargar datos completos del dashboard. Mostrando vista básica.', 'warning')
        return render_template('dashboard.html',
                             total_candidatos=0,
                             vacantes_activas=0,
                             en_proceso=0,
                             postulaciones_hoy=0)
    finally:
        if cursor:
            cursor.close()

def render_admin_dashboard(cursor):
    """Dashboard completo para Administrador usando stored procedures"""
    try:
        print("DEBUG: Iniciando render_admin_dashboard con SP")
        
        # Función auxiliar para ejecutar stored procedures
        def safe_sp_call(sp_name, params=None, default=0):
            try:
                if params:
                    cursor.callproc(sp_name, params)
                else:
                    cursor.callproc(sp_name)
                result = cursor.fetchone()
                return result['total'] if result and 'total' in result else default
            except Exception as e:
                print(f"ERROR en SP {sp_name}: {e}")
                return default

        # Función para stored procedures que devuelven múltiples registros
        def safe_sp_call_multi(sp_name, params=None, default=[]):
            try:
                if params:
                    cursor.callproc(sp_name, params)
                else:
                    cursor.callproc(sp_name)
                return cursor.fetchall()
            except Exception as e:
                print(f"ERROR en SP {sp_name}: {e}")
                return default

        # Estadísticas generales usando stored procedures
        print("DEBUG: Ejecutando SP de candidatos")
        total_candidatos = safe_sp_call('sp_total_candidatos')
        
        print("DEBUG: Ejecutando SP de vacantes activas")
        vacantes_activas = safe_sp_call('sp_vacantes_activas')
        
        print("DEBUG: Ejecutando SP de usuarios activos")
        usuarios_activos = safe_sp_call('sp_usuarios_activos')
        
        print("DEBUG: Ejecutando SP de postulaciones hoy")
        postulaciones_hoy = safe_sp_call('sp_postulaciones_hoy')
        
        # Actividad reciente
        print("DEBUG: Ejecutando SP de actividad reciente")
        actividad_reciente = safe_sp_call_multi('sp_actividad_reciente')
        
        # Próximas entrevistas
        print("DEBUG: Ejecutando SP de próximas entrevistas")
        proximas_entrevistas = safe_sp_call_multi('sp_proximas_entrevistas')
        
        print(f"DEBUG: Datos obtenidos - Candidatos: {total_candidatos}, Vacantes: {vacantes_activas}, Usuarios: {usuarios_activos}, Postulaciones hoy: {postulaciones_hoy}")
        
        return render_template('dashboard_admin.html',
                             total_candidatos=total_candidatos,
                             vacantes_activas=vacantes_activas,
                             usuarios_activos=usuarios_activos,
                             postulaciones_hoy=postulaciones_hoy,
                             actividad_reciente=actividad_reciente,
                             proximas_entrevistas=proximas_entrevistas)
                             
    except Exception as e:
        print(f"ERROR CRÍTICO en render_admin_dashboard: {str(e)}")
        import traceback
        print(f"TRACEBACK: {traceback.format_exc()}")
        raise

def render_recruiter_dashboard(cursor):
    """Dashboard para Reclutador usando stored procedures"""
    try:
        print("DEBUG: Iniciando render_recruiter_dashboard con SP")
        
        def safe_sp_call(sp_name, params=None, default=0):
            try:
                if params:
                    cursor.callproc(sp_name, params)
                else:
                    cursor.callproc(sp_name)
                result = cursor.fetchone()
                return result['total'] if result and 'total' in result else default
            except Exception as e:
                print(f"ERROR en SP {sp_name}: {e}")
                return default

        def safe_sp_call_multi(sp_name, params=None, default=[]):
            try:
                if params:
                    cursor.callproc(sp_name, params)
                else:
                    cursor.callproc(sp_name)
                return cursor.fetchall()
            except Exception as e:
                print(f"ERROR en SP {sp_name}: {e}")
                return default

        # Estadísticas básicas
        print("DEBUG: Ejecutando SP básicos para recruiter")
        total_candidatos = safe_sp_call('sp_total_candidatos')
        vacantes_activas = safe_sp_call('sp_vacantes_activas')
        postulaciones_hoy = safe_sp_call('sp_postulaciones_hoy')
        en_proceso = safe_sp_call('sp_candidatos_en_proceso')
        
        # Candidatos recientes
        print("DEBUG: Ejecutando SP de candidatos recientes")
        candidatos_recientes = safe_sp_call_multi('sp_candidatos_recientes')
        
        # Postulaciones pendientes
        print("DEBUG: Ejecutando SP de postulaciones pendientes")
        postulaciones_pendientes = safe_sp_call_multi('sp_postulaciones_pendientes')
        
        print(f"DEBUG: Datos recruiter - Candidatos: {total_candidatos}, Vacantes: {vacantes_activas}, Postulaciones hoy: {postulaciones_hoy}, En proceso: {en_proceso}")
        
        return render_template('dashboard_recruiter.html',
                             total_candidatos=total_candidatos,
                             vacantes_activas=vacantes_activas,
                             postulaciones_hoy=postulaciones_hoy,
                             en_proceso=en_proceso,
                             candidatos_recientes=candidatos_recientes,
                             postulaciones_pendientes=postulaciones_pendientes)
                             
    except Exception as e:
        print(f"ERROR CRÍTICO en render_recruiter_dashboard: {str(e)}")
        import traceback
        print(f"TRACEBACK: {traceback.format_exc()}")
        raise

def render_hiring_manager_dashboard(cursor):
    """Dashboard para Hiring Manager usando stored procedures"""
    try:
        print("DEBUG: Iniciando render_hiring_manager_dashboard con SP")
        
        def safe_sp_call(sp_name, params=None, default=0):
            try:
                if params:
                    cursor.callproc(sp_name, params)
                else:
                    cursor.callproc(sp_name)
                result = cursor.fetchone()
                return result['total'] if result and 'total' in result else default
            except Exception as e:
                print(f"ERROR en SP {sp_name}: {e}")
                return default

        def safe_sp_call_multi(sp_name, params=None, default=[]):
            try:
                if params:
                    cursor.callproc(sp_name, params)
                else:
                    cursor.callproc(sp_name)
                return cursor.fetchall()
            except Exception as e:
                print(f"ERROR en SP {sp_name}: {e}")
                return default

        # Estadísticas básicas
        print("DEBUG: Ejecutando SP básicos para hiring manager")
        vacantes_activas = safe_sp_call('sp_vacantes_activas')
        ofertas_pendientes = safe_sp_call('sp_ofertas_pendientes')
        ofertas_aceptadas = safe_sp_call('sp_ofertas_aceptadas')
        candidatos_en_seleccion = safe_sp_call('sp_candidatos_en_seleccion')
        
        # Vacantes con más postulaciones
        print("DEBUG: Ejecutando SP de vacantes populares")
        vacantes_populares = safe_sp_call_multi('sp_vacantes_populares')
        
        # Candidatos finalistas
        print("DEBUG: Ejecutando SP de candidatos finalistas")
        candidatos_finalistas = safe_sp_call_multi('sp_candidatos_finalistas')
        
        print(f"DEBUG: Datos hiring manager - Vacantes: {vacantes_activas}, En selección: {candidatos_en_seleccion}, Ofertas pendientes: {ofertas_pendientes}")
        
        return render_template('dashboard_hiring_manager.html',
                             vacantes_activas=vacantes_activas,
                             candidatos_en_seleccion=candidatos_en_seleccion,
                             ofertas_pendientes=ofertas_pendientes,
                             ofertas_aceptadas=ofertas_aceptadas,
                             vacantes_populares=vacantes_populares,
                             candidatos_finalistas=candidatos_finalistas)
                             
    except Exception as e:
        print(f"ERROR CRÍTICO en render_hiring_manager_dashboard: {str(e)}")
        import traceback
        print(f"TRACEBACK: {traceback.format_exc()}")
        raise

def render_entrevistador_dashboard(cursor):
    """Dashboard para Entrevistador usando stored procedures"""
    try:
        print("DEBUG: Iniciando render_entrevistador_dashboard con SP")
        
        def safe_sp_call(sp_name, params=None, default=0):
            try:
                if params:
                    cursor.callproc(sp_name, params)
                else:
                    cursor.callproc(sp_name)
                result = cursor.fetchone()
                return result['total'] if result and 'total' in result else default
            except Exception as e:
                print(f"ERROR en SP {sp_name}: {e}")
                return default

        def safe_sp_call_multi(sp_name, params=None, default=[]):
            try:
                if params:
                    cursor.callproc(sp_name, params)
                else:
                    cursor.callproc(sp_name)
                return cursor.fetchall()
            except Exception as e:
                print(f"ERROR en SP {sp_name}: {e}")
                return default

        # Obtener el ID del entrevistador asociado al usuario
        print("DEBUG: Obteniendo ID del entrevistador")
        try:
            cursor.execute("SELECT id_entrevistador FROM usuarios WHERE id_usuario = %s", (session['id_usuario'],))
            user_data = cursor.fetchone()
            
            if not user_data or not user_data['id_entrevistador']:
                print("DEBUG: No se encontró entrevistador asociado al usuario")
                return render_template('dashboard_entrevistador.html', 
                                     entrevistas_hoy=0,
                                     proximas_entrevistas=[],
                                     pendientes_feedback=0,
                                     historial_entrevistas=[])
            
            id_entrevistador = user_data['id_entrevistador']
            print(f"DEBUG: ID del entrevistador: {id_entrevistador}")
        except Exception as e:
            print(f"ERROR obteniendo ID del entrevistador: {e}")
            return render_template('dashboard_entrevistador.html', 
                                 entrevistas_hoy=0,
                                 proximas_entrevistas=[],
                                 pendientes_feedback=0,
                                 historial_entrevistas=[])
        
        # Estadísticas del entrevistador usando SP con parámetros
        print("DEBUG: Ejecutando SP del entrevistador")
        entrevistas_hoy = safe_sp_call('sp_entrevistas_hoy', [id_entrevistador])
        pendientes_feedback = safe_sp_call('sp_pendientes_feedback', [id_entrevistador])
        
        # Próximas entrevistas
        print("DEBUG: Ejecutando SP de próximas entrevistas para entrevistador")
        proximas_entrevistas = safe_sp_call_multi('sp_proximas_entrevistas_entrevistador', [id_entrevistador])
        
        # Historial reciente de entrevistas
        print("DEBUG: Ejecutando SP de historial de entrevistas")
        historial_entrevistas = safe_sp_call_multi('sp_historial_entrevistas', [id_entrevistador])
        
        print(f"DEBUG: Datos entrevistador - Entrevistas hoy: {entrevistas_hoy}, Pendientes feedback: {pendientes_feedback}")
        
        return render_template('dashboard_entrevistador.html',
                             entrevistas_hoy=entrevistas_hoy,
                             proximas_entrevistas=proximas_entrevistas,
                             pendientes_feedback=pendientes_feedback,
                             historial_entrevistas=historial_entrevistas)
                             
    except Exception as e:
        print(f"ERROR CRÍTICO en render_entrevistador_dashboard: {str(e)}")
        import traceback
        print(f"TRACEBACK: {traceback.format_exc()}")
        raise

def render_auditor_dashboard(cursor):
    """Dashboard para Auditor usando stored procedures"""
    try:
        print("DEBUG: Iniciando render_auditor_dashboard con SP")
        
        def safe_sp_call(sp_name, params=None, default=0):
            try:
                if params:
                    cursor.callproc(sp_name, params)
                else:
                    cursor.callproc(sp_name)
                result = cursor.fetchone()
                return result['total'] if result and 'total' in result else default
            except Exception as e:
                print(f"ERROR en SP {sp_name}: {e}")
                return default

        def safe_sp_call_multi(sp_name, params=None, default=[]):
            try:
                if params:
                    cursor.callproc(sp_name, params)
                else:
                    cursor.callproc(sp_name)
                return cursor.fetchall()
            except Exception as e:
                print(f"ERROR en SP {sp_name}: {e}")
                return default

        # Totales generales en una sola llamada
        print("DEBUG: Ejecutando SP de totales generales")
        try:
            cursor.callproc('sp_totales_generales')
            totales = cursor.fetchone()
            
            total_candidatos = totales['total_candidatos'] if totales else 0
            total_vacantes = totales['total_vacantes'] if totales else 0
            total_postulaciones = totales['total_postulaciones'] if totales else 0
            total_entrevistas = totales['total_entrevistas'] if totales else 0
            total_ofertas = totales['total_ofertas'] if totales else 0
            total_contratados = totales['total_contratados'] if totales else 0
            
            # Calcular tasa de conversión
            tasa_conversion = (total_contratados / total_postulaciones * 100) if total_postulaciones > 0 else 0
            
        except Exception as e:
            print(f"ERROR en totales generales: {e}")
            total_candidatos = total_vacantes = total_postulaciones = total_entrevistas = total_ofertas = total_contratados = 0
            tasa_conversion = 0
        
        # Fuentes de candidatos
        print("DEBUG: Ejecutando SP de fuentes de candidatos")
        fuentes_candidatos = safe_sp_call_multi('sp_fuentes_candidatos')
        
        # Tiempo promedio
        print("DEBUG: Ejecutando SP de tiempo promedio")
        try:
            cursor.callproc('sp_tiempo_promedio_proceso')
            result = cursor.fetchone()
            tiempo_promedio = result['tiempo_promedio'] if result and result['tiempo_promedio'] else 0
        except Exception as e:
            print(f"ERROR en tiempo promedio: {e}")
            tiempo_promedio = 0
        
        print(f"DEBUG: Datos auditor - Candidatos: {total_candidatos}, Vacantes: {total_vacantes}, Postulaciones: {total_postulaciones}, Tasa conversión: {tasa_conversion}")
        
        return render_template('dashboard_auditor.html',
                             total_candidatos=total_candidatos,
                             total_vacantes=total_vacantes,
                             total_postulaciones=total_postulaciones,
                             total_entrevistas=total_entrevistas,
                             total_ofertas=total_ofertas,
                             total_contratados=total_contratados,
                             tasa_conversion=round(tasa_conversion, 2),
                             fuentes_candidatos=fuentes_candidatos,
                             tiempo_promedio=round(tiempo_promedio, 1))
                             
    except Exception as e:
        print(f"ERROR CRÍTICO en render_auditor_dashboard: {str(e)}")
        import traceback
        print(f"TRACEBACK: {traceback.format_exc()}")
        raise

def render_generic_dashboard(cursor):
    """Dashboard genérico para roles no especificados usando SP"""
    try:
        cursor.callproc('sp_total_candidatos')
        total_candidatos_result = cursor.fetchone()
        total_candidatos = total_candidatos_result['total'] if total_candidatos_result else 0
        
        cursor.callproc('sp_vacantes_activas')
        vacantes_activas_result = cursor.fetchone()
        vacantes_activas = vacantes_activas_result['total'] if vacantes_activas_result else 0
        
        return render_template('dashboard_generic.html',
                             total_candidatos=total_candidatos,
                             vacantes_activas=vacantes_activas)
    except Exception as e:
        print(f"Error en dashboard genérico: {e}")
        return render_template('dashboard_generic.html',
                             total_candidatos=0,
                             vacantes_activas=0)

# RUTAS PARA CANDIDATOS - VERSIÓN COMPLETA CON STORED PROCEDURES
@app.route('/candidatos')
@login_required
@role_required([1, 2, 9])
def candidatos():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        # Usar stored procedure para obtener candidatos
        cursor.callproc('sp_obtener_candidatos')
        candidatos = cursor.fetchall()
        
        # Obtener fuentes usando stored procedure
        cursor.callproc('sp_obtener_fuentes')
        fuentes = cursor.fetchall()
        
    except Exception as e:
        print(f"Error al cargar candidatos: {e}")
        # Fallback a consultas directas
        try:
            cursor.execute("SELECT c.*, f.nom_fuente FROM candidatos c LEFT JOIN fuentes f ON c.id_fuente = f.id_fuente")
            candidatos = cursor.fetchall()
            cursor.execute("SELECT * FROM fuentes")
            fuentes = cursor.fetchall()
        except Exception as fallback_error:
            print(f"Error en fallback: {fallback_error}")
            candidatos = []
            fuentes = []
    finally:
        cursor.close()
    
    return render_template('candidatos.html', candidatos=candidatos, fuentes=fuentes)

# RUTA PÚBLICA PARA REGISTRO DE CANDIDATOS (SIN LOGIN REQUERIDO)
@app.route('/registro-candidato', methods=['GET', 'POST'])
def registro_candidato_publico():
    if request.method == 'POST':
        identificacion = request.form['identificacion']
        nombre = request.form['nombre']
        email = request.form['email']
        telefono = request.form.get('telefono', '')
        id_fuente = request.form.get('id_fuente', 1)  # Fuente por defecto
        
        cursor = mysql.connection.cursor()
        try:
            # Llamar al stored procedure para crear candidato
            cursor.callproc('candidatoCrearActualizar', 
                           [None, identificacion, nombre, email, telefono, id_fuente])
            mysql.connection.commit()
            flash('¡Registro exitoso! Ahora puedes postularte a vacantes.', 'success')
            return redirect(url_for('registro_candidato_publico'))
        except Exception as e:
            mysql.connection.rollback()
            error_msg = str(e)
            if 'email ya existe' in error_msg.lower():
                flash('Error: El email ya está registrado. Por favor usa otro email.', 'danger')
            elif 'identificacion ya existe' in error_msg.lower():
                flash('Error: La identificación ya está registrada.', 'danger')
            else:
                flash(f'Error en el registro: {error_msg}', 'danger')
        finally:
            cursor.close()
    
    # GET request - mostrar formulario de registro
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        # Obtener fuentes usando stored procedure
        cursor.callproc('sp_obtener_fuentes')
        fuentes = cursor.fetchall()

        # Obtener vacantes activas usando stored procedure
        cursor.callproc('sp_obtener_vacantes_activas')
        vacantes_activas = cursor.fetchall()
        
    except Exception as e:
        print(f"Error al cargar datos para registro público: {e}")
        # Fallback a consultas directas
        try:
            cursor.execute("SELECT * FROM fuentes ORDER BY nom_fuente")
            fuentes = cursor.fetchall()
            cursor.execute("""
                SELECT 
                    v.*, 
                    d.nom_departamento,
                    (SELECT COUNT(*) FROM postulaciones p WHERE p.id_vacante = v.id_vacante) as num_postulaciones
                FROM vacantes v 
                LEFT JOIN departamentos d ON v.id_departamento = d.id_departamento 
                WHERE v.id_estadovacante = 1 
                ORDER BY v.fecha_creacion DESC 
                LIMIT 10
            """)
            vacantes_activas = cursor.fetchall()
        except Exception as fallback_error:
            print(f"Error en fallback registro público: {fallback_error}")
            fuentes = []
            vacantes_activas = []
    finally:
        cursor.close()
    
    return render_template('registro_publico.html', fuentes=fuentes, vacantes_activas=vacantes_activas)

@app.route('/candidatos/crear', methods=['POST'])
@login_required
@role_required([1, 2, 9])
def crear_candidato():
    if request.method == 'POST':
        identificacion = request.form['identificacion']
        nombre = request.form['nombre']
        email = request.form['email']
        telefono = request.form.get('telefono', '')
        id_fuente = request.form.get('id_fuente', 1)
        
        cursor = mysql.connection.cursor()
        try:
            # Llamar al stored procedure para crear candidato
            cursor.callproc('candidatoCrearActualizar', 
                           [None, identificacion, nombre, email, telefono, id_fuente])
            mysql.connection.commit()
            flash('Candidato creado exitosamente', 'success')
        except Exception as e:
            mysql.connection.rollback()
            error_msg = str(e)
            if 'email ya existe' in error_msg.lower():
                flash('Error: El email ya existe para otro candidato', 'danger')
            else:
                flash(f'Error al crear candidato: {error_msg}', 'danger')
        finally:
            cursor.close()
    
    return redirect(url_for('candidatos'))

@app.route('/candidatos/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required([1, 2, 9])
def editar_candidato(id):
    if request.method == 'POST':
        identificacion = request.form['identificacion']
        nombre = request.form['nombre']
        email = request.form['email']
        telefono = request.form.get('telefono', '')
        id_fuente = request.form.get('id_fuente', 1)
        
        cursor = mysql.connection.cursor()
        try:
            # Llamar al stored procedure para actualizar candidato
            cursor.callproc('candidatoCrearActualizar', 
                           [id, identificacion, nombre, email, telefono, id_fuente])
            mysql.connection.commit()
            flash('Candidato actualizado exitosamente', 'success')
        except Exception as e:
            mysql.connection.rollback()
            error_msg = str(e)
            if 'email ya existe' in error_msg.lower():
                flash('Error: El email ya existe para otro candidato', 'danger')
            else:
                flash(f'Error al actualizar candidato: {error_msg}', 'danger')
        finally:
            cursor.close()
        
        return redirect(url_for('candidatos'))
    
    else:
        # GET request - mostrar formulario de edición
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        try:
            # Usar stored procedure para obtener candidato
            cursor.callproc('sp_obtener_candidato_por_id', [id])
            candidato = cursor.fetchone()
            
            # Obtener fuentes usando stored procedure
            cursor.callproc('sp_obtener_fuentes')
            fuentes = cursor.fetchall()
            
        except Exception as e:
            print(f"Error al cargar candidato para edición: {e}")
            # Fallback a consultas directas
            try:
                cursor.execute("SELECT c.*, f.nom_fuente FROM candidatos c LEFT JOIN fuentes f ON c.id_fuente = f.id_fuente WHERE c.id_candidato = %s", (id,))
                candidato = cursor.fetchone()
                cursor.execute("SELECT * FROM fuentes")
                fuentes = cursor.fetchall()
            except Exception as fallback_error:
                flash(f'Error al cargar candidato: {str(fallback_error)}', 'danger')
                return redirect(url_for('candidatos'))
        finally:
            cursor.close()
        
        if not candidato:
            flash('Candidato no encontrado', 'danger')
            return redirect(url_for('candidatos'))
        
        return render_template('editar_candidato.html', candidato=candidato, fuentes=fuentes)

@app.route('/candidatos/eliminar/<int:id>', methods=['POST'])
@login_required
@role_required([1, 2, 9])
def eliminar_candidato(id):
    cursor = mysql.connection.cursor()
    try:
        # Usar stored procedure para eliminar candidato
        cursor.callproc('sp_eliminar_candidato', [id, ''])
        
        # Obtener el resultado del stored procedure
        result_cursor = mysql.connection.cursor()
        result_cursor.execute("SELECT @p_resultado as resultado")
        result = result_cursor.fetchone()
        result_cursor.close()
        
        if 'exitosamente' in result['resultado']:
            mysql.connection.commit()
            flash('Candidato eliminado exitosamente', 'success')
        else:
            flash(result['resultado'], 'danger')
            
    except Exception as e:
        mysql.connection.rollback()
        print(f"Error en eliminación con SP: {e}")
        # Fallback a método original
        try:
            cursor.execute("SELECT COUNT(*) as total FROM postulaciones WHERE id_candidato = %s", (id,))
            result = cursor.fetchone()
            
            if result['total'] > 0:
                flash('No se puede eliminar el candidato porque tiene postulaciones activas', 'danger')
            else:
                cursor.execute("DELETE FROM candidatos WHERE id_candidato = %s", (id,))
                mysql.connection.commit()
                flash('Candidato eliminado exitosamente', 'success')
        except Exception as fallback_error:
            mysql.connection.rollback()
            flash(f'Error al eliminar candidato: {str(fallback_error)}', 'danger')
    finally:
        cursor.close()
    
    return redirect(url_for('candidatos'))

@app.route('/api/candidatos/<int:id>')
@login_required
def api_obtener_candidato(id):
    """API para obtener datos de un candidato específico (para AJAX) usando stored procedure"""
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        # Usar stored procedure para obtener candidato
        cursor.callproc('sp_obtener_candidato_por_id', [id])
        candidato = cursor.fetchone()
        
        if candidato:
            return jsonify({
                'success': True,
                'candidato': candidato
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Candidato no encontrado'
            }), 404
    except Exception as e:
        print(f"Error en API obtener candidato: {e}")
        # Fallback a consulta directa
        try:
            cursor.execute("""
                SELECT c.*, f.nom_fuente 
                FROM candidatos c 
                LEFT JOIN fuentes f ON c.id_fuente = f.id_fuente 
                WHERE c.id_candidato = %s
            """, (id,))
            candidato = cursor.fetchone()
            
            if candidato:
                return jsonify({
                    'success': True,
                    'candidato': candidato
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'Candidato no encontrado'
                }), 404
        except Exception as fallback_error:
            return jsonify({
                'success': False,
                'message': f'Error: {str(fallback_error)}'
            }), 500
    finally:
        cursor.close()

@app.route('/api/candidatos-descartados')
@login_required
def api_candidatos_descartados():
    """API para obtener candidatos descartados usando stored procedure"""
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        # Usar stored procedure para obtener candidatos descartados
        cursor.callproc('sp_obtener_candidatos_descartados')
        data = cursor.fetchall()
        
        return jsonify({
            'success': True,
            'candidatos': data
        })
    except Exception as e:
        print(f"Error en API candidatos descartados: {e}")
        # Fallback a consulta directa
        try:
            cursor.execute("SELECT * FROM vCandidatosDescartados")
            data = cursor.fetchall()
            
            return jsonify({
                'success': True,
                'candidatos': data
            })
        except Exception as fallback_error:
            return jsonify({
                'success': False,
                'message': f'Error: {str(fallback_error)}'
            }), 500
    finally:
        cursor.close()
# RUTAS PARA VACANTES - VERSIÓN CON STORED PROCEDURES
@app.route('/vacantes')
@login_required
@role_required([1, 2, 9, 10])
def vacantes():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        # Usar stored procedure para obtener vacantes
        cursor.callproc('sp_obtener_vacantes')
        vacantes = cursor.fetchall()
        
        # Obtener departamentos usando stored procedure
        cursor.callproc('sp_obtener_departamentos')
        departamentos = cursor.fetchall()
        
        # Obtener estados de vacantes usando stored procedure
        cursor.callproc('sp_obtener_estados_vacantes')
        estados_vacantes = cursor.fetchall()
        
    except Exception as e:
        print(f"Error al cargar vacantes: {e}")
        # Fallback a consultas directas
        try:
            cursor.execute("""
                SELECT 
                    v.*, 
                    d.nom_departamento, 
                    ev.nom_estado,
                    (SELECT COUNT(*) FROM postulaciones p WHERE p.id_vacante = v.id_vacante) as num_postulaciones
                FROM vacantes v 
                LEFT JOIN departamentos d ON v.id_departamento = d.id_departamento 
                LEFT JOIN estados_vacantes ev ON v.id_estadovacante = ev.id_estadovacante
                ORDER BY v.fecha_creacion DESC
            """)
            vacantes = cursor.fetchall()
            
            cursor.execute("SELECT * FROM departamentos ORDER BY nom_departamento")
            departamentos = cursor.fetchall()
            
            cursor.execute("SELECT * FROM estados_vacantes ORDER BY id_estadovacante")
            estados_vacantes = cursor.fetchall()
            
        except Exception as fallback_error:
            print(f"Error en fallback: {fallback_error}")
            flash(f'Error al cargar vacantes: {str(fallback_error)}', 'danger')
            vacantes = []
            departamentos = []
            estados_vacantes = []
    
    cursor.close()
    return render_template('vacantes.html', 
                         vacantes=vacantes, 
                         departamentos=departamentos, 
                         estados_vacantes=estados_vacantes)

@app.route('/vacantes/crear', methods=['POST'])
@login_required
@role_required([1, 2, 9, 10])
def crear_vacante():
    if request.method == 'POST':
        titulo = request.form['titulo_vacante']
        descripcion = request.form.get('desc_vacante', '')
        id_departamento = request.form.get('id_departamento', 1)
        id_estado = request.form.get('id_estadovacante', 1)
        
        cursor = mysql.connection.cursor()
        try:
            # Llamar al stored procedure para crear vacante
            cursor.callproc('svacanteCrearActualizar', 
                           [None, titulo, descripcion, id_departamento, id_estado])
            mysql.connection.commit()
            flash('Vacante creada exitosamente', 'success')
        except Exception as e:
            mysql.connection.rollback()
            flash(f'Error al crear vacante: {str(e)}', 'danger')
        finally:
            cursor.close()
    
    return redirect(url_for('vacantes'))

@app.route('/vacantes/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required([1, 2, 9, 10])
def editar_vacante(id):
    if request.method == 'POST':
        titulo = request.form['titulo_vacante']
        descripcion = request.form.get('desc_vacante', '')
        id_departamento = request.form.get('id_departamento', 1)
        id_estado = request.form.get('id_estadovacante', 1)
        
        cursor = mysql.connection.cursor()
        try:
            # Llamar al stored procedure para actualizar vacante
            cursor.callproc('svacanteCrearActualizar', 
                           [id, titulo, descripcion, id_departamento, id_estado])
            mysql.connection.commit()
            flash('Vacante actualizada exitosamente', 'success')
        except Exception as e:
            mysql.connection.rollback()
            flash(f'Error al actualizar vacante: {str(e)}', 'danger')
        finally:
            cursor.close()
        
        return redirect(url_for('vacantes'))
    
    else:
        # GET request - mostrar formulario de edición
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        try:
            # Usar stored procedure para obtener vacante
            cursor.callproc('sp_obtener_vacante_por_id', [id])
            vacante = cursor.fetchone()
            
            # Obtener departamentos usando stored procedure
            cursor.callproc('sp_obtener_departamentos')
            departamentos = cursor.fetchall()
            
            # Obtener estados de vacantes usando stored procedure
            cursor.callproc('sp_obtener_estados_vacantes')
            estados_vacantes = cursor.fetchall()
            
        except Exception as e:
            print(f"Error al cargar vacante para edición: {e}")
            # Fallback a consultas directas
            try:
                cursor.execute("""
                    SELECT v.*, d.nom_departamento, ev.nom_estado
                    FROM vacantes v 
                    LEFT JOIN departamentos d ON v.id_departamento = d.id_departamento 
                    LEFT JOIN estados_vacantes ev ON v.id_estadovacante = ev.id_estadovacante
                    WHERE v.id_vacante = %s
                """, (id,))
                vacante = cursor.fetchone()
                
                cursor.execute("SELECT * FROM departamentos")
                departamentos = cursor.fetchall()
                
                cursor.execute("SELECT * FROM estados_vacantes")
                estados_vacantes = cursor.fetchall()
            except Exception as fallback_error:
                flash(f'Error al cargar vacante: {str(fallback_error)}', 'danger')
                return redirect(url_for('vacantes'))
        finally:
            cursor.close()
        
        if not vacante:
            flash('Vacante no encontrada', 'danger')
            return redirect(url_for('vacantes'))
        
        return render_template('editar_vacante.html', vacante=vacante, departamentos=departamentos, estados_vacantes=estados_vacantes)

@app.route('/vacantes/eliminar/<int:id>', methods=['POST'])
@login_required
@role_required([1, 2, 9])
def eliminar_vacante(id):
    cursor = mysql.connection.cursor()
    try:
        # Usar stored procedure para eliminar vacante
        cursor.callproc('sp_eliminar_vacante', [id, ''])
        
        # Obtener el resultado del stored procedure
        result_cursor = mysql.connection.cursor()
        result_cursor.execute("SELECT @p_resultado as resultado")
        result = result_cursor.fetchone()
        result_cursor.close()
        
        if 'exitosamente' in result['resultado']:
            mysql.connection.commit()
            flash('Vacante eliminada exitosamente', 'success')
        else:
            flash(result['resultado'], 'danger')
            
    except Exception as e:
        mysql.connection.rollback()
        print(f"Error en eliminación con SP: {e}")
        # Fallback a método original
        try:
            cursor.execute("SELECT COUNT(*) as total FROM postulaciones WHERE id_vacante = %s", (id,))
            result = cursor.fetchone()
            
            if result['total'] > 0:
                flash('No se puede eliminar la vacante porque tiene postulaciones activas', 'danger')
            else:
                cursor.execute("DELETE FROM vacantes WHERE id_vacante = %s", (id,))
                mysql.connection.commit()
                flash('Vacante eliminada exitosamente', 'success')
        except Exception as fallback_error:
            mysql.connection.rollback()
            flash(f'Error al eliminar vacante: {str(fallback_error)}', 'danger')
    finally:
        cursor.close()
    
    return redirect(url_for('vacantes'))

@app.route('/api/vacantes/<int:id>')
@login_required
def api_obtener_vacante(id):
    """API para obtener datos de una vacante específica (para AJAX) usando stored procedure"""
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        # Usar stored procedure para obtener estadísticas de vacante
        cursor.callproc('sp_obtener_estadisticas_vacante', [id])
        vacante = cursor.fetchone()
        
        if vacante:
            return jsonify({
                'success': True,
                'vacante': vacante
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Vacante no encontrada'
            }), 404
    except Exception as e:
        print(f"Error en API obtener vacante: {e}")
        # Fallback a consulta directa
        try:
            cursor.execute("""
                SELECT v.*, d.nom_departamento, ev.nom_estado,
                       (SELECT COUNT(*) FROM postulaciones p WHERE p.id_vacante = v.id_vacante) as num_postulaciones,
                       (SELECT COUNT(*) FROM entrevistas e 
                        JOIN postulaciones p ON e.id_postulacion = p.id_postulacion 
                        WHERE p.id_vacante = v.id_vacante) as num_entrevistas,
                       (SELECT COUNT(*) FROM ofertas o 
                        JOIN postulaciones p ON o.id_postulacion = p.id_postulacion 
                        WHERE p.id_vacante = v.id_vacante) as num_ofertas,
                       (SELECT COUNT(*) FROM postulaciones p 
                        WHERE p.id_vacante = v.id_vacante AND p.id_etapa = 11) as num_contratados
                FROM vacantes v 
                LEFT JOIN departamentos d ON v.id_departamento = d.id_departamento 
                LEFT JOIN estados_vacantes ev ON v.id_estadovacante = ev.id_estadovacante 
                WHERE v.id_vacante = %s
            """, (id,))
            vacante = cursor.fetchone()
            
            if vacante:
                return jsonify({
                    'success': True,
                    'vacante': vacante
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'Vacante no encontrada'
                }), 404
        except Exception as fallback_error:
            return jsonify({
                'success': False,
                'message': f'Error: {str(fallback_error)}'
            }), 500
    finally:
        cursor.close()

# RUTAS PARA POSTULACIONES
# RUTAS PARA POSTULACIONES - VERSIÓN CON STORED PROCEDURES
@app.route('/postulaciones')
@login_required
@role_required([1, 2, 9, 10])
def postulaciones():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        # Usar stored procedure para obtener postulaciones
        cursor.callproc('sp_obtener_postulaciones')
        postulaciones = cursor.fetchall()
        
        # Obtener candidatos usando stored procedure
        cursor.callproc('sp_obtener_candidatos_postulaciones')
        candidatos = cursor.fetchall()
        
        # Obtener vacantes usando stored procedure
        cursor.callproc('sp_obtener_vacantes_postulaciones')
        vacantes = cursor.fetchall()
        
        # Obtener etapas usando stored procedure
        cursor.callproc('sp_obtener_etapas')
        etapas = cursor.fetchall()
        
    except Exception as e:
        print(f"Error al cargar postulaciones: {e}")
        # Fallback a consultas directas
        try:
            cursor.execute("""
                SELECT p.*, c.nom_candidato, c.email, c.telefono, 
                       v.titulo_vacante, d.nom_departamento, ev.nom_estado, e.nom_etapa
                FROM postulaciones p 
                JOIN candidatos c ON p.id_candidato = c.id_candidato 
                JOIN vacantes v ON p.id_vacante = v.id_vacante 
                LEFT JOIN departamentos d ON v.id_departamento = d.id_departamento 
                LEFT JOIN estados_vacantes ev ON v.id_estadovacante = ev.id_estadovacante 
                JOIN etapas e ON p.id_etapa = e.id_etapa
                ORDER BY p.fecha_postula DESC
            """)
            postulaciones = cursor.fetchall()
            
            cursor.execute("SELECT id_candidato, nom_candidato, email FROM candidatos ORDER BY nom_candidato")
            candidatos = cursor.fetchall()
            
            cursor.execute("SELECT id_vacante, titulo_vacante FROM vacantes ORDER BY titulo_vacante")
            vacantes = cursor.fetchall()
            
            cursor.execute("SELECT id_etapa, nom_etapa FROM etapas ORDER BY id_etapa")
            etapas = cursor.fetchall()
            
        except Exception as fallback_error:
            print(f"Error en fallback: {fallback_error}")
            flash(f'Error al cargar postulaciones: {str(fallback_error)}', 'danger')
            postulaciones = []
            candidatos = []
            vacantes = []
            etapas = []
    
    cursor.close()
    return render_template('postulaciones.html', 
                         postulaciones=postulaciones, 
                         candidatos=candidatos, 
                         vacantes=vacantes, 
                         etapas=etapas)

@app.route('/postulaciones/crear', methods=['POST'])
@login_required
@role_required([1, 2, 9])
def crear_postulacion():
    if request.method == 'POST':
        id_candidato = request.form['id_candidato']
        id_vacante = request.form['id_vacante']
        id_etapa = request.form.get('id_etapa', 1)  # Etapa inicial por defecto
        
        cursor = mysql.connection.cursor()
        try:
            # Usar stored procedure para crear postulación
            cursor.callproc('sp_crear_postulacion', [id_candidato, id_vacante, id_etapa, ''])
            
            # Obtener el resultado del stored procedure
            result_cursor = mysql.connection.cursor()
            result_cursor.execute("SELECT @p_resultado as resultado")
            result = result_cursor.fetchone()
            result_cursor.close()
            
            if 'exitosamente' in result['resultado']:
                mysql.connection.commit()
                flash('Postulación creada exitosamente', 'success')
            else:
                flash(result['resultado'], 'danger')
                
        except Exception as e:
            mysql.connection.rollback()
            print(f"Error en creación con SP: {e}")
            # Fallback a método original
            try:
                cursor.callproc('postular', [id_candidato, id_vacante])
                
                # Si se especificó una etapa diferente a la inicial, actualizarla
                if id_etapa != 1:
                    cursor.execute(
                        "UPDATE postulaciones SET id_etapa = %s WHERE id_candidato = %s AND id_vacante = %s",
                        (id_etapa, id_candidato, id_vacante)
                    )
                
                mysql.connection.commit()
                flash('Postulación creada exitosamente', 'success')
            except Exception as fallback_error:
                mysql.connection.rollback()
                error_msg = str(fallback_error)
                if 'ya existe' in error_msg.lower():
                    flash('Error: El candidato ya está postulado a esta vacante', 'danger')
                else:
                    flash(f'Error al crear postulación: {error_msg}', 'danger')
        finally:
            cursor.close()
    
    return redirect(url_for('postulaciones'))

@app.route('/postulaciones/mover-etapa/<int:id>', methods=['POST'])
@login_required
@role_required([1, 2, 9])
def mover_etapa_postulacion(id):
    if request.method == 'POST':
        nueva_etapa = request.form['nueva_etapa']
        
        cursor = mysql.connection.cursor()
        try:
            # Usar stored procedure para actualizar etapa
            cursor.callproc('sp_actualizar_etapa_postulacion', [id, nueva_etapa, ''])
            
            # Obtener el resultado del stored procedure
            result_cursor = mysql.connection.cursor()
            result_cursor.execute("SELECT @p_resultado as resultado")
            result = result_cursor.fetchone()
            result_cursor.close()
            
            if 'exitosamente' in result['resultado']:
                mysql.connection.commit()
                flash('Etapa actualizada exitosamente', 'success')
            else:
                flash(result['resultado'], 'danger')
                
        except Exception as e:
            mysql.connection.rollback()
            print(f"Error en actualización de etapa con SP: {e}")
            # Fallback a método original
            try:
                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                
                # Obtener la etapa actual
                cursor.execute("SELECT id_etapa FROM postulaciones WHERE id_postulacion = %s", (id,))
                resultado = cursor.fetchone()
                
                if not resultado:
                    flash('Postulación no encontrada', 'danger')
                    return redirect(url_for('postulaciones'))
                    
                etapa_actual = resultado['id_etapa']
                
                # Verificar que la nueva etapa existe
                cursor.execute("SELECT id_etapa FROM etapas WHERE id_etapa = %s", (nueva_etapa,))
                if not cursor.fetchone():
                    flash('Etapa no válida', 'danger')
                    return redirect(url_for('postulaciones'))
                
                # Realizar la transición
                cursor.execute(
                    "UPDATE postulaciones SET id_etapa = %s WHERE id_postulacion = %s",
                    (nueva_etapa, id)
                )
                mysql.connection.commit()
                flash('Etapa actualizada exitosamente', 'success')
            except Exception as fallback_error:
                mysql.connection.rollback()
                flash(f'Error al actualizar etapa: {str(fallback_error)}', 'danger')
            finally:
                cursor.close()
    
    return redirect(url_for('postulaciones'))

@app.route('/postulaciones/eliminar/<int:id>', methods=['POST'])
@login_required
@role_required([1, 2, 9])
def eliminar_postulacion(id):
    cursor = mysql.connection.cursor()
    try:
        # Usar stored procedure para eliminar postulación
        cursor.callproc('sp_eliminar_postulacion', [id, ''])
        
        # Obtener el resultado del stored procedure
        result_cursor = mysql.connection.cursor()
        result_cursor.execute("SELECT @p_resultado as resultado")
        result = result_cursor.fetchone()
        result_cursor.close()
        
        mysql.connection.commit()
        flash(result['resultado'], 'success')
            
    except Exception as e:
        mysql.connection.rollback()
        print(f"Error en eliminación con SP: {e}")
        # Fallback a método original
        try:
            mysql.connection.begin()
            
            # Verificar si existen entrevistas asociadas y eliminarlas primero
            cursor.execute("SELECT COUNT(*) as count FROM entrevistas WHERE id_postulacion = %s", (id,))
            entrevistas_count = cursor.fetchone()['count']
            
            if entrevistas_count > 0:
                cursor.execute("DELETE FROM entrevistas WHERE id_postulacion = %s", (id,))
                flash(f'Se eliminaron {entrevistas_count} entrevistas asociadas', 'info')
            
            # Verificar si existen ofertas asociadas y eliminarlas
            cursor.execute("SELECT COUNT(*) as count FROM ofertas WHERE id_postulacion = %s", (id,))
            ofertas_count = cursor.fetchone()['count']
            
            if ofertas_count > 0:
                cursor.execute("DELETE FROM ofertas WHERE id_postulacion = %s", (id,))
                flash(f'Se eliminaron {ofertas_count} ofertas asociadas', 'info')
            
            # Eliminar la postulación
            cursor.execute("DELETE FROM postulaciones WHERE id_postulacion = %s", (id,))
            
            mysql.connection.commit()
            flash('Postulación eliminada exitosamente', 'success')
        except Exception as fallback_error:
            mysql.connection.rollback()
            flash(f'Error al eliminar postulación: {str(fallback_error)}', 'danger')
    finally:
        cursor.close()
    
    return redirect(url_for('postulaciones'))

@app.route('/api/postulaciones/<int:id>')
@login_required
def api_obtener_postulacion(id):
    """API para obtener datos de una postulación específica usando stored procedure"""
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        # Usar stored procedure para obtener postulación
        cursor.callproc('sp_obtener_postulacion_por_id', [id])
        postulacion = cursor.fetchone()
        
        if postulacion:
            return jsonify({
                'success': True,
                'postulacion': postulacion
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Postulación no encontrada'
            }), 404
    except Exception as e:
        print(f"Error en API obtener postulación: {e}")
        # Fallback a consulta directa
        try:
            cursor.execute("""
                SELECT p.*, c.nom_candidato, c.email, c.telefono, 
                       v.titulo_vacante, d.nom_departamento, ev.nom_estado, e.nom_etapa
                FROM postulaciones p 
                JOIN candidatos c ON p.id_candidato = c.id_candidato 
                JOIN vacantes v ON p.id_vacante = v.id_vacante 
                LEFT JOIN departamentos d ON v.id_departamento = d.id_departamento 
                LEFT JOIN estados_vacantes ev ON v.id_estadovacante = ev.id_estadovacante 
                JOIN etapas e ON p.id_etapa = e.id_etapa
                WHERE p.id_postulacion = %s
            """, (id,))
            postulacion = cursor.fetchone()
            
            if postulacion:
                return jsonify({
                    'success': True,
                    'postulacion': postulacion
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'Postulación no encontrada'
                }), 404
        except Exception as fallback_error:
            return jsonify({
                'success': False,
                'message': f'Error: {str(fallback_error)}'
            }), 500
    finally:
        cursor.close()

@app.route('/api/etapas')
@login_required
def api_obtener_etapas():
    """API para obtener todas las etapas usando stored procedure"""
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        # Usar stored procedure para obtener etapas
        cursor.callproc('sp_obtener_etapas')
        etapas = cursor.fetchall()
        
        return jsonify({
            'success': True,
            'etapas': etapas
        })
    except Exception as e:
        print(f"Error en API obtener etapas: {e}")
        # Fallback a consulta directa
        try:
            cursor.execute("SELECT id_etapa, nom_etapa FROM etapas ORDER BY id_etapa")
            etapas = cursor.fetchall()
            
            return jsonify({
                'success': True,
                'etapas': etapas
            })
        except Exception as fallback_error:
            return jsonify({
                'success': False,
                'message': f'Error: {str(fallback_error)}'
            }), 500
    finally:
        cursor.close()

# RUTAS PARA ENTREVISTAS - VERSIÓN CON STORED PROCEDURES
@app.route('/entrevistas')
@login_required
@role_required([1, 2, 9, 10, 3])
def entrevistas():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        # Usar stored procedure para obtener entrevistas
        cursor.callproc('sp_obtener_entrevistas')
        entrevistas = cursor.fetchall()
        
        # Obtener postulaciones usando stored procedure
        cursor.callproc('sp_obtener_postulaciones_entrevistables')
        postulaciones = cursor.fetchall()
        
        # Obtener entrevistadores usando stored procedure
        cursor.callproc('sp_obtener_entrevistadores')
        entrevistadores = cursor.fetchall()
        
        # Obtener estados de entrevista usando stored procedure
        cursor.callproc('sp_obtener_estados_entrevista')
        estados_entrevista = cursor.fetchall()
        
    except Exception as e:
        print(f"Error al cargar entrevistas: {e}")
        # Fallback a consultas directas
        try:
            cursor.execute("""
                SELECT 
                    e.*, 
                    p.id_postulacion,
                    c.id_candidato,
                    c.nom_candidato, 
                    c.email as email_candidato,
                    c.telefono as telefono_candidato,
                    v.id_vacante,
                    v.titulo_vacante, 
                    d.nom_departamento,
                    ent.id_entrevistador,
                    ent.nom_entrevistador,
                    ent.email as email_entrevistador,
                    es.id_estadoentrevista,
                    es.nom_estado as estado_entrevista,
                    CONCAT(c.nom_candidato, ' - ', v.titulo_vacante) as descripcion,
                    CASE 
                        WHEN e.fecha_entrevista < CURDATE() THEN 'Pasada'
                        WHEN e.fecha_entrevista = CURDATE() THEN 'Hoy'
                        ELSE 'Futura'
                    END as tipo_fecha
                FROM entrevistas e
                JOIN postulaciones p ON e.id_postulacion = p.id_postulacion
                JOIN candidatos c ON p.id_candidato = c.id_candidato
                JOIN vacantes v ON p.id_vacante = v.id_vacante
                LEFT JOIN departamentos d ON v.id_departamento = d.id_departamento
                JOIN entrevistadores ent ON e.id_entrevistador = ent.id_entrevistador
                JOIN estados_entrevistas es ON e.id_estadoentrevista = es.id_estadoentrevista
                ORDER BY e.fecha_entrevista DESC, e.id_entrevista DESC
            """)
            entrevistas = cursor.fetchall()
            
            cursor.execute("""
                SELECT p.id_postulacion, c.nom_candidato, v.titulo_vacante,
                       CONCAT(c.nom_candidato, ' - ', v.titulo_vacante) as descripcion
                FROM postulaciones p
                JOIN candidatos c ON p.id_candidato = c.id_candidato
                JOIN vacantes v ON p.id_vacante = v.id_vacante
                WHERE p.id_etapa NOT IN (11,12)
                ORDER BY c.nom_candidato
            """)
            postulaciones = cursor.fetchall()
            
            cursor.execute("SELECT * FROM entrevistadores ORDER BY nom_entrevistador")
            entrevistadores = cursor.fetchall()
            
            cursor.execute("SELECT * FROM estados_entrevistas ORDER BY id_estadoentrevista")
            estados_entrevista = cursor.fetchall()
            
        except Exception as fallback_error:
            print(f"Error en fallback: {fallback_error}")
            flash(f'Error al cargar entrevistas: {str(fallback_error)}', 'danger')
            entrevistas = []
            postulaciones = []
            entrevistadores = []
            estados_entrevista = []
    
    cursor.close()
    return render_template('entrevistas.html', 
                         entrevistas=entrevistas,
                         postulaciones=postulaciones,
                         entrevistadores=entrevistadores,
                         estados_entrevista=estados_entrevista)

@app.route('/entrevistas/crear', methods=['POST'])
@login_required
@role_required([1, 2, 9])
def crear_entrevista():
    if request.method == 'POST':
        id_postulacion = request.form['id_postulacion']
        fecha_entrevista = request.form['fecha_entrevista']
        hora_entrevista = request.form.get('hora_entrevista', '09:00')
        id_entrevistador = request.form['id_entrevistador']
        id_estadoentrevista = request.form.get('id_estadoentrevista', 1)
        notas = request.form.get('notas', '')

        # Combinar fecha y hora
        fecha_hora = f"{fecha_entrevista} {hora_entrevista}"

        cursor = mysql.connection.cursor()
        try:
            # Usar stored procedure para crear entrevista
            cursor.callproc('sp_crear_entrevista', [
                id_postulacion, 
                fecha_hora, 
                id_entrevistador, 
                id_estadoentrevista, 
                notas, 
                ''
            ])
            
            # Obtener el resultado del stored procedure
            result_cursor = mysql.connection.cursor()
            result_cursor.execute("SELECT @p_resultado as resultado")
            result = result_cursor.fetchone()
            result_cursor.close()
            
            if 'exitosamente' in result['resultado']:
                mysql.connection.commit()
                flash('Entrevista programada exitosamente', 'success')
            else:
                flash(result['resultado'], 'danger')
                
        except Exception as e:
            mysql.connection.rollback()
            print(f"Error en creación con SP: {e}")
            # Fallback a método original
            try:
                cursor.execute("SHOW PROCEDURE STATUS LIKE 'programarEntrevista'")
                sp_exists = cursor.fetchone()
                
                if sp_exists:
                    cursor.callproc('programarEntrevista', [id_postulacion, id_entrevistador, fecha_hora])
                    cursor.execute("SELECT LAST_INSERT_ID() as id_entrevista")
                    id_entrevista_recien_creada = cursor.fetchone()['id_entrevista']
                    
                    if id_estadoentrevista != 1 or notas:
                        cursor.execute("""
                            UPDATE entrevistas 
                            SET id_estadoentrevista = %s, notas = %s
                            WHERE id_entrevista = %s
                        """, (id_estadoentrevista, notas, id_entrevista_recien_creada))
                else:
                    cursor.execute("""
                        INSERT INTO entrevistas (id_postulacion, fecha_entrevista, id_entrevistador, id_estadoentrevista, notas)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (id_postulacion, fecha_hora, id_entrevistador, id_estadoentrevista, notas))
                
                mysql.connection.commit()
                flash('Entrevista programada exitosamente', 'success')
                
            except Exception as fallback_error:
                mysql.connection.rollback()
                error_msg = str(fallback_error)
                if 'duplicate' in error_msg.lower() or 'ya existe' in error_msg.lower():
                    flash('Error: Ya existe una entrevista programada para esta postulación', 'danger')
                else:
                    flash(f'Error al programar entrevista: {error_msg}', 'danger')
        finally:
            cursor.close()
    
    return redirect(url_for('entrevistas'))

@app.route('/entrevistas/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required([1, 2, 9])
def editar_entrevista(id):
    if request.method == 'POST':
        fecha_entrevista = request.form['fecha_entrevista']
        hora_entrevista = request.form.get('hora_entrevista', '09:00')
        id_entrevistador = request.form['id_entrevistador']
        id_estadoentrevista = request.form['id_estadoentrevista']
        notas = request.form.get('notas', '')
        
        fecha_hora = f"{fecha_entrevista} {hora_entrevista}"
        
        cursor = mysql.connection.cursor()
        try:
            # Usar stored procedure para actualizar entrevista
            cursor.callproc('sp_actualizar_entrevista', [
                id, 
                fecha_hora, 
                id_entrevistador, 
                id_estadoentrevista, 
                notas, 
                ''
            ])
            
            # Obtener el resultado del stored procedure
            result_cursor = mysql.connection.cursor()
            result_cursor.execute("SELECT @p_resultado as resultado")
            result = result_cursor.fetchone()
            result_cursor.close()
            
            if 'exitosamente' in result['resultado']:
                mysql.connection.commit()
                flash('Entrevista actualizada exitosamente', 'success')
            else:
                flash(result['resultado'], 'danger')
                
        except Exception as e:
            mysql.connection.rollback()
            print(f"Error en actualización con SP: {e}")
            # Fallback a método original
            try:
                cursor.execute("""
                    UPDATE entrevistas 
                    SET fecha_entrevista = %s, id_entrevistador = %s, 
                        id_estadoentrevista = %s, notas = %s
                    WHERE id_entrevista = %s
                """, (fecha_hora, id_entrevistador, id_estadoentrevista, notas, id))
                
                mysql.connection.commit()
                flash('Entrevista actualizada exitosamente', 'success')
            except Exception as fallback_error:
                mysql.connection.rollback()
                flash(f'Error al actualizar entrevista: {str(fallback_error)}', 'danger')
        finally:
            cursor.close()
        
        return redirect(url_for('entrevistas'))
    
    else:
        # GET request - mostrar formulario de edición
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        try:
            # Usar stored procedure para obtener entrevista
            cursor.callproc('sp_obtener_entrevista_por_id', [id])
            entrevista = cursor.fetchone()
            
            # Obtener entrevistadores usando stored procedure
            cursor.callproc('sp_obtener_entrevistadores')
            entrevistadores = cursor.fetchall()
            
            # Obtener estados de entrevista usando stored procedure
            cursor.callproc('sp_obtener_estados_entrevista')
            estados_entrevista = cursor.fetchall()
            
        except Exception as e:
            print(f"Error al cargar entrevista para edición: {e}")
            # Fallback a consultas directas
            try:
                cursor.execute("""
                    SELECT e.*, p.id_postulacion, c.nom_candidato, v.titulo_vacante,
                           ent.nom_entrevistador, es.nom_estado as estado_entrevista,
                           DATE(e.fecha_entrevista) as fecha_sola,
                           TIME(e.fecha_entrevista) as hora_sola
                    FROM entrevistas e
                    JOIN postulaciones p ON e.id_postulacion = p.id_postulacion
                    JOIN candidatos c ON p.id_candidato = c.id_candidato
                    JOIN vacantes v ON p.id_vacante = v.id_vacante
                    JOIN entrevistadores ent ON e.id_entrevistador = ent.id_entrevistador
                    JOIN estados_entrevistas es ON e.id_estadoentrevista = es.id_estadoentrevista
                    WHERE e.id_entrevista = %s
                """, (id,))
                entrevista = cursor.fetchone()
                
                cursor.execute("SELECT * FROM entrevistadores ORDER BY nom_entrevistador")
                entrevistadores = cursor.fetchall()
                
                cursor.execute("SELECT * FROM estados_entrevistas ORDER BY id_estadoentrevista")
                estados_entrevista = cursor.fetchall()
                
            except Exception as fallback_error:
                flash(f'Error al cargar entrevista: {str(fallback_error)}', 'danger')
                return redirect(url_for('entrevistas'))
        finally:
            cursor.close()
        
        if not entrevista:
            flash('Entrevista no encontrada', 'danger')
            return redirect(url_for('entrevistas'))
        
        return render_template('editar_entrevista.html', 
                             entrevista=entrevista,
                             entrevistadores=entrevistadores,
                             estados_entrevista=estados_entrevista)

@app.route('/entrevistas/feedback/<int:id>', methods=['GET','POST'])
@login_required
@role_required([1, 2, 9])
def registrar_feedback_entrevista(id):
    if request.method == 'POST':
        puntaje = request.form['puntaje']
        comentarios = request.form.get('comentarios', '')
        id_estadoentrevista = request.form.get('id_estadoentrevista', 3)
        
        cursor = mysql.connection.cursor()
        try:
            # Verificar si la entrevista existe
            cursor.execute("SELECT id_entrevista FROM entrevistas WHERE id_entrevista = %s", (id,))
            if not cursor.fetchone():
                flash('Entrevista no encontrada', 'danger')
                return redirect(url_for('entrevistas'))
            
            # Usar el stored procedure existente para registrar feedback
            cursor.callproc('registrarFeedback', [id, puntaje, comentarios])
            
            # Actualizar el estado de la entrevista si se proporciona
            if id_estadoentrevista:
                cursor.execute("UPDATE entrevistas SET id_estadoentrevista = %s WHERE id_entrevista = %s", 
                             (id_estadoentrevista, id))
            
            mysql.connection.commit()
            flash('Feedback registrado exitosamente', 'success')
            return redirect(url_for('entrevistas'))
        except Exception as e:
            mysql.connection.rollback()
            flash(f'Error al registrar feedback: {str(e)}', 'danger')
            return redirect(url_for('entrevistas'))
        finally:
            cursor.close()
    
    # Para el método GET, obtener los estados de entrevista
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        cursor.callproc('sp_obtener_estados_entrevista')
        estados_entrevista = cursor.fetchall()
    except Exception as e:
        flash(f'Error al cargar estados de entrevista: {str(e)}', 'danger')
        return redirect(url_for('entrevistas'))
    finally:
        cursor.close()
    
    return render_template('registrar_feedback.html', 
                         entrevista_id=id,
                         estados_entrevista=estados_entrevista)

@app.route('/entrevistas/eliminar/<int:id>', methods=['POST'])
@login_required
@role_required([1, 2, 9])
def eliminar_entrevista(id):
    cursor = mysql.connection.cursor()
    try:
        # Usar stored procedure para eliminar entrevista
        cursor.callproc('sp_eliminar_entrevista', [id, ''])
        
        # Obtener el resultado del stored procedure
        result_cursor = mysql.connection.cursor()
        result_cursor.execute("SELECT @p_resultado as resultado")
        result = result_cursor.fetchone()
        result_cursor.close()
        
        if 'exitosamente' in result['resultado']:
            mysql.connection.commit()
            flash('Entrevista eliminada exitosamente', 'success')
        else:
            flash(result['resultado'], 'danger')
            
    except Exception as e:
        mysql.connection.rollback()
        print(f"Error en eliminación con SP: {e}")
        # Fallback a método original
        try:
            cursor.execute("SELECT id_entrevista FROM entrevistas WHERE id_entrevista = %s", (id,))
            if not cursor.fetchone():
                flash('Entrevista no encontrada', 'danger')
                return redirect(url_for('entrevistas'))
            
            cursor.execute("DELETE FROM entrevistas WHERE id_entrevista = %s", (id,))
            mysql.connection.commit()
            flash('Entrevista eliminada exitosamente', 'success')
        except Exception as fallback_error:
            mysql.connection.rollback()
            flash(f'Error al eliminar entrevista: {str(fallback_error)}', 'danger')
    finally:
        cursor.close()
    
    return redirect(url_for('entrevistas'))

@app.route('/api/entrevistas/<int:id>')
@login_required
def api_obtener_entrevista(id):
    """API para obtener datos de una entrevista específica usando stored procedure"""
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        # Usar stored procedure para obtener entrevista detallada
        cursor.callproc('sp_obtener_entrevista_detallada', [id])
        entrevista = cursor.fetchone()
        
        if not entrevista:
            return jsonify({
                'success': False,
                'message': 'Entrevista no encontrada'
            }), 404
        
        # Formatear respuesta
        resultado = {
            'id_entrevista': entrevista['id_entrevista'],
            'fecha_entrevista': str(entrevista['fecha_entrevista']) if entrevista['fecha_entrevista'] else None,
            'puntaje': float(entrevista['puntaje']) if entrevista['puntaje'] else None,
            'notas': entrevista['notas'] or '',
            'id_estadoentrevista': entrevista['id_estadoentrevista'],
            'id_entrevistador': entrevista['id_entrevistador'],
            'id_postulacion': entrevista['id_postulacion'],
            'nom_candidato': entrevista['nom_candidato'] or 'Candidato no disponible',
            'email_candidato': entrevista['email_candidato'] or '',
            'telefono_candidato': entrevista['telefono_candidato'] or '',
            'titulo_vacante': entrevista['titulo_vacante'] or 'Vacante no disponible',
            'nom_departamento': entrevista['nom_departamento'] or '',
            'nom_entrevistador': entrevista['nom_entrevistador'] or 'Entrevistador no disponible',
            'email_entrevistador': entrevista['email_entrevistador'] or '',
            'telefono_entrevistador': entrevista['telefono_entrevistador'] or '',
            'estado_entrevista': entrevista['estado_entrevista'] or 'Estado no disponible'
        }
        
        # Procesar fecha si existe
        if entrevista['fecha_entrevista']:
            from datetime import datetime
            if isinstance(entrevista['fecha_entrevista'], str):
                try:
                    fecha_obj = datetime.strptime(entrevista['fecha_entrevista'], '%Y-%m-%d %H:%M:%S')
                    resultado['fecha_sola'] = fecha_obj.strftime('%Y-%m-%d')
                    resultado['hora_sola'] = fecha_obj.strftime('%H:%M')
                except ValueError:
                    resultado['fecha_sola'] = None
                    resultado['hora_sola'] = None
            else:
                resultado['fecha_sola'] = entrevista['fecha_entrevista'].strftime('%Y-%m-%d')
                resultado['hora_sola'] = entrevista['fecha_entrevista'].strftime('%H:%M')
        else:
            resultado['fecha_sola'] = None
            resultado['hora_sola'] = None
        
        return jsonify({
            'success': True,
            'entrevista': resultado
        })
        
    except Exception as e:
        print(f"Error en API obtener entrevista: {e}")
        # Fallback a consulta directa
        try:
            cursor.execute("""
                SELECT 
                    e.id_entrevista,
                    e.fecha_entrevista,
                    e.puntaje,
                    e.notas,
                    e.id_estadoentrevista,
                    e.id_entrevistador,
                    p.id_postulacion,
                    c.nom_candidato, 
                    c.email as email_candidato,
                    c.telefono as telefono_candidato,
                    v.titulo_vacante, 
                    d.nom_departamento,
                    ent.nom_entrevistador,
                    ent.email as email_entrevistador,
                    ent.telefono as telefono_entrevistador,
                    es.nom_estado as estado_entrevista
                FROM entrevistas e
                LEFT JOIN postulaciones p ON e.id_postulacion = p.id_postulacion
                LEFT JOIN candidatos c ON p.id_candidato = c.id_candidato
                LEFT JOIN vacantes v ON p.id_vacante = v.id_vacante
                LEFT JOIN departamentos d ON v.id_departamento = d.id_departamento
                LEFT JOIN entrevistadores ent ON e.id_entrevistador = ent.id_entrevistador
                LEFT JOIN estados_entrevistas es ON e.id_estadoentrevista = es.id_estadoentrevista
                WHERE e.id_entrevista = %s
            """, (id,))
            entrevista = cursor.fetchone()
            
            if not entrevista:
                return jsonify({
                    'success': False,
                    'message': 'Entrevista no encontrada'
                }), 404
            
            # Formatear respuesta (mismo código que arriba)
            # ... (repetir el código de formateo)
            
        except Exception as fallback_error:
            return jsonify({
                'success': False,
                'message': f'Error: {str(fallback_error)}'
            }), 500
    finally:
        cursor.close()

@app.route('/api/postulaciones-entrevistables')
@login_required
def api_postulaciones_entrevistables():
    """API para obtener postulaciones que pueden tener entrevistas usando stored procedure"""
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        # Usar stored procedure para obtener postulaciones entrevistables
        cursor.callproc('sp_obtener_postulaciones_entrevistables_api')
        postulaciones = cursor.fetchall()
        
        return jsonify({
            'success': True,
            'postulaciones': postulaciones
        })
    except Exception as e:
        print(f"Error en API postulaciones entrevistables: {e}")
        # Fallback a consulta directa
        try:
            cursor.execute("""
                SELECT p.id_postulacion, c.nom_candidato, v.titulo_vacante,
                       CONCAT(c.nom_candidato, ' - ', v.titulo_vacante) as descripcion,
                       e.nom_etapa as etapa_actual
                FROM postulaciones p
                JOIN candidatos c ON p.id_candidato = c.id_candidato
                JOIN vacantes v ON p.id_vacante = v.id_vacante
                JOIN etapas e ON p.id_etapa = e.id_etapa
                WHERE p.id_etapa NOT IN (11,12)
                AND NOT EXISTS (
                    SELECT 1 FROM entrevistas ent 
                    WHERE ent.id_postulacion = p.id_postulacion 
                    AND ent.id_estadoentrevista IN (1, 2)
                )
                ORDER BY c.nom_candidato
            """)
            postulaciones = cursor.fetchall()
            
            return jsonify({
                'success': True,
                'postulaciones': postulaciones
            })
        except Exception as fallback_error:
            return jsonify({
                'success': False,
                'message': f'Error: {str(fallback_error)}'
            }), 500
    finally:
        cursor.close()

@app.route('/api/entrevistas-semana')
@login_required
def api_entrevistas_semana():
    """API para obtener entrevistas de la semana usando stored procedure"""
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        # Usar stored procedure para obtener entrevistas de la semana
        cursor.callproc('sp_obtener_entrevistas_semana')
        data = cursor.fetchall()
        
        return jsonify({
            'success': True,
            'entrevistas': data
        })
    except Exception as e:
        print(f"Error en API entrevistas semana: {e}")
        # Fallback a consulta directa de la vista
        try:
            cursor.execute("SELECT * FROM vEntrevistasSemana")
            data = cursor.fetchall()
            
            return jsonify({
                'success': True,
                'entrevistas': data
            })
        except Exception as fallback_error:
            return jsonify({
                'success': False,
                'message': f'Error: {str(fallback_error)}'
            }), 500
    finally:
        cursor.close()

# RUTAS PARA OFERTAS - VERSIÓN CON STORED PROCEDURES
@app.route('/ofertas')
@login_required
@role_required([1, 2, 9, 10])
def ofertas():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        # Usar stored procedure para obtener ofertas
        cursor.callproc('sp_obtener_ofertas')
        ofertas = cursor.fetchall()
        
        # Obtener postulaciones usando stored procedure
        cursor.callproc('sp_obtener_postulaciones_ofertables')
        postulaciones = cursor.fetchall()
        
        # Obtener estados de oferta usando stored procedure
        cursor.callproc('sp_obtener_estados_oferta')
        estados_oferta = cursor.fetchall()
        
    except Exception as e:
        print(f"Error al cargar ofertas: {e}")
        # Fallback a consultas directas
        try:
            cursor.execute("""
                SELECT 
                    o.*, 
                    p.id_postulacion,
                    c.id_candidato,
                    c.nom_candidato, 
                    c.email,
                    c.telefono,
                    v.id_vacante,
                    v.titulo_vacante, 
                    d.nom_departamento,
                    eo.id_estadoferta,
                    eo.nom_estado as estado_oferta,
                    CONCAT(c.nom_candidato, ' - ', v.titulo_vacante) as descripcion,
                    CASE 
                        WHEN o.fecha_decision IS NULL THEN 'Pendiente de decisión'
                        ELSE 'Decidida'
                    END as estado_avance
                FROM ofertas o
                JOIN postulaciones p ON o.id_postulacion = p.id_postulacion
                JOIN candidatos c ON p.id_candidato = c.id_candidato
                JOIN vacantes v ON p.id_vacante = v.id_vacante
                LEFT JOIN departamentos d ON v.id_departamento = d.id_departamento
                JOIN estados_ofertas eo ON o.id_estadoferta = eo.id_estadoferta
                ORDER BY o.id_oferta DESC
            """)
            ofertas = cursor.fetchall()
            
            cursor.execute("""
                SELECT p.id_postulacion, c.nom_candidato, v.titulo_vacante,
                       CONCAT(c.nom_candidato, ' - ', v.titulo_vacante) as descripcion,
                       e.nom_etapa as etapa_actual
                FROM postulaciones p
                JOIN candidatos c ON p.id_candidato = c.id_candidato
                JOIN vacantes v ON p.id_vacante = v.id_vacante
                JOIN etapas e ON p.id_etapa = e.id_etapa
                WHERE p.id_etapa >= 4
                AND NOT EXISTS (
                    SELECT 1 FROM ofertas o 
                    WHERE o.id_postulacion = p.id_postulacion 
                    AND o.id_estadoferta IN (1)
                )
                ORDER BY c.nom_candidato
            """)
            postulaciones = cursor.fetchall()
            
            cursor.execute("SELECT * FROM estados_ofertas ORDER BY id_estadoferta")
            estados_oferta = cursor.fetchall()
            
        except Exception as fallback_error:
            print(f"Error en fallback: {fallback_error}")
            flash(f'Error al cargar ofertas: {str(fallback_error)}', 'danger')
            ofertas = []
            postulaciones = []
            estados_oferta = []
    
    cursor.close()
    return render_template('ofertas.html', 
                         ofertas=ofertas,
                         postulaciones=postulaciones,
                         estados_oferta=estados_oferta)

@app.route('/ofertas/emitir', methods=['POST'])
@login_required
@role_required([1, 2, 9])
def emitir_oferta():
    if request.method == 'POST':
        id_postulacion = request.form['id_postulacion']
        monto_oferta = request.form['monto_oferta']
        id_estadoferta = request.form.get('id_estadoferta', 1)
        
        cursor = mysql.connection.cursor()
        try:
            # Usar stored procedure para crear oferta
            cursor.callproc('sp_crear_oferta', [
                id_postulacion, 
                monto_oferta, 
                id_estadoferta, 
                '',  # notas vacías por defecto
                ''
            ])
            
            # Obtener el resultado del stored procedure
            result_cursor = mysql.connection.cursor()
            result_cursor.execute("SELECT @p_resultado as resultado")
            result = result_cursor.fetchone()
            result_cursor.close()
            
            if 'exitosamente' in result['resultado']:
                mysql.connection.commit()
                flash('Oferta emitida exitosamente', 'success')
            else:
                flash(result['resultado'], 'danger')
                
        except Exception as e:
            mysql.connection.rollback()
            print(f"Error en emisión con SP: {e}")
            # Fallback a método original
            try:
                cursor.execute("SHOW PROCEDURE STATUS LIKE 'ofertaEmitir'")
                sp_exists = cursor.fetchone()
                
                if sp_exists:
                    cursor.callproc('ofertaEmitir', [id_postulacion, monto_oferta])
                    cursor.execute("SELECT LAST_INSERT_ID() as id_oferta")
                    id_oferta_recien_creada = cursor.fetchone()['id_oferta']
                    
                    if id_estadoferta != 1:
                        cursor.execute("""
                            UPDATE ofertas 
                            SET id_estadoferta = %s
                            WHERE id_oferta = %s
                        """, (id_estadoferta, id_oferta_recien_creada))
                else:
                    cursor.execute("""
                        INSERT INTO ofertas (id_postulacion, monto_oferta, id_estadoferta)
                        VALUES (%s, %s, %s)
                    """, (id_postulacion, monto_oferta, id_estadoferta))
                
                mysql.connection.commit()
                flash('Oferta emitida exitosamente', 'success')
                
            except Exception as fallback_error:
                mysql.connection.rollback()
                error_msg = str(fallback_error)
                if 'solo se puede emitir oferta a candidatos finalistas' in error_msg.lower():
                    flash('Error: Solo se pueden emitir ofertas a candidatos finalistas (Etapa 5)', 'danger')
                elif 'duplicate' in error_msg.lower() or 'ya existe' in error_msg.lower():
                    flash('Error: Ya existe una oferta para esta postulación', 'danger')
                else:
                    flash(f'Error al emitir oferta: {error_msg}', 'danger')
        finally:
            cursor.close()
    
    return redirect(url_for('ofertas'))

@app.route('/ofertas/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required([1, 2, 9])
def editar_oferta(id):
    if request.method == 'POST':
        monto_oferta = request.form['monto_oferta']
        id_estadoferta = request.form['id_estadoferta']
        notas = request.form.get('notas', '')
        
        cursor = mysql.connection.cursor()
        try:
            # Usar stored procedure para actualizar oferta
            cursor.callproc('sp_actualizar_oferta', [
                id, 
                monto_oferta, 
                id_estadoferta, 
                notas, 
                ''
            ])
            
            # Obtener el resultado del stored procedure
            result_cursor = mysql.connection.cursor()
            result_cursor.execute("SELECT @p_resultado as resultado")
            result = result_cursor.fetchone()
            result_cursor.close()
            
            if 'exitosamente' in result['resultado']:
                mysql.connection.commit()
                flash('Oferta actualizada exitosamente', 'success')
            else:
                flash(result['resultado'], 'danger')
                
        except Exception as e:
            mysql.connection.rollback()
            print(f"Error en actualización con SP: {e}")
            # Fallback a método original
            try:
                cursor.execute("""
                    UPDATE ofertas 
                    SET monto_oferta = %s, id_estadoferta = %s, notas = %s
                    WHERE id_oferta = %s
                """, (monto_oferta, id_estadoferta, notas, id))
                
                mysql.connection.commit()
                flash('Oferta actualizada exitosamente', 'success')
            except Exception as fallback_error:
                mysql.connection.rollback()
                flash(f'Error al actualizar oferta: {str(fallback_error)}', 'danger')
        finally:
            cursor.close()
        
        return redirect(url_for('ofertas'))
    
    else:
        # GET request - mostrar formulario de edición
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        try:
            # Usar stored procedure para obtener oferta
            cursor.callproc('sp_obtener_oferta_por_id', [id])
            oferta = cursor.fetchone()
            
            # Obtener estados de oferta usando stored procedure
            cursor.callproc('sp_obtener_estados_oferta')
            estados_oferta = cursor.fetchall()
            
        except Exception as e:
            print(f"Error al cargar oferta para edición: {e}")
            # Fallback a consultas directas
            try:
                cursor.execute("""
                    SELECT o.*, p.id_postulacion, c.nom_candidato, v.titulo_vacante,
                           eo.nom_estado as estado_oferta
                    FROM ofertas o
                    JOIN postulaciones p ON o.id_postulacion = p.id_postulacion
                    JOIN candidatos c ON p.id_candidato = c.id_candidato
                    JOIN vacantes v ON p.id_vacante = v.id_vacante
                    JOIN estados_ofertas eo ON o.id_estadoferta = eo.id_estadoferta
                    WHERE o.id_oferta = %s
                """, (id,))
                oferta = cursor.fetchone()
                
                cursor.execute("SELECT * FROM estados_ofertas ORDER BY id_estadoferta")
                estados_oferta = cursor.fetchall()
                
            except Exception as fallback_error:
                flash(f'Error al cargar oferta: {str(fallback_error)}', 'danger')
                return redirect(url_for('ofertas'))
        finally:
            cursor.close()
        
        if not oferta:
            flash('Oferta no encontrada', 'danger')
            return redirect(url_for('ofertas'))
        
        return render_template('editar_oferta.html', 
                             oferta=oferta,
                             estados_oferta=estados_oferta)

@app.route('/ofertas/decidir/<int:id>', methods=['POST'])
@login_required
@role_required([1, 2, 9])
def decidir_oferta(id):
    if request.method == 'POST':
        id_estadoferta = request.form['id_estadoferta']
        
        cursor = mysql.connection.cursor()
        try:
            # Usar stored procedure para decidir oferta
            cursor.callproc('sp_decidir_oferta', [id, id_estadoferta, ''])
            
            # Obtener el resultado del stored procedure
            result_cursor = mysql.connection.cursor()
            result_cursor.execute("SELECT @p_resultado as resultado")
            result = result_cursor.fetchone()
            result_cursor.close()
            
            if 'exitosamente' in result['resultado']:
                mysql.connection.commit()
                
                # Mensaje según el estado
                if id_estadoferta == '2':
                    flash('Oferta marcada como ACEPTADA exitosamente', 'success')
                elif id_estadoferta == '3':
                    flash('Oferta marcada como RECHAZADA exitosamente', 'warning')
                else:
                    flash('Decisión de oferta registrada exitosamente', 'success')
            else:
                flash(result['resultado'], 'danger')
                
        except Exception as e:
            mysql.connection.rollback()
            print(f"Error en decisión con SP: {e}")
            # Fallback a método original
            try:
                cursor.execute("SHOW PROCEDURE STATUS LIKE 'ofertaDecidir'")
                sp_exists = cursor.fetchone()
                
                if sp_exists:
                    if id_estadoferta == '2':
                        decision_texto = 'Aceptada'
                    elif id_estadoferta == '3':
                        decision_texto = 'Rechazada'
                    else:
                        flash('Estado de oferta no válido', 'danger')
                        return redirect(url_for('ofertas'))
                    
                    cursor.callproc('ofertaDecidir', [id, decision_texto])
                else:
                    cursor.execute("""
                        UPDATE ofertas 
                        SET id_estadoferta = %s, fecha_decision = NOW()
                        WHERE id_oferta = %s
                    """, (id_estadoferta, id))
                
                mysql.connection.commit()
                
                if id_estadoferta == '2':
                    flash('Oferta marcada como ACEPTADA exitosamente', 'success')
                elif id_estadoferta == '3':
                    flash('Oferta marcada como RECHAZADA exitosamente', 'warning')
                    
            except Exception as fallback_error:
                mysql.connection.rollback()
                error_msg = str(fallback_error)
                if 'solo se pueden decidir ofertas emitidas' in error_msg.lower():
                    flash('Error: Solo se pueden decidir ofertas en estado "Emitida"', 'danger')
                elif 'decisión inválida' in error_msg.lower():
                    flash('Error: Decisión inválida. Use Aceptada o Rechazada', 'danger')
                elif 'oferta no encontrada' in error_msg.lower():
                    flash('Error: Oferta no encontrada', 'danger')
                else:
                    flash(f'Error al registrar decisión de oferta: {error_msg}', 'danger')
        finally:
            cursor.close()
    
    return redirect(url_for('ofertas'))

@app.route('/ofertas/eliminar/<int:id>', methods=['POST'])
@login_required
@role_required([1, 2, 9])
def eliminar_oferta(id):
    cursor = mysql.connection.cursor()
    try:
        # Usar stored procedure para eliminar oferta
        cursor.callproc('sp_eliminar_oferta', [id, ''])
        
        # Obtener el resultado del stored procedure
        result_cursor = mysql.connection.cursor()
        result_cursor.execute("SELECT @p_resultado as resultado")
        result = result_cursor.fetchone()
        result_cursor.close()
        
        if 'exitosamente' in result['resultado']:
            mysql.connection.commit()
            flash('Oferta eliminada exitosamente', 'success')
        else:
            flash(result['resultado'], 'danger')
            
    except Exception as e:
        mysql.connection.rollback()
        print(f"Error en eliminación con SP: {e}")
        # Fallback a método original
        try:
            cursor.execute("SELECT id_oferta FROM ofertas WHERE id_oferta = %s", (id,))
            if not cursor.fetchone():
                flash('Oferta no encontrada', 'danger')
                return redirect(url_for('ofertas'))
            
            cursor.execute("SELECT id_estadoferta FROM ofertas WHERE id_oferta = %s", (id,))
            oferta = cursor.fetchone()
            
            if oferta and oferta['id_estadoferta'] in [2, 3]:
                flash('No se puede eliminar una oferta que ya ha sido decidida', 'danger')
            else:
                cursor.execute("DELETE FROM ofertas WHERE id_oferta = %s", (id,))
                mysql.connection.commit()
                flash('Oferta eliminada exitosamente', 'success')
        except Exception as fallback_error:
            mysql.connection.rollback()
            flash(f'Error al eliminar oferta: {str(fallback_error)}', 'danger')
    finally:
        cursor.close()
    
    return redirect(url_for('ofertas'))

# RUTAS PARA ESTADOS DE OFERTAS
@app.route('/estados-ofertas')
@login_required
@role_required([1, 2, 9])
def estados_ofertas():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        cursor.callproc('sp_obtener_estados_oferta')
        estados = cursor.fetchall()
    except Exception as e:
        flash(f'Error al cargar estados de ofertas: {str(e)}', 'danger')
        estados = []
    cursor.close()
    return render_template('estados_ofertas.html', estados=estados)

# RUTAS PARA REPORTES DE OFERTAS
@app.route('/reportes/ofertas')
@login_required
@role_required([1, 2, 9])
def reportes_ofertas():
    from datetime import datetime, timedelta
    fecha_fin = datetime.now().strftime('%Y-%m-%d')
    fecha_inicio = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    
    return render_template('reportes_ofertas.html', 
                         fecha_inicio=fecha_inicio,
                         fecha_fin=fecha_fin)

# APIs para Reportes usando Stored Procedures
@app.route('/api/reportes/ofertas/distribucion-estado')
@login_required
def api_reportes_ofertas_distribucion_estado():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        cursor.callproc('sp_reporte_ofertas_distribucion_estado')
        datos = cursor.fetchall()
        
        return jsonify({
            'success': True,
            'datos': datos
        })
    except Exception as e:
        print(f"Error en reporte distribución estado: {e}")
        # Fallback a consulta directa
        try:
            cursor.execute("""
                SELECT eo.nom_estado, COUNT(*) as cantidad
                FROM ofertas o
                JOIN estados_ofertas eo ON o.id_estadoferta = eo.id_estadoferta
                GROUP BY eo.nom_estado
                ORDER BY cantidad DESC
            """)
            datos = cursor.fetchall()
            
            return jsonify({
                'success': True,
                'datos': datos
            })
        except Exception as fallback_error:
            return jsonify({
                'success': False,
                'message': f'Error: {str(fallback_error)}'
            }), 500
    finally:
        cursor.close()

@app.route('/api/reportes/ofertas/tendencias-mensuales')
@login_required
def api_reportes_ofertas_tendencias_mensuales():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        cursor.callproc('sp_reporte_ofertas_tendencias_mensuales')
        datos = cursor.fetchall()
        
        return jsonify({
            'success': True,
            'datos': datos
        })
    except Exception as e:
        print(f"Error en reporte tendencias mensuales: {e}")
        # Fallback a consulta directa
        try:
            cursor.execute("""
                SELECT 
                    DATE_FORMAT(fecha_cambio, '%Y-%m') as mes,
                    COUNT(*) as cantidad,
                    SUM(CASE WHEN JSON_EXTRACT(payload, '$.estado') = 2 THEN 1 ELSE 0 END) as aceptadas,
                    SUM(CASE WHEN JSON_EXTRACT(payload, '$.estado') = 3 THEN 1 ELSE 0 END) as rechazadas
                FROM audit_ofertas
                WHERE op = 'U' AND JSON_EXTRACT(payload, '$.new_estado') IN (2, 3)
                GROUP BY DATE_FORMAT(fecha_cambio, '%Y-%m')
                ORDER BY mes
                LIMIT 12
            """)
            datos = cursor.fetchall()
            
            return jsonify({
                'success': True,
                'datos': datos
            })
        except Exception as fallback_error:
            return jsonify({
                'success': False,
                'message': f'Error: {str(fallback_error)}'
            }), 500
    finally:
        cursor.close()

@app.route('/api/reportes/ofertas/metricas-clave')
@login_required
def api_reportes_ofertas_metricas_clave():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        cursor.callproc('sp_reporte_ofertas_metricas_clave')
        datos = cursor.fetchone()
        
        return jsonify({
            'success': True,
            'datos': {
                'total_ofertas': datos['total_ofertas'],
                'monto_promedio': float(datos['monto_promedio']),
                'tasa_aceptacion': round(float(datos['tasa_aceptacion']), 2),
                'tiempo_promedio_decision': float(datos['tiempo_promedio_decision'])
            }
        })
    except Exception as e:
        print(f"Error en reporte métricas clave: {e}")
        # Fallback a consulta directa
        try:
            cursor.execute("SELECT COUNT(*) as total FROM ofertas")
            total_ofertas = cursor.fetchone()['total']
            
            cursor.execute("SELECT AVG(monto_oferta) as promedio FROM ofertas WHERE id_estadoferta = 2")
            monto_promedio = cursor.fetchone()['promedio'] or 0
            
            cursor.execute("SELECT COUNT(*) as total FROM ofertas WHERE id_estadoferta = 2")
            aceptadas = cursor.fetchone()['total']
            
            tasa_aceptacion = (aceptadas / total_ofertas * 100) if total_ofertas > 0 else 0
            
            cursor.execute("""
                SELECT AVG(DATEDIFF(fecha_cambio, 
                    (SELECT MAX(fecha_cambio) 
                     FROM audit_ofertas a2 
                     WHERE a2.id_oferta = a1.id_oferta AND a2.fecha_cambio < a1.fecha_cambio)
                )) as tiempo_promedio
                FROM audit_ofertas a1
                WHERE op = 'U' AND JSON_EXTRACT(payload, '$.new_estado') IN (2, 3)
            """)
            tiempo_promedio = cursor.fetchone()['tiempo_promedio'] or 0
            
            return jsonify({
                'success': True,
                'datos': {
                    'total_ofertas': total_ofertas,
                    'monto_promedio': float(monto_promedio),
                    'tasa_aceptacion': round(tasa_aceptacion, 2),
                    'tiempo_promedio_decision': float(tiempo_promedio)
                }
            })
        except Exception as fallback_error:
            return jsonify({
                'success': False,
                'message': f'Error: {str(fallback_error)}'
            }), 500
    finally:
        cursor.close()

@app.route('/api/reportes/ofertas/por-vacante')
@login_required
def api_reportes_ofertas_por_vacante():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        cursor.callproc('sp_reporte_ofertas_por_vacante')
        datos = cursor.fetchall()
        
        return jsonify({
            'success': True,
            'datos': datos
        })
    except Exception as e:
        print(f"Error en reporte por vacante: {e}")
        # Fallback a consulta directa
        try:
            cursor.execute("""
                SELECT 
                    v.id_vacante,
                    v.titulo_vacante,
                    COUNT(o.id_oferta) as total_ofertas,
                    SUM(CASE WHEN o.id_estadoferta = 2 THEN 1 ELSE 0 END) as aceptadas,
                    SUM(CASE WHEN o.id_estadoferta = 3 THEN 1 ELSE 0 END) as rechazadas,
                    AVG(o.monto_oferta) as monto_promedio
                FROM vacantes v
                LEFT JOIN postulaciones p ON v.id_vacante = p.id_vacante
                LEFT JOIN ofertas o ON p.id_postulacion = o.id_postulacion
                GROUP BY v.id_vacante, v.titulo_vacante
                HAVING total_ofertas > 0
                ORDER BY total_ofertas DESC
                LIMIT 10
            """)
            datos = cursor.fetchall()
            
            return jsonify({
                'success': True,
                'datos': datos
            })
        except Exception as fallback_error:
            return jsonify({
                'success': False,
                'message': f'Error: {str(fallback_error)}'
            }), 500
    finally:
        cursor.close()

@app.route('/api/reportes/ofertas/detallado')
@login_required
def api_reportes_ofertas_detallado():
    fecha_inicio = request.args.get('fecha_inicio', '')
    fecha_fin = request.args.get('fecha_fin', '')
    estado = request.args.get('estado', 'todos')
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        # Usar stored procedure para reporte detallado
        cursor.callproc('sp_reporte_ofertas_detallado', [fecha_inicio, fecha_fin, estado])
        datos = cursor.fetchall()
        
        # Formatear fechas
        for item in datos:
            if item['fecha_emision_estimada']:
                item['fecha_emision_estimada'] = item['fecha_emision_estimada'].strftime('%Y-%m-%d')
            if item['fecha_decision']:
                item['fecha_decision'] = item['fecha_decision'].strftime('%Y-%m-%d')
        
        return jsonify({
            'success': True,
            'datos': datos
        })
    except Exception as e:
        print(f"Error en reporte detallado: {e}")
        # Fallback a consulta directa
        try:
            query = """
                SELECT 
                    o.id_oferta,
                    c.nom_candidato,
                    v.titulo_vacante,
                    o.monto_oferta,
                    eo.nom_estado,
                    (SELECT MIN(fecha_cambio) 
                     FROM audit_ofertas a 
                     WHERE a.id_oferta = o.id_oferta AND a.op = 'I') as fecha_emision_estimada,
                    o.fecha_decision,
                    DATEDIFF(o.fecha_decision, 
                        (SELECT MIN(fecha_cambio) 
                         FROM audit_ofertas a 
                         WHERE a.id_oferta = o.id_oferta AND a.op = 'I')
                    ) as dias_pendiente
                FROM ofertas o
                JOIN postulaciones p ON o.id_postulacion = p.id_postulacion
                JOIN candidatos c ON p.id_candidato = c.id_candidato
                JOIN vacantes v ON p.id_vacante = v.id_vacante
                JOIN estados_ofertas eo ON o.id_estadoferta = eo.id_estadoferta
                WHERE 1=1
            """
            
            params = []
            
            if fecha_inicio:
                query += " AND (SELECT MIN(fecha_cambio) FROM audit_ofertas a WHERE a.id_oferta = o.id_oferta AND a.op = 'I') >= %s"
                params.append(fecha_inicio)
                
            if fecha_fin:
                query += " AND (SELECT MIN(fecha_cambio) FROM audit_ofertas a WHERE a.id_oferta = o.id_oferta AND a.op = 'I') <= %s"
                params.append(fecha_fin)
                
            if estado != 'todos':
                query += " AND o.id_estadoferta = %s"
                params.append(estado)
                
            query += " ORDER BY o.id_oferta DESC"
            
            cursor.execute(query, params)
            datos = cursor.fetchall()
            
            # Formatear fechas
            for item in datos:
                if item['fecha_emision_estimada']:
                    item['fecha_emision_estimada'] = item['fecha_emision_estimada'].strftime('%Y-%m-%d')
                if item['fecha_decision']:
                    item['fecha_decision'] = item['fecha_decision'].strftime('%Y-%m-%d')
            
            return jsonify({
                'success': True,
                'datos': datos
            })
        except Exception as fallback_error:
            return jsonify({
                'success': False,
                'message': f'Error: {str(fallback_error)}'
            }), 500
    finally:
        cursor.close()

# APIs adicionales usando Stored Procedures
@app.route('/api/ofertas/<int:id>')
@login_required
def api_obtener_oferta(id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        cursor.callproc('sp_obtener_oferta_por_id', [id])
        oferta = cursor.fetchone()
        
        if oferta:
            if oferta.get('fecha_decision'):
                oferta['fecha_decision'] = oferta['fecha_decision'].strftime('%Y-%m-%d %H:%M:%S')
            
            return jsonify({
                'success': True,
                'oferta': oferta
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Oferta no encontrada'
            }), 404
    except Exception as e:
        print(f"Error en API obtener oferta: {e}")
        # Fallback a consulta directa
        try:
            cursor.execute("""
                SELECT 
                    o.*, 
                    p.id_postulacion,
                    c.nom_candidato, 
                    c.email,
                    c.telefono,
                    v.titulo_vacante, 
                    d.nom_departamento,
                    eo.nom_estado as estado_oferta,
                    e.nom_etapa as etapa_actual
                FROM ofertas o
                JOIN postulaciones p ON o.id_postulacion = p.id_postulacion
                JOIN candidatos c ON p.id_candidato = c.id_candidato
                JOIN vacantes v ON p.id_vacante = v.id_vacante
                LEFT JOIN departamentos d ON v.id_departamento = d.id_departamento
                JOIN estados_ofertas eo ON o.id_estadoferta = eo.id_estadoferta
                JOIN etapas e ON p.id_etapa = e.id_etapa
                WHERE o.id_oferta = %s
            """, (id,))
            oferta = cursor.fetchone()
            
            if oferta:
                if oferta.get('fecha_decision'):
                    oferta['fecha_decision'] = oferta['fecha_decision'].strftime('%Y-%m-%d %H:%M:%S')
                
                return jsonify({
                    'success': True,
                    'oferta': oferta
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'Oferta no encontrada'
                }), 404
        except Exception as fallback_error:
            return jsonify({
                'success': False,
                'message': f'Error: {str(fallback_error)}'
            }), 500
    finally:
        cursor.close()

@app.route('/api/postulaciones-ofertables')
@login_required
def api_postulaciones_ofertables():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        cursor.callproc('sp_obtener_postulaciones_ofertables_api')
        postulaciones = cursor.fetchall()
        
        return jsonify({
            'success': True,
            'postulaciones': postulaciones
        })
    except Exception as e:
        print(f"Error en API postulaciones ofertables: {e}")
        # Fallback a consulta directa
        try:
            cursor.execute("""
                SELECT p.id_postulacion, c.nom_candidato, v.titulo_vacante,
                       CONCAT(c.nom_candidato, ' - ', v.titulo_vacante) as descripcion,
                       e.nom_etapa as etapa_actual,
                       c.email,
                       c.telefono
                FROM postulaciones p
                JOIN candidatos c ON p.id_candidato = c.id_candidato
                JOIN vacantes v ON p.id_vacante = v.id_vacante
                JOIN etapas e ON p.id_etapa = e.id_etapa
                WHERE p.id_etapa = 5
                AND NOT EXISTS (
                    SELECT 1 FROM ofertas o 
                    WHERE o.id_postulacion = p.id_postulacion 
                    AND o.id_estadoferta IN (1)
                )
                ORDER BY c.nom_candidato
            """)
            postulaciones = cursor.fetchall()
            
            return jsonify({
                'success': True,
                'postulaciones': postulaciones
            })
        except Exception as fallback_error:
            return jsonify({
                'success': False,
                'message': f'Error: {str(fallback_error)}'
            }), 500
    finally:
        cursor.close()

@app.route('/api/estadisticas-ofertas')
@login_required
def api_estadisticas_ofertas():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        cursor.callproc('sp_obtener_estadisticas_ofertas')
        estadisticas = cursor.fetchone()
        
        tasa_aceptacion = (estadisticas['ofertas_aceptadas'] / estadisticas['total_ofertas'] * 100) if estadisticas['total_ofertas'] > 0 else 0
        
        return jsonify({
            'success': True,
            'estadisticas': {
                'total_ofertas': estadisticas['total_ofertas'],
                'ofertas_pendientes': estadisticas['ofertas_pendientes'],
                'ofertas_aceptadas': estadisticas['ofertas_aceptadas'],
                'ofertas_rechazadas': estadisticas['ofertas_rechazadas'],
                'monto_promedio': float(estadisticas['monto_promedio'] or 0),
                'tasa_aceptacion': round(tasa_aceptacion, 2)
            }
        })
        
    except Exception as e:
        print(f"Error en API estadísticas ofertas: {e}")
        # Fallback a consulta directa
        try:
            cursor.execute("SELECT COUNT(*) as total FROM ofertas")
            total_ofertas = cursor.fetchone()['total']
            
            cursor.execute("SELECT COUNT(*) as total FROM ofertas WHERE id_estadoferta = 1")
            ofertas_pendientes = cursor.fetchone()['total']
            
            cursor.execute("SELECT COUNT(*) as total FROM ofertas WHERE id_estadoferta = 2")
            ofertas_aceptadas = cursor.fetchone()['total']
            
            cursor.execute("SELECT COUNT(*) as total FROM ofertas WHERE id_estadoferta = 3")
            ofertas_rechazadas = cursor.fetchone()['total']
            
            cursor.execute("SELECT AVG(monto_oferta) as promedio FROM ofertas WHERE id_estadoferta = 2")
            monto_promedio = cursor.fetchone()['promedio'] or 0
            
            tasa_aceptacion = (ofertas_aceptadas / total_ofertas * 100) if total_ofertas > 0 else 0
            
            return jsonify({
                'success': True,
                'estadisticas': {
                    'total_ofertas': total_ofertas,
                    'ofertas_pendientes': ofertas_pendientes,
                    'ofertas_aceptadas': ofertas_aceptadas,
                    'ofertas_rechazadas': ofertas_rechazadas,
                    'monto_promedio': float(monto_promedio),
                    'tasa_aceptacion': round(tasa_aceptacion, 2)
                }
            })
        except Exception as fallback_error:
            return jsonify({
                'success': False,
                'message': f'Error: {str(fallback_error)}'
            }), 500
    finally:
        cursor.close()

@app.route('/ofertas/dashboard')
@login_required
@role_required([1, 2, 9, 10])
def dashboard_ofertas():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        # Obtener ofertas recientes usando stored procedure
        cursor.callproc('sp_obtener_ofertas_recientes')
        ofertas_recientes = cursor.fetchall()
        
        # Obtener estadísticas rápidas usando stored procedure
        cursor.callproc('sp_obtener_estadisticas_ofertas')
        estadisticas = cursor.fetchone()
        
        pendientes = estadisticas['ofertas_pendientes']
        monto_promedio = estadisticas['monto_promedio'] or 0
        
    except Exception as e:
        print(f"Error en dashboard de ofertas: {e}")
        ofertas_recientes = []
        pendientes = 0
        monto_promedio = 0
    
    cursor.close()
    
    return render_template('dashboard_ofertas.html',
                         ofertas_recientes=ofertas_recientes,
                         pendientes=pendientes,
                         monto_promedio=monto_promedio)


# RUTA PARA CALENDARIO - VERSIÓN MEJORADA CON STORED PROCEDURES
@app.route('/calendario')
@login_required
@role_required([1, 2, 9, 10, 3])
def calendario():
    """Calendario de entrevistas con FullCalendar"""
    return render_template('calendario.html')

@app.route('/api/calendario/eventos')
@login_required
def api_calendario_eventos():
    """API para obtener eventos del calendario en formato FullCalendar usando stored procedure"""
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        # Usar stored procedure para obtener eventos del calendario
        cursor.callproc('sp_obtener_eventos_calendario')
        eventos_db = cursor.fetchall()
        
        # Formatear eventos para FullCalendar
        eventos = []
        for evento in eventos_db:
            eventos.append({
                'id': evento['id_entrevista'],
                'title': evento['title'],
                'start': evento['fecha_entrevista'].isoformat() if evento['fecha_entrevista'] else None,
                'end': evento['end'].isoformat() if evento['end'] else None,
                'color': evento['color'],
                'textColor': evento['textColor'],
                'extendedProps': {
                    'candidato': evento['nom_candidato'],
                    'vacante': evento['titulo_vacante'],
                    'entrevistador': evento['nom_entrevistador'],
                    'estado': evento['estado_entrevista'],
                    'id_estado': evento['id_estadoentrevista']
                }
            })
        
        return jsonify({
            'success': True,
            'eventos': eventos
        })
        
    except Exception as e:
        print(f"Error al cargar eventos del calendario: {e}")
        # Fallback a consulta directa en caso de error
        try:
            cursor.execute("""
                SELECT 
                    e.id_entrevista,
                    e.fecha_entrevista,
                    DATE_ADD(e.fecha_entrevista, INTERVAL 1 HOUR) as end,
                    c.nom_candidato,
                    v.titulo_vacante,
                    ent.nom_entrevistador,
                    es.nom_estado as estado_entrevista,
                    es.id_estadoentrevista,
                    CONCAT(c.nom_candidato, ' - ', v.titulo_vacante) as title,
                    CASE 
                        WHEN es.id_estadoentrevista = 1 THEN '#3498db'  -- Programada - Azul
                        WHEN es.id_estadoentrevista = 2 THEN '#f39c12'  -- En progreso - Naranja
                        WHEN es.id_estadoentrevista = 3 THEN '#27ae60'  -- Completada - Verde
                        WHEN es.id_estadoentrevista = 4 THEN '#e74c3c'  -- Cancelada - Rojo
                        ELSE '#95a5a6'  -- Otros - Gris
                    END as color,
                    CASE 
                        WHEN es.id_estadoentrevista = 1 THEN '#2980b9'  -- Programada - Azul oscuro
                        WHEN es.id_estadoentrevista = 2 THEN '#e67e22'  -- En progreso - Naranja oscuro
                        WHEN es.id_estadoentrevista = 3 THEN '#229954'  -- Completada - Verde oscuro
                        WHEN es.id_estadoentrevista = 4 THEN '#c0392b'  -- Cancelada - Rojo oscuro
                        ELSE '#7f8c8d'  -- Otros - Gris oscuro
                    END as textColor
                FROM entrevistas e
                JOIN postulaciones p ON e.id_postulacion = p.id_postulacion
                JOIN candidatos c ON p.id_candidato = c.id_candidato
                JOIN vacantes v ON p.id_vacante = v.id_vacante
                JOIN entrevistadores ent ON e.id_entrevistador = ent.id_entrevistador
                JOIN estados_entrevistas es ON e.id_estadoentrevista = es.id_estadoentrevista
                WHERE e.fecha_entrevista IS NOT NULL
                ORDER BY e.fecha_entrevista
            """)
            eventos_db = cursor.fetchall()
            
            eventos = []
            for evento in eventos_db:
                eventos.append({
                    'id': evento['id_entrevista'],
                    'title': evento['title'],
                    'start': evento['fecha_entrevista'].isoformat() if evento['fecha_entrevista'] else None,
                    'end': evento['end'].isoformat() if evento['end'] else None,
                    'color': evento['color'],
                    'textColor': evento['textColor'],
                    'extendedProps': {
                        'candidato': evento['nom_candidato'],
                        'vacante': evento['titulo_vacante'],
                        'entrevistador': evento['nom_entrevistador'],
                        'estado': evento['estado_entrevista'],
                        'id_estado': evento['id_estadoentrevista']
                    }
                })
            
            return jsonify({
                'success': True,
                'eventos': eventos
            })
            
        except Exception as fallback_error:
            print(f"Error en fallback al cargar eventos del calendario: {fallback_error}")
            return jsonify({
                'success': False,
                'message': f'Error al cargar eventos: {str(fallback_error)}'
            }), 500
    finally:
        cursor.close()

@app.route('/api/calendario/entrevistas-hoy')
@login_required
def api_entrevistas_hoy():
    """API para obtener entrevistas del día actual usando stored procedure"""
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        # Usar stored procedure para obtener entrevistas de hoy
        cursor.callproc('sp_obtener_entrevistas_hoy')
        entrevistas_hoy = cursor.fetchall()
        
        return jsonify({
            'success': True,
            'entrevistas': entrevistas_hoy
        })
        
    except Exception as e:
        print(f"Error al cargar entrevistas de hoy: {e}")
        # Fallback a consulta directa en caso de error
        try:
            cursor.execute("""
                SELECT 
                    e.id_entrevista,
                    e.fecha_entrevista,
                    c.nom_candidato,
                    v.titulo_vacante,
                    ent.nom_entrevistador,
                    es.nom_estado as estado_entrevista,
                    TIME(e.fecha_entrevista) as hora
                FROM entrevistas e
                JOIN postulaciones p ON e.id_postulacion = p.id_postulacion
                JOIN candidatos c ON p.id_candidato = c.id_candidato
                JOIN vacantes v ON p.id_vacante = v.id_vacante
                JOIN entrevistadores ent ON e.id_entrevistador = ent.id_entrevistador
                JOIN estados_entrevistas es ON e.id_estadoentrevista = es.id_estadoentrevista
                WHERE DATE(e.fecha_entrevista) = CURDATE()
                ORDER BY e.fecha_entrevista
            """)
            entrevistas_hoy = cursor.fetchall()
            
            return jsonify({
                'success': True,
                'entrevistas': entrevistas_hoy
            })
            
        except Exception as fallback_error:
            print(f"Error en fallback al cargar entrevistas de hoy: {fallback_error}")
            return jsonify({
                'success': False,
                'message': f'Error al cargar entrevistas: {str(fallback_error)}'
            }), 500
    finally:
        cursor.close()

# NUEVAS RUTAS ADICIONALES PARA EL CALENDARIO
@app.route('/api/calendario/estadisticas')
@login_required
def api_calendario_estadisticas():
    """API para obtener estadísticas del calendario usando stored procedure"""
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        # Usar stored procedure para obtener estadísticas
        cursor.callproc('sp_obtener_estadisticas_calendario')
        estadisticas = cursor.fetchall()
        
        return jsonify({
            'success': True,
            'estadisticas': estadisticas
        })
        
    except Exception as e:
        print(f"Error al cargar estadísticas del calendario: {e}")
        # Fallback a consulta directa
        try:
            cursor.execute("""
                SELECT 
                    YEAR(fecha_entrevista) as año,
                    MONTH(fecha_entrevista) as mes,
                    COUNT(*) as total_entrevistas,
                    SUM(CASE WHEN id_estadoentrevista = 1 THEN 1 ELSE 0 END) as programadas,
                    SUM(CASE WHEN id_estadoentrevista = 2 THEN 1 ELSE 0 END) as en_progreso,
                    SUM(CASE WHEN id_estadoentrevista = 3 THEN 1 ELSE 0 END) as completadas,
                    SUM(CASE WHEN id_estadoentrevista = 4 THEN 1 ELSE 0 END) as canceladas
                FROM entrevistas
                WHERE fecha_entrevista >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)
                GROUP BY YEAR(fecha_entrevista), MONTH(fecha_entrevista)
                ORDER BY año DESC, mes DESC
            """)
            estadisticas = cursor.fetchall()
            
            return jsonify({
                'success': True,
                'estadisticas': estadisticas
            })
            
        except Exception as fallback_error:
            return jsonify({
                'success': False,
                'message': f'Error al cargar estadísticas: {str(fallback_error)}'
            }), 500
    finally:
        cursor.close()

@app.route('/api/calendario/proximas-entrevistas')
@login_required
def api_proximas_entrevistas():
    """API para obtener próximas entrevistas usando stored procedure"""
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        # Usar stored procedure para obtener próximas entrevistas
        cursor.callproc('sp_obtener_proximas_entrevistas')
        proximas_entrevistas = cursor.fetchall()
        
        return jsonify({
            'success': True,
            'proximas_entrevistas': proximas_entrevistas
        })
        
    except Exception as e:
        print(f"Error al cargar próximas entrevistas: {e}")
        # Fallback a consulta directa
        try:
            cursor.execute("""
                SELECT 
                    e.id_entrevista,
                    e.fecha_entrevista,
                    c.nom_candidato,
                    v.titulo_vacante,
                    ent.nom_entrevistador,
                    es.nom_estado as estado_entrevista,
                    DATEDIFF(e.fecha_entrevista, CURDATE()) as dias_restantes
                FROM entrevistas e
                JOIN postulaciones p ON e.id_postulacion = p.id_postulacion
                JOIN candidatos c ON p.id_candidato = c.id_candidato
                JOIN vacantes v ON p.id_vacante = v.id_vacante
                JOIN entrevistadores ent ON e.id_entrevistador = ent.id_entrevistador
                JOIN estados_entrevistas es ON e.id_estadoentrevista = es.id_estadoentrevista
                WHERE e.fecha_entrevista >= CURDATE()
                AND e.fecha_entrevista <= DATE_ADD(CURDATE(), INTERVAL 7 DAY)
                AND e.id_estadoentrevista IN (1, 2)
                ORDER BY e.fecha_entrevista ASC
                LIMIT 10
            """)
            proximas_entrevistas = cursor.fetchall()
            
            return jsonify({
                'success': True,
                'proximas_entrevistas': proximas_entrevistas
            })
            
        except Exception as fallback_error:
            return jsonify({
                'success': False,
                'message': f'Error al cargar próximas entrevistas: {str(fallback_error)}'
            }), 500
    finally:
        cursor.close()

@app.route('/api/calendario/disponibilidad-entrevistadores')
@login_required
def api_disponibilidad_entrevistadores():
    """API para obtener disponibilidad de entrevistadores usando stored procedure"""
    fecha = request.args.get('fecha', datetime.now().strftime('%Y-%m-%d'))
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        # Usar stored procedure para obtener disponibilidad
        cursor.callproc('sp_obtener_disponibilidad_entrevistadores', [fecha])
        disponibilidad = cursor.fetchall()
        
        return jsonify({
            'success': True,
            'disponibilidad': disponibilidad,
            'fecha_consultada': fecha
        })
        
    except Exception as e:
        print(f"Error al cargar disponibilidad de entrevistadores: {e}")
        # Fallback a consulta directa
        try:
            cursor.execute("""
                SELECT 
                    ent.id_entrevistador,
                    ent.nom_entrevistador,
                    COUNT(e.id_entrevista) as entrevistas_programadas,
                    GROUP_CONCAT(TIME(e.fecha_entrevista) ORDER BY e.fecha_entrevista) as horarios_ocupados
                FROM entrevistadores ent
                LEFT JOIN entrevistas e ON ent.id_entrevistador = e.id_entrevistador 
                    AND DATE(e.fecha_entrevista) = %s
                    AND e.id_estadoentrevista IN (1, 2)
                GROUP BY ent.id_entrevistador, ent.nom_entrevistador
                ORDER BY entrevistas_programadas ASC
            """, (fecha,))
            disponibilidad = cursor.fetchall()
            
            return jsonify({
                'success': True,
                'disponibilidad': disponibilidad,
                'fecha_consultada': fecha
            })
            
        except Exception as fallback_error:
            return jsonify({
                'success': False,
                'message': f'Error al cargar disponibilidad: {str(fallback_error)}'
            }), 500
    finally:
        cursor.close()

# Ruta para el dashboard del calendario
@app.route('/calendario/dashboard')
@login_required
@role_required([1, 2, 9, 10, 3])
def calendario_dashboard():
    """Dashboard del calendario con estadísticas y próximas entrevistas"""
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        # Obtener estadísticas usando stored procedure
        cursor.callproc('sp_obtener_estadisticas_calendario')
        estadisticas = cursor.fetchall()
        
        # Obtener próximas entrevistas usando stored procedure
        cursor.callproc('sp_obtener_proximas_entrevistas')
        proximas_entrevistas = cursor.fetchall()
        
        # Obtener entrevistas de hoy usando stored procedure
        cursor.callproc('sp_obtener_entrevistas_hoy')
        entrevistas_hoy = cursor.fetchall()
        
    except Exception as e:
        print(f"Error en dashboard del calendario: {e}")
        estadisticas = []
        proximas_entrevistas = []
        entrevistas_hoy = []
    
    cursor.close()
    
    return render_template('calendario_dashboard.html',
                         estadisticas=estadisticas,
                         proximas_entrevistas=proximas_entrevistas,
                         entrevistas_hoy=entrevistas_hoy)

# RUTAS PARA ENTREVISTADORES - VERSIÓN CON STORED PROCEDURES
@app.route('/entrevistadores')
@login_required
@role_required([1, 2, 9])
def entrevistadores():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        # Usar stored procedure para obtener entrevistadores
        cursor.callproc('sp_obtener_entrevistadores')
        entrevistadores = cursor.fetchall()
        
        # Obtener roles usando stored procedure
        cursor.callproc('sp_obtener_roles')
        roles = cursor.fetchall()
        
    except Exception as e:
        print(f"Error al cargar entrevistadores: {e}")
        # Fallback a consultas directas
        try:
            cursor.execute("""
                SELECT e.*, r.nom_rol, 
                       COUNT(ent.id_entrevista) as total_entrevistas,
                       COUNT(CASE WHEN ent.fecha_entrevista >= CURDATE() THEN 1 END) as entrevistas_pendientes
                FROM entrevistadores e
                LEFT JOIN roles r ON e.id_rol = r.id_rol
                LEFT JOIN entrevistas ent ON e.id_entrevistador = ent.id_entrevistador
                GROUP BY e.id_entrevistador
                ORDER BY e.nom_entrevistador
            """)
            entrevistadores = cursor.fetchall()
            
            cursor.execute("SELECT * FROM roles ORDER BY nom_rol")
            roles = cursor.fetchall()
            
        except Exception as fallback_error:
            print(f"Error en fallback: {fallback_error}")
            flash(f'Error al cargar entrevistadores: {str(fallback_error)}', 'danger')
            entrevistadores = []
            roles = []
    
    cursor.close()
    return render_template('entrevistadores.html', 
                         entrevistadores=entrevistadores, 
                         roles=roles)

@app.route('/entrevistadores/crear', methods=['POST'])
@login_required
@role_required([1, 2, 9])
def crear_entrevistador():
    if request.method == 'POST':
        nom_entrevistador = request.form['nom_entrevistador']
        email = request.form['email']
        telefono = request.form.get('telefono', '')
        id_rol = request.form.get('id_rol', 1)
        
        cursor = mysql.connection.cursor()
        try:
            # Usar stored procedure para crear entrevistador
            cursor.callproc('sp_crear_entrevistador', [
                nom_entrevistador, 
                email, 
                telefono, 
                id_rol, 
                ''
            ])
            
            # Obtener el resultado del stored procedure
            result_cursor = mysql.connection.cursor()
            result_cursor.execute("SELECT @p_resultado as resultado")
            result = result_cursor.fetchone()
            result_cursor.close()
            
            if 'exitosamente' in result['resultado']:
                mysql.connection.commit()
                flash('Entrevistador creado exitosamente', 'success')
            else:
                flash(result['resultado'], 'danger')
                
        except Exception as e:
            mysql.connection.rollback()
            print(f"Error en creación con SP: {e}")
            # Fallback a método original
            try:
                cursor.execute("SELECT COUNT(*) as count FROM entrevistadores WHERE email = %s", (email,))
                result = cursor.fetchone()
                
                if result['count'] > 0:
                    flash('Error: El email ya existe para otro entrevistador', 'danger')
                else:
                    cursor.execute("""
                        INSERT INTO entrevistadores (nom_entrevistador, email, telefono, id_rol)
                        VALUES (%s, %s, %s, %s)
                    """, (nom_entrevistador, email, telefono, id_rol))
                    mysql.connection.commit()
                    flash('Entrevistador creado exitosamente', 'success')
                    
            except Exception as fallback_error:
                mysql.connection.rollback()
                flash(f'Error al crear entrevistador: {str(fallback_error)}', 'danger')
        finally:
            cursor.close()
    
    return redirect(url_for('entrevistadores'))

@app.route('/entrevistadores/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required([1, 2, 9])
def editar_entrevistador(id):
    if request.method == 'POST':
        nom_entrevistador = request.form['nom_entrevistador']
        email = request.form['email']
        telefono = request.form.get('telefono', '')
        id_rol = request.form.get('id_rol', 1)
        
        cursor = mysql.connection.cursor()
        try:
            # Usar stored procedure para actualizar entrevistador
            cursor.callproc('sp_actualizar_entrevistador', [
                id, 
                nom_entrevistador, 
                email, 
                telefono, 
                id_rol, 
                ''
            ])
            
            # Obtener el resultado del stored procedure
            result_cursor = mysql.connection.cursor()
            result_cursor.execute("SELECT @p_resultado as resultado")
            result = result_cursor.fetchone()
            result_cursor.close()
            
            if 'exitosamente' in result['resultado']:
                mysql.connection.commit()
                flash('Entrevistador actualizado exitosamente', 'success')
            else:
                flash(result['resultado'], 'danger')
                
        except Exception as e:
            mysql.connection.rollback()
            print(f"Error en actualización con SP: {e}")
            # Fallback a método original
            try:
                cursor.execute("SELECT COUNT(*) as count FROM entrevistadores WHERE email = %s AND id_entrevistador != %s", 
                             (email, id))
                result = cursor.fetchone()
                
                if result['count'] > 0:
                    flash('Error: El email ya existe para otro entrevistador', 'danger')
                else:
                    cursor.execute("""
                        UPDATE entrevistadores 
                        SET nom_entrevistador = %s, email = %s, telefono = %s, id_rol = %s
                        WHERE id_entrevistador = %s
                    """, (nom_entrevistador, email, telefono, id_rol, id))
                    mysql.connection.commit()
                    flash('Entrevistador actualizado exitosamente', 'success')
                    
            except Exception as fallback_error:
                mysql.connection.rollback()
                flash(f'Error al actualizar entrevistador: {str(fallback_error)}', 'danger')
        finally:
            cursor.close()
        
        return redirect(url_for('entrevistadores'))
    
    else:
        # GET request - mostrar formulario de edición
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        try:
            # Usar stored procedure para obtener entrevistador
            cursor.callproc('sp_obtener_entrevistador_por_id', [id])
            entrevistador = cursor.fetchone()
            
            # Obtener roles usando stored procedure
            cursor.callproc('sp_obtener_roles')
            roles = cursor.fetchall()
            
        except Exception as e:
            print(f"Error al cargar entrevistador para edición: {e}")
            # Fallback a consultas directas
            try:
                cursor.execute("""
                    SELECT e.*, r.nom_rol
                    FROM entrevistadores e
                    LEFT JOIN roles r ON e.id_rol = r.id_rol
                    WHERE e.id_entrevistador = %s
                """, (id,))
                entrevistador = cursor.fetchone()
                
                cursor.execute("SELECT * FROM roles ORDER BY nom_rol")
                roles = cursor.fetchall()
                
            except Exception as fallback_error:
                flash(f'Error al cargar entrevistador: {str(fallback_error)}', 'danger')
                return redirect(url_for('entrevistadores'))
        finally:
            cursor.close()
        
        if not entrevistador:
            flash('Entrevistador no encontrado', 'danger')
            return redirect(url_for('entrevistadores'))
        
        return render_template('editar_entrevistador.html', 
                             entrevistador=entrevistador, 
                             roles=roles)

@app.route('/entrevistadores/eliminar/<int:id>', methods=['POST'])
@login_required
@role_required([1, 2, 9])
def eliminar_entrevistador(id):
    cursor = mysql.connection.cursor()
    try:
        # Usar stored procedure para eliminar entrevistador
        cursor.callproc('sp_eliminar_entrevistador', [id, ''])
        
        # Obtener el resultado del stored procedure
        result_cursor = mysql.connection.cursor()
        result_cursor.execute("SELECT @p_resultado as resultado")
        result = result_cursor.fetchone()
        result_cursor.close()
        
        if 'exitosamente' in result['resultado']:
            mysql.connection.commit()
            flash('Entrevistador eliminado exitosamente', 'success')
        else:
            flash(result['resultado'], 'danger')
            
    except Exception as e:
        mysql.connection.rollback()
        print(f"Error en eliminación con SP: {e}")
        # Fallback a método original
        try:
            cursor.execute("SELECT COUNT(*) as total FROM entrevistas WHERE id_entrevistador = %s", (id,))
            result = cursor.fetchone()
            
            if result['total'] > 0:
                flash('No se puede eliminar el entrevistador porque tiene entrevistas asignadas', 'danger')
            else:
                cursor.execute("SELECT COUNT(*) as total FROM usuarios WHERE id_entrevistador = %s", (id,))
                user_result = cursor.fetchone()
                
                if user_result['total'] > 0:
                    flash('No se puede eliminar el entrevistador porque está asociado a un usuario del sistema', 'danger')
                else:
                    cursor.execute("DELETE FROM entrevistadores WHERE id_entrevistador = %s", (id,))
                    mysql.connection.commit()
                    flash('Entrevistador eliminado exitosamente', 'success')
                    
        except Exception as fallback_error:
            mysql.connection.rollback()
            flash(f'Error al eliminar entrevistador: {str(fallback_error)}', 'danger')
    finally:
        cursor.close()
    
    return redirect(url_for('entrevistadores'))

@app.route('/api/entrevistadores/<int:id>')
@login_required
def api_obtener_entrevistador(id):
    """API para obtener datos de un entrevistador específico usando stored procedure"""
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        # Usar stored procedure para obtener estadísticas del entrevistador
        cursor.callproc('sp_obtener_estadisticas_entrevistador', [id])
        entrevistador = cursor.fetchone()
        
        if entrevistador:
            return jsonify({
                'success': True,
                'entrevistador': entrevistador
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Entrevistador no encontrado'
            }), 404
    except Exception as e:
        print(f"Error en API obtener entrevistador: {e}")
        # Fallback a consulta directa
        try:
            cursor.execute("""
                SELECT e.*, r.nom_rol,
                       COUNT(ent.id_entrevista) as total_entrevistas,
                       AVG(ent.puntaje) as puntaje_promedio,
                       COUNT(CASE WHEN ent.fecha_entrevista >= CURDATE() THEN 1 END) as entrevistas_pendientes
                FROM entrevistadores e
                LEFT JOIN roles r ON e.id_rol = r.id_rol
                LEFT JOIN entrevistas ent ON e.id_entrevistador = ent.id_entrevistador
                WHERE e.id_entrevistador = %s
                GROUP BY e.id_entrevistador
            """, (id,))
            entrevistador = cursor.fetchone()
            
            if entrevistador:
                return jsonify({
                    'success': True,
                    'entrevistador': entrevistador
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'Entrevistador no encontrado'
                }), 404
        except Exception as fallback_error:
            return jsonify({
                'success': False,
                'message': f'Error: {str(fallback_error)}'
            }), 500
    finally:
        cursor.close()

@app.route('/api/entrevistadores/<int:id>/entrevistas')
@login_required
def api_entrevistador_entrevistas(id):
    """API para obtener las entrevistas de un entrevistador específico usando stored procedure"""
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        # Usar stored procedure para obtener próximas entrevistas del entrevistador
        cursor.callproc('sp_obtener_proximas_entrevistas_entrevistador', [id])
        entrevistas = cursor.fetchall()
        
        return jsonify({
            'success': True,
            'entrevistas': entrevistas
        })
    except Exception as e:
        print(f"Error en API entrevistador entrevistas: {e}")
        # Fallback a consulta directa
        try:
            cursor.execute("""
                SELECT 
                    e.id_entrevista,
                    e.fecha_entrevista,
                    c.nom_candidato,
                    v.titulo_vacante,
                    es.nom_estado as estado_entrevista,
                    es.id_estadoentrevista
                FROM entrevistas e
                JOIN postulaciones p ON e.id_postulacion = p.id_postulacion
                JOIN candidatos c ON p.id_candidato = c.id_candidato
                JOIN vacantes v ON p.id_vacante = v.id_vacante
                JOIN estados_entrevistas es ON e.id_estadoentrevista = es.id_estadoentrevista
                WHERE e.id_entrevistador = %s
                AND e.fecha_entrevista >= CURDATE()
                ORDER BY e.fecha_entrevista ASC
                LIMIT 10
            """, (id,))
            entrevistas = cursor.fetchall()
            
            return jsonify({
                'success': True,
                'entrevistas': entrevistas
            })
        except Exception as fallback_error:
            return jsonify({
                'success': False,
                'message': f'Error: {str(fallback_error)}'
            }), 500
    finally:
        cursor.close()

@app.route('/api/entrevistadores-estadisticas')
@login_required
def api_entrevistadores_estadisticas():
    """API para obtener estadísticas de entrevistadores usando stored procedure"""
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        # Usar stored procedure para obtener estadísticas de entrevistadores
        cursor.callproc('sp_obtener_estadisticas_entrevistadores')
        estadisticas = cursor.fetchall()
        
        return jsonify({
            'success': True,
            'estadisticas': estadisticas
        })
    except Exception as e:
        print(f"Error en API entrevistadores estadísticas: {e}")
        # Fallback a consulta directa
        try:
            cursor.execute("""
                SELECT 
                    e.id_entrevistador,
                    e.nom_entrevistador,
                    COUNT(ent.id_entrevista) as total_entrevistas,
                    AVG(ent.puntaje) as puntaje_promedio,
                    COUNT(CASE WHEN ent.fecha_entrevista >= CURDATE() THEN 1 END) as entrevistas_pendientes,
                    COUNT(CASE WHEN ent.id_estadoentrevista = 2 THEN 1 END) as entrevistas_completadas,
                    COUNT(CASE WHEN ent.id_estadoentrevista = 1 THEN 1 END) as entrevistas_programadas
                FROM entrevistadores e
                LEFT JOIN entrevistas ent ON e.id_entrevistador = ent.id_entrevistador
                GROUP BY e.id_entrevistador, e.nom_entrevistador
                ORDER BY total_entrevistas DESC
            """)
            estadisticas = cursor.fetchall()
            
            return jsonify({
                'success': True,
                'estadisticas': estadisticas
            })
        except Exception as fallback_error:
            return jsonify({
                'success': False,
                'message': f'Error: {str(fallback_error)}'
            }), 500
    finally:
        cursor.close()

# NUEVAS RUTAS ADICIONALES PARA ENTREVISTADORES

@app.route('/api/entrevistadores/<int:id>/entrevistas-completas')
@login_required
def api_entrevistador_entrevistas_completas(id):
    """API para obtener todas las entrevistas de un entrevistador usando stored procedure"""
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        # Usar stored procedure para obtener todas las entrevistas del entrevistador
        cursor.callproc('sp_obtener_entrevistas_entrevistador', [id])
        entrevistas = cursor.fetchall()
        
        return jsonify({
            'success': True,
            'entrevistas': entrevistas
        })
    except Exception as e:
        print(f"Error en API entrevistador entrevistas completas: {e}")
        # Fallback a consulta directa
        try:
            cursor.execute("""
                SELECT 
                    e.id_entrevista,
                    e.fecha_entrevista,
                    c.nom_candidato,
                    v.titulo_vacante,
                    es.nom_estado as estado_entrevista,
                    es.id_estadoentrevista,
                    e.puntaje,
                    CASE 
                        WHEN e.fecha_entrevista < CURDATE() THEN 'Pasada'
                        WHEN e.fecha_entrevista = CURDATE() THEN 'Hoy'
                        ELSE 'Futura'
                    END as tipo_fecha
                FROM entrevistas e
                JOIN postulaciones p ON e.id_postulacion = p.id_postulacion
                JOIN candidatos c ON p.id_candidato = c.id_candidato
                JOIN vacantes v ON p.id_vacante = v.id_vacante
                JOIN estados_entrevistas es ON e.id_estadoentrevista = es.id_estadoentrevista
                WHERE e.id_entrevistador = %s
                ORDER BY e.fecha_entrevista DESC
                LIMIT 20
            """, (id,))
            entrevistas = cursor.fetchall()
            
            return jsonify({
                'success': True,
                'entrevistas': entrevistas
            })
        except Exception as fallback_error:
            return jsonify({
                'success': False,
                'message': f'Error: {str(fallback_error)}'
            }), 500
    finally:
        cursor.close()

@app.route('/entrevistadores/<int:id>/perfil')
@login_required
@role_required([1, 2, 9])
def perfil_entrevistador(id):
    """Página de perfil del entrevistador con estadísticas completas"""
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        # Usar stored procedure para obtener estadísticas del entrevistador
        cursor.callproc('sp_obtener_estadisticas_entrevistador', [id])
        entrevistador = cursor.fetchone()
        
        if not entrevistador:
            flash('Entrevistador no encontrado', 'danger')
            return redirect(url_for('entrevistadores'))
        
        # Usar stored procedure para obtener entrevistas del entrevistador
        cursor.callproc('sp_obtener_entrevistas_entrevistador', [id])
        entrevistas = cursor.fetchall()
        
    except Exception as e:
        print(f"Error al cargar perfil del entrevistador: {e}")
        flash(f'Error al cargar perfil del entrevistador: {str(e)}', 'danger')
        return redirect(url_for('entrevistadores'))
    finally:
        cursor.close()
    
    return render_template('perfil_entrevistador.html',
                         entrevistador=entrevistador,
                         entrevistas=entrevistas)

@app.route('/entrevistadores/dashboard')
@login_required
@role_required([1, 2, 9])
def dashboard_entrevistadores():
    """Dashboard de entrevistadores con estadísticas generales"""
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        # Usar stored procedure para obtener estadísticas de entrevistadores
        cursor.callproc('sp_obtener_estadisticas_entrevistadores')
        estadisticas = cursor.fetchall()
        
        # Obtener total de entrevistadores
        cursor.execute("SELECT COUNT(*) as total FROM entrevistadores")
        total_entrevistadores = cursor.fetchone()['total']
        
    except Exception as e:
        print(f"Error en dashboard de entrevistadores: {e}")
        estadisticas = []
        total_entrevistadores = 0
    
    cursor.close()
    
    return render_template('dashboard_entrevistadores.html',
                         estadisticas=estadisticas,
                         total_entrevistadores=total_entrevistadores)

# RUTAS PARA USUARIOS DEL SISTEMA - VERSIÓN COMPLETA
@app.route('/usuarios')
@login_required
@role_required([1])  # Solo administradores
def usuarios():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        # QUITAR el filtro WHERE u.activo = 1 para mostrar todos los usuarios
        cursor.execute("""
            SELECT u.*, rs.nom_rol, e.nom_entrevistador,
                   CASE 
                       WHEN u.id_entrevistador IS NOT NULL THEN CONCAT('Entrevistador: ', e.nom_entrevistador)
                       ELSE 'Solo usuario sistema'
                   END as tipo_usuario
            FROM usuarios u 
            JOIN roles_sistema rs ON u.id_rolsistema = rs.id_rolsistema
            LEFT JOIN entrevistadores e ON u.id_entrevistador = e.id_entrevistador
            ORDER BY u.activo DESC, u.username  -- Ordenar por estado (activos primero)
        """)
        usuarios = cursor.fetchall()
        
        cursor.execute("SELECT * FROM roles_sistema ORDER BY nom_rol")
        roles = cursor.fetchall()
        
        cursor.execute("SELECT * FROM entrevistadores ORDER BY nom_entrevistador")
        entrevistadores = cursor.fetchall()
        
    except Exception as e:
        print(f"Error al cargar usuarios: {e}")
        flash(f'Error al cargar usuarios: {str(e)}', 'danger')
        usuarios = []
        roles = []
        entrevistadores = []
    cursor.close()
    return render_template('usuarios.html', 
                         usuarios=usuarios, 
                         roles=roles, 
                         entrevistadores=entrevistadores)

@app.route('/usuarios/crear', methods=['POST'])
@login_required
@role_required([1])  # Solo administradores
def crear_usuario():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        id_rolsistema = request.form['id_rolsistema']
        id_entrevistador = request.form.get('id_entrevistador', None)
        
        cursor = mysql.connection.cursor()
        try:
            # Verificar si el username o email ya existen
            cursor.execute("SELECT COUNT(*) as count FROM usuarios WHERE username = %s OR email = %s", 
                         (username, email))
            result = cursor.fetchone()
            
            if result['count'] > 0:
                flash('Error: El nombre de usuario o email ya existe', 'danger')
            else:
                # En un sistema real, deberías hashear la contraseña
                # Por ahora usamos texto plano para pruebas
                cursor.execute("""
                    INSERT INTO usuarios (username, hashed_pass, email, id_rolsistema, id_entrevistador, activo)
                    VALUES (%s, %s, %s, %s, %s, 1)
                """, (username, password, email, id_rolsistema, id_entrevistador))
                mysql.connection.commit()
                flash('Usuario creado exitosamente', 'success')
        except Exception as e:
            mysql.connection.rollback()
            flash(f'Error al crear usuario: {str(e)}', 'danger')
        finally:
            cursor.close()
    
    return redirect(url_for('usuarios'))

@app.route('/usuarios/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required([1])  # Solo administradores
def editar_usuario(id):
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        id_rolsistema = request.form['id_rolsistema']
        id_entrevistador = request.form.get('id_entrevistador', None)
        activo = 1 if request.form.get('activo') else 0
        
        # Manejar cambio de contraseña (opcional)
        nueva_password = request.form.get('nueva_password')
        
        cursor = mysql.connection.cursor()
        try:
            # Verificar si el username o email ya existen en otros usuarios
            cursor.execute("SELECT COUNT(*) as count FROM usuarios WHERE (username = %s OR email = %s) AND id_usuario != %s", 
                         (username, email, id))
            result = cursor.fetchone()
            
            if result['count'] > 0:
                flash('Error: El nombre de usuario o email ya existe para otro usuario', 'danger')
            else:
                if nueva_password:
                    # Actualizar con nueva contraseña
                    cursor.execute("""
                        UPDATE usuarios 
                        SET username = %s, email = %s, id_rolsistema = %s, 
                            id_entrevistador = %s, activo = %s, hashed_pass = %s
                        WHERE id_usuario = %s
                    """, (username, email, id_rolsistema, id_entrevistador, activo, nueva_password, id))
                else:
                    # Mantener contraseña actual
                    cursor.execute("""
                        UPDATE usuarios 
                        SET username = %s, email = %s, id_rolsistema = %s, 
                            id_entrevistador = %s, activo = %s
                        WHERE id_usuario = %s
                    """, (username, email, id_rolsistema, id_entrevistador, activo, id))
                
                mysql.connection.commit()
                flash('Usuario actualizado exitosamente', 'success')
        except Exception as e:
            mysql.connection.rollback()
            flash(f'Error al actualizar usuario: {str(e)}', 'danger')
        finally:
            cursor.close()
        
        return redirect(url_for('usuarios'))
    
    else:
        # GET request - mostrar formulario de edición
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        try:
            cursor.execute("""
                SELECT u.*, rs.nom_rol, e.nom_entrevistador
                FROM usuarios u 
                JOIN roles_sistema rs ON u.id_rolsistema = rs.id_rolsistema
                LEFT JOIN entrevistadores e ON u.id_entrevistador = e.id_entrevistador
                WHERE u.id_usuario = %s
            """, (id,))
            usuario = cursor.fetchone()
            
            cursor.execute("SELECT * FROM roles_sistema ORDER BY nom_rol")
            roles = cursor.fetchall()
            
            cursor.execute("SELECT * FROM entrevistadores ORDER BY nom_entrevistador")
            entrevistadores = cursor.fetchall()
            
        except Exception as e:
            flash(f'Error al cargar usuario: {str(e)}', 'danger')
            return redirect(url_for('usuarios'))
        finally:
            cursor.close()
        
        if not usuario:
            flash('Usuario no encontrado', 'danger')
            return redirect(url_for('usuarios'))
        
        return render_template('editar_usuario.html', 
                             usuario=usuario, 
                             roles=roles, 
                             entrevistadores=entrevistadores)

@app.route('/usuarios/eliminar/<int:id>', methods=['POST'])
@login_required
@role_required([1])  # Solo administradores
def eliminar_usuario(id):
    cursor = mysql.connection.cursor()
    try:
        # No permitir eliminar el propio usuario
        if id == session.get('id_usuario'):
            flash('No puede eliminar su propio usuario', 'danger')
        else:
            # En lugar de eliminar físicamente, marcamos como inactivo
            cursor.execute("UPDATE usuarios SET activo = 0 WHERE id_usuario = %s", (id,))
            mysql.connection.commit()
            flash('Usuario desactivado exitosamente', 'success')
    except Exception as e:
        mysql.connection.rollback()
        flash(f'Error al desactivar usuario: {str(e)}', 'danger')
    finally:
        cursor.close()
    
    return redirect(url_for('usuarios'))

@app.route('/usuarios/reactivar/<int:id>', methods=['POST'])
@login_required
@role_required([1])  # Solo administradores
def reactivar_usuario(id):
    cursor = mysql.connection.cursor()
    try:
        cursor.execute("UPDATE usuarios SET activo = 1 WHERE id_usuario = %s", (id,))
        mysql.connection.commit()
        flash('Usuario reactivado exitosamente', 'success')
    except Exception as e:
        mysql.connection.rollback()
        flash(f'Error al reactivar usuario: {str(e)}', 'danger')
    finally:
        cursor.close()
    
    return redirect(url_for('usuarios'))

@app.route('/api/usuarios/<int:id>')
@login_required
@role_required([1])  # Solo administradores
def api_obtener_usuario(id):
    """API para obtener datos de un usuario específico (para AJAX)"""
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        cursor.execute("""
            SELECT u.*, rs.nom_rol, e.nom_entrevistador
            FROM usuarios u 
            JOIN roles_sistema rs ON u.id_rolsistema = rs.id_rolsistema
            LEFT JOIN entrevistadores e ON u.id_entrevistador = e.id_entrevistador
            WHERE u.id_usuario = %s
        """, (id,))
        usuario = cursor.fetchone()
        
        if usuario:
            return jsonify({
                'success': True,
                'usuario': usuario
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Usuario no encontrado'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500
    finally:
        cursor.close()

# Ruta para perfil de usuario
@app.route('/mi-perfil')
@login_required
def mi_perfil():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        cursor.execute("""
            SELECT u.*, rs.nom_rol, e.nom_entrevistador
            FROM usuarios u 
            JOIN roles_sistema rs ON u.id_rolsistema = rs.id_rolsistema
            LEFT JOIN entrevistadores e ON u.id_entrevistador = e.id_entrevistador
            WHERE u.id_usuario = %s
        """, (session['id_usuario'],))
        usuario = cursor.fetchone()
    except Exception as e:
        flash(f'Error al cargar perfil: {str(e)}', 'danger')
        return redirect(url_for('dashboard'))
    finally:
        cursor.close()
    
    return render_template('mi_perfil.html', usuario=usuario)

@app.route('/actualizar-perfil', methods=['POST'])
@login_required
def actualizar_perfil():
    if request.method == 'POST':
        email = request.form['email']
        nueva_password = request.form.get('nueva_password')
        
        cursor = mysql.connection.cursor()
        try:
            # Verificar si el email ya existe en otros usuarios
            cursor.execute("SELECT COUNT(*) as count FROM usuarios WHERE email = %s AND id_usuario != %s", 
                         (email, session['id_usuario']))
            result = cursor.fetchone()
            
            if result['count'] > 0:
                flash('Error: El email ya existe para otro usuario', 'danger')
            else:
                if nueva_password:
                    # Actualizar email y contraseña
                    cursor.execute("""
                        UPDATE usuarios 
                        SET email = %s, hashed_pass = %s
                        WHERE id_usuario = %s
                    """, (email, nueva_password, session['id_usuario']))
                    flash('Perfil y contraseña actualizados exitosamente', 'success')
                else:
                    # Solo actualizar email
                    cursor.execute("""
                        UPDATE usuarios 
                        SET email = %s
                        WHERE id_usuario = %s
                    """, (email, session['id_usuario']))
                    flash('Perfil actualizado exitosamente', 'success')
                
                mysql.connection.commit()
        except Exception as e:
            mysql.connection.rollback()
            flash(f'Error al actualizar perfil: {str(e)}', 'danger')
        finally:
            cursor.close()
    
    return redirect(url_for('mi_perfil'))


# RUTAS PARA REPORTES - VERSIÓN MEJORADA CON HIGHCHARTS
@app.route('/reportes')
@login_required
@role_required([1, 11])
def reportes():
    return render_template('reportes.html')

@app.route('/api/reporte/conversion-fuente')
@login_required
def api_conversion_fuente():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        # Usar el stored procedure conversionFuentes
        cursor.callproc('conversionFuentes', ['2023-01-01', '2024-12-31'])
        data = cursor.fetchall()
        
        # Si el stored procedure no devuelve datos, usar la vista
        if not data:
            cursor.execute("SELECT * FROM vConversionPorFuente")
            data = cursor.fetchall()
            
    except Exception as e:
        print(f"Error en conversion-fuente: {e}")
        # Fallback a consulta directa
        cursor.execute("""
            SELECT 
                f.nom_fuente, 
                COUNT(DISTINCT c.id_candidato) as total_candidatos,
                COUNT(DISTINCT p.id_postulacion) as total_postulaciones,
                CASE 
                    WHEN COUNT(DISTINCT c.id_candidato) > 0 
                    THEN ROUND(COUNT(DISTINCT p.id_postulacion) / COUNT(DISTINCT c.id_candidato) * 100, 2)
                    ELSE 0 
                END as conversion_pct
            FROM fuentes f
            LEFT JOIN candidatos c ON f.id_fuente = c.id_fuente
            LEFT JOIN postulaciones p ON c.id_candidato = p.id_candidato
            GROUP BY f.id_fuente, f.nom_fuente
            ORDER BY conversion_pct DESC
        """)
        data = cursor.fetchall()
    finally:
        cursor.close()
    
    # Procesar datos para Highcharts
    categorias = []
    conversion_pct = []
    total_candidatos = []
    total_postulaciones = []
    
    for item in data:
        # Manejar diferentes nombres de columna
        fuente = item.get('nom_fuente', item.get('fuente', 'Desconocido'))
        conversion = item.get('conversion_pct', item.get('tasa_conversion', 0))
        candidatos = item.get('total_candidatos', 0)
        postulaciones = item.get('total_postulaciones', 0)
        
        categorias.append(fuente)
        conversion_pct.append(float(conversion))
        total_candidatos.append(int(candidatos))
        total_postulaciones.append(int(postulaciones))
    
    return jsonify({
        'categorias': categorias,
        'series': [
            {
                'name': 'Tasa de Conversión (%)',
                'data': conversion_pct,
                'type': 'column',
                'yAxis': 0
            },
            {
                'name': 'Total Candidatos',
                'data': total_candidatos,
                'type': 'spline',
                'yAxis': 1
            }
        ]
    })

@app.route('/api/reporte/pipeline-vacante')
@login_required
def api_pipeline_vacante():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        # Usar el stored procedure funnelVacante
        cursor.callproc('funnelVacante', [1])  # Puedes cambiar el ID según necesites
        data = cursor.fetchall()
        
        if not data:
            # Usar la vista si el stored procedure no devuelve datos
            cursor.execute("SELECT * FROM vpipelinePorVacante")
            data = cursor.fetchall()
            
    except Exception as e:
        print(f"Error en pipeline-vacante: {e}")
        # Consulta directa como fallback
        cursor.execute("""
            SELECT 
                e.nom_etapa as etapa,
                COUNT(p.id_postulacion) as cantidad
            FROM etapas e
            LEFT JOIN postulaciones p ON e.id_etapa = p.id_etapa
            GROUP BY e.id_etapa, e.nom_etapa
            ORDER BY e.id_etapa
        """)
        data = cursor.fetchall()
    finally:
        cursor.close()
    
    # Procesar datos para gráfico de embudo
    etapas = []
    cantidades = []
    
    for item in data:
        etapa = item.get('etapa', item.get('nom_etapa', 'Desconocida'))
        cantidad = item.get('cantidad', item.get('total_candidatos', 0))
        
        etapas.append(etapa)
        cantidades.append(int(cantidad))
    
    return jsonify({
        'etapas': etapas,
        'series': [{
            'name': 'Candidatos',
            'data': cantidades
        }]
    })

@app.route('/api/reporte/ofertas-mensuales')
@login_required
def api_ofertas_mensuales():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        # Usar la vista vOfertasEmitidasAceptadas
        cursor.execute("SELECT * FROM vOfertasEmitidasAceptadas ORDER BY anio, mes")
        data = cursor.fetchall()
        
    except Exception as e:
        print(f"Error en ofertas-mensuales: {e}")
        # Consulta directa como fallback
        cursor.execute("""
            SELECT 
                YEAR(o.fecha_emision) as anio,
                MONTH(o.fecha_emision) as mes,
                COUNT(*) as emitidas,
                SUM(CASE WHEN o.id_estadoferta = 2 THEN 1 ELSE 0 END) as aceptadas
            FROM ofertas o
            WHERE o.fecha_emision >= DATE_SUB(CURRENT_DATE, INTERVAL 12 MONTH)
            GROUP BY YEAR(o.fecha_emision), MONTH(o.fecha_emision)
            ORDER BY anio, mes
        """)
        data = cursor.fetchall()
    finally:
        cursor.close()
    
    # Procesar datos
    meses = []
    emitidas = []
    aceptadas = []
    
    for item in data:
        anio = item['anio']
        mes = item['mes']
        nombre_mes = f"{mes:02d}/{anio}"
        
        meses.append(nombre_mes)
        emitidas.append(item.get('emitidas', 0))
        aceptadas.append(item.get('aceptadas', 0))
    
    return jsonify({
        'meses': meses,
        'series': [
            {
                'name': 'Ofertas Emitidas',
                'data': emitidas,
                'color': '#3498db'
            },
            {
                'name': 'Ofertas Aceptadas', 
                'data': aceptadas,
                'color': '#2ecc71'
            }
        ]
    })

@app.route('/api/reporte/entrevistadores')
@login_required
def api_carga_entrevistadores():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        # Usar la vista vCargaEntrevistadores
        cursor.execute("SELECT * FROM vCargaEntrevistadores ORDER BY total_entrevistas DESC")
        data = cursor.fetchall()
        
    except Exception as e:
        print(f"Error en entrevistadores: {e}")
        # Consulta directa como fallback
        cursor.execute("""
            SELECT 
                e.nom_entrevistador,
                COUNT(ent.id_entrevista) as total_entrevistas
            FROM entrevistadores e
            LEFT JOIN entrevistas ent ON e.id_entrevistador = ent.id_entrevistador
            WHERE ent.fecha_entrevista >= DATE_SUB(CURRENT_DATE, INTERVAL 30 DAY)
            GROUP BY e.id_entrevistador, e.nom_entrevistador
            ORDER BY total_entrevistas DESC
        """)
        data = cursor.fetchall()
    finally:
        cursor.close()
    
    entrevistadores = []
    carga = []
    
    for item in data:
        entrevistadores.append(item['nom_entrevistador'])
        carga.append(item['total_entrevistas'])
    
    return jsonify({
        'entrevistadores': entrevistadores,
        'carga': carga
    })

@app.route('/api/reporte/tiempo-medio-etapa')
@login_required
def api_tiempo_medio_etapa():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        # Usar la vista vTiempoMedioPorEtapa
        cursor.execute("SELECT * FROM vTiempoMedioPorEtapa ORDER BY id_etapa")
        data = cursor.fetchall()
        
    except Exception as e:
        print(f"Error en tiempo-medio-etapa: {e}")
        # Consulta directa como fallback
        cursor.execute("""
            SELECT 
                e.nom_etapa,
                AVG(DATEDIFF(
                    COALESCE(
                        (SELECT MIN(p2.fecha_postula) 
                         FROM postulaciones p2 
                         WHERE p2.id_candidato = p.id_candidato 
                         AND p2.id_etapa > p.id_etapa),
                        CURRENT_DATE
                    ),
                    p.fecha_postula
                )) as tiempo_promedio
            FROM postulaciones p
            JOIN etapas e ON p.id_etapa = e.id_etapa
            WHERE p.fecha_postula >= DATE_SUB(CURRENT_DATE, INTERVAL 6 MONTH)
            GROUP BY e.id_etapa, e.nom_etapa
            ORDER BY e.id_etapa
        """)
        data = cursor.fetchall()
    finally:
        cursor.close()
    
    etapas = []
    tiempos = []
    
    for item in data:
        etapas.append(item['nom_etapa'])
        tiempos.append(float(item.get('tiempo_promedio', item.get('dias_promedio', 0))))
    
    return jsonify({
        'etapas': etapas,
        'series': [{
            'name': 'Días Promedio',
            'data': tiempos,
            'color': '#e74c3c'
        }]
    })

@app.route('/api/reporte/estadisticas-generales')
@login_required
def api_estadisticas_generales():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        # Obtener estadísticas generales
        cursor.execute("SELECT COUNT(*) as total FROM candidatos")
        total_candidatos = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(*) as total FROM vacantes WHERE id_estadovacante = 1")
        vacantes_activas = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(*) as total FROM vCandidatosEnProceso")
        en_proceso = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(*) as total FROM postulaciones WHERE id_etapa = 11")
        contratados = cursor.fetchone()['total']
        
        cursor.execute("SELECT AVG(time_to_fill) as promedio FROM vacantes WHERE time_to_fill IS NOT NULL")
        tiempo_promedio = cursor.fetchone()['promedio'] or 0
        
        return jsonify({
            'total_candidatos': total_candidatos,
            'vacantes_activas': vacantes_activas,
            'en_proceso': en_proceso,
            'contratados': contratados,
            'tiempo_promedio_contratacion': round(float(tiempo_promedio), 1)
        })
        
    except Exception as e:
        print(f"Error en estadisticas-generales: {e}")
        return jsonify({
            'total_candidatos': 0,
            'vacantes_activas': 0,
            'en_proceso': 0,
            'contratados': 0,
            'tiempo_promedio_contratacion': 0
        })
    finally:
        cursor.close()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)