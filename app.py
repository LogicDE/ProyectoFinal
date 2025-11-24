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
# RUTAS PARA CANDIDATOS - VERSIÓN COMPLETA
@app.route('/candidatos')
@login_required
@role_required([1, 2, 9, 10])
def candidatos():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        # Usar stored procedure para obtener candidatos
        cursor.callproc('candidatoCrearActualizar', [None, None, None, None, None, None, 'SELECT'])
        candidatos = cursor.fetchall()
        
        # Obtener fuentes para el formulario
        cursor.execute("SELECT * FROM fuentes")
        fuentes = cursor.fetchall()
    except Exception as e:
        print(f"Error al cargar candidatos: {e}")
        # Fallback a consulta directa
        cursor.execute("SELECT c.*, f.nom_fuente FROM candidatos c LEFT JOIN fuentes f ON c.id_fuente = f.id_fuente")
        candidatos = cursor.fetchall()
        cursor.execute("SELECT * FROM fuentes")
        fuentes = cursor.fetchall()
    cursor.close()
    return render_template('candidatos.html', candidatos=candidatos, fuentes=fuentes)

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
            cursor.execute("SELECT c.*, f.nom_fuente FROM candidatos c LEFT JOIN fuentes f ON c.id_fuente = f.id_fuente WHERE c.id_candidato = %s", (id,))
            candidato = cursor.fetchone()
            
            cursor.execute("SELECT * FROM fuentes")
            fuentes = cursor.fetchall()
        except Exception as e:
            flash(f'Error al cargar candidato: {str(e)}', 'danger')
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
        # Verificar si el candidato tiene postulaciones antes de eliminar
        cursor.execute("SELECT COUNT(*) as total FROM postulaciones WHERE id_candidato = %s", (id,))
        result = cursor.fetchone()
        
        if result['total'] > 0:
            flash('No se puede eliminar el candidato porque tiene postulaciones activas', 'danger')
        else:
            # Llamar al stored procedure para eliminar candidato
            cursor.execute("DELETE FROM candidatos WHERE id_candidato = %s", (id,))
            mysql.connection.commit()
            flash('Candidato eliminado exitosamente', 'success')
    except Exception as e:
        mysql.connection.rollback()
        flash(f'Error al eliminar candidato: {str(e)}', 'danger')
    finally:
        cursor.close()
    
    return redirect(url_for('candidatos'))

@app.route('/api/candidatos/<int:id>')
@login_required
def api_obtener_candidato(id):
    """API para obtener datos de un candidato específico (para AJAX)"""
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
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
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500
    finally:
        cursor.close()

@app.route('/api/candidatos-descartados')
@login_required
def api_candidatos_descartados():
    """API para obtener candidatos descartados"""
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        cursor.execute("SELECT * FROM vCandidatosDescartados")
        data = cursor.fetchall()
        
        return jsonify({
            'success': True,
            'candidatos': data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500
    finally:
        cursor.close()


# RUTAS PARA VACANTES - VERSIÓN CORREGIDA
@app.route('/vacantes')
@login_required
@role_required([1, 2, 9, 10])
def vacantes():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        # Obtener vacantes con información adicional usando JOINs
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
        
        # Obtener departamentos para el formulario
        cursor.execute("SELECT * FROM departamentos ORDER BY nom_departamento")
        departamentos = cursor.fetchall()
        
        # Obtener estados de vacantes para el formulario
        cursor.execute("SELECT * FROM estados_vacantes ORDER BY id_estadovacante")
        estados_vacantes = cursor.fetchall()
        
    except Exception as e:
        print(f"Error al cargar vacantes: {e}")
        flash(f'Error al cargar vacantes: {str(e)}', 'danger')
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
        except Exception as e:
            flash(f'Error al cargar vacante: {str(e)}', 'danger')
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
        # Verificar si la vacante tiene postulaciones antes de eliminar
        cursor.execute("SELECT COUNT(*) as total FROM postulaciones WHERE id_vacante = %s", (id,))
        result = cursor.fetchone()
        
        if result['total'] > 0:
            flash('No se puede eliminar la vacante porque tiene postulaciones activas', 'danger')
        else:
            # Realizar la eliminación directamente con una consulta DELETE
            cursor.execute("DELETE FROM vacantes WHERE id_vacante = %s", (id,))
            mysql.connection.commit()
            flash('Vacante eliminada exitosamente', 'success')
    except Exception as e:
        mysql.connection.rollback()
        flash(f'Error al eliminar vacante: {str(e)}', 'danger')
    finally:
        cursor.close()
    
    return redirect(url_for('vacantes'))

@app.route('/api/vacantes/<int:id>')
@login_required
def api_obtener_vacante(id):
    """API para obtener datos de una vacante específica (para AJAX)"""
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
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
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500
    finally:
        cursor.close()

# RUTAS PARA POSTULACIONES
# RUTAS PARA POSTULACIONES - VERSIÓN COMPLETA
@app.route('/postulaciones')
@login_required
@role_required([1, 2, 9, 10])
def postulaciones():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        # Obtener postulaciones con información adicional
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
        
        # Obtener candidatos para el formulario
        cursor.execute("SELECT id_candidato, nom_candidato, email FROM candidatos ORDER BY nom_candidato")
        candidatos = cursor.fetchall()
        
        # Obtener vacantes para el formulario
        cursor.execute("SELECT id_vacante, titulo_vacante FROM vacantes ORDER BY titulo_vacante")
        vacantes = cursor.fetchall()
        
        # Obtener etapas para el formulario
        cursor.execute("SELECT id_etapa, nom_etapa FROM etapas ORDER BY id_etapa")
        etapas = cursor.fetchall()
    except Exception as e:
        print(f"Error al cargar postulaciones: {e}")
        flash(f'Error al cargar postulaciones: {str(e)}', 'danger')
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
            # Llamar al stored procedure para crear postulación
            cursor.callproc('postular', [id_candidato, id_vacante])
            
            # Si se especificó una etapa diferente a la inicial, actualizarla
            if id_etapa != 1:
                cursor.execute(
                    "UPDATE postulaciones SET id_etapa = %s WHERE id_candidato = %s AND id_vacante = %s",
                    (id_etapa, id_candidato, id_vacante)
                )
            
            mysql.connection.commit()
            flash('Postulación creada exitosamente', 'success')
        except Exception as e:
            mysql.connection.rollback()
            error_msg = str(e)
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
        
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        try:
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
            
            # Realizar la transición directamente con una consulta SQL
            cursor.execute(
                "UPDATE postulaciones SET id_etapa = %s WHERE id_postulacion = %s",
                (nueva_etapa, id)
            )
            mysql.connection.commit()
            flash('Etapa actualizada exitosamente', 'success')
        except Exception as e:
            mysql.connection.rollback()
            flash(f'Error al actualizar etapa: {str(e)}', 'danger')
        finally:
            cursor.close()
    
    return redirect(url_for('postulaciones'))

@app.route('/postulaciones/eliminar/<int:id>', methods=['POST'])
@login_required
@role_required([1, 2, 9])
def eliminar_postulacion(id):
    cursor = mysql.connection.cursor()
    try:
        # Iniciar transacción para asegurar la integridad de los datos
        mysql.connection.begin()
        
        # Verificar si existen entrevistas asociadas y eliminarlas primero
        cursor.execute("SELECT COUNT(*) as count FROM entrevistas WHERE id_postulacion = %s", (id,))
        entrevistas_count = cursor.fetchone()['count']
        
        if entrevistas_count > 0:
            # Eliminar las entrevistas asociadas
            cursor.execute("DELETE FROM entrevistas WHERE id_postulacion = %s", (id,))
            flash(f'Se eliminaron {entrevistas_count} entrevistas asociadas', 'info')
        
        # Verificar si existen ofertas asociadas y eliminarlas
        cursor.execute("SELECT COUNT(*) as count FROM ofertas WHERE id_postulacion = %s", (id,))
        ofertas_count = cursor.fetchone()['count']
        
        if ofertas_count > 0:
            # Eliminar las ofertas asociadas
            cursor.execute("DELETE FROM ofertas WHERE id_postulacion = %s", (id,))
            flash(f'Se eliminaron {ofertas_count} ofertas asociadas', 'info')
        
        # Ahora eliminar la postulación
        cursor.execute("DELETE FROM postulaciones WHERE id_postulacion = %s", (id,))
        
        # Confirmar la transacción
        mysql.connection.commit()
        flash('Postulación eliminada exitosamente', 'success')
    except Exception as e:
        # Revertir la transacción en caso de error
        mysql.connection.rollback()
        flash(f'Error al eliminar postulación: {str(e)}', 'danger')
    finally:
        cursor.close()
    
    return redirect(url_for('postulaciones'))

@app.route('/api/postulaciones/<int:id>')
@login_required
def api_obtener_postulacion(id):
    """API para obtener datos de una postulación específica (para AJAX)"""
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
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
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500
    finally:
        cursor.close()

@app.route('/api/etapas')
@login_required
def api_obtener_etapas():
    """API para obtener todas las etapas (para AJAX)"""
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        cursor.execute("SELECT id_etapa, nom_etapa FROM etapas ORDER BY id_etapa")
        etapas = cursor.fetchall()
        
        return jsonify({
            'success': True,
            'etapas': etapas
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500
    finally:
        cursor.close()

# RUTAS PARA ENTREVISTAS - VERSIÓN COMPLETA Y MEJORADA
@app.route('/entrevistas')
@login_required
@role_required([1, 2, 9, 10])
def entrevistas():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        # Obtener entrevistas con información completa
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
        
        # Datos para formularios
        cursor.execute("""
            SELECT p.id_postulacion, c.nom_candidato, v.titulo_vacante,
                   CONCAT(c.nom_candidato, ' - ', v.titulo_vacante) as descripcion
            FROM postulaciones p
            JOIN candidatos c ON p.id_candidato = c.id_candidato
            JOIN vacantes v ON p.id_vacante = v.id_vacante
            WHERE p.id_etapa NOT IN (11,12)  -- Excluir etapas finales
            ORDER BY c.nom_candidato
        """)
        postulaciones = cursor.fetchall()
        
        cursor.execute("SELECT * FROM entrevistadores ORDER BY nom_entrevistador")
        entrevistadores = cursor.fetchall()
        
        cursor.execute("SELECT * FROM estados_entrevistas ORDER BY id_estadoentrevista")
        estados_entrevista = cursor.fetchall()
        
    except Exception as e:
        print(f"Error al cargar entrevistas: {e}")
        flash(f'Error al cargar entrevistas: {str(e)}', 'danger')
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
        id_estadoentrevista = request.form.get('id_estadoentrevista', 1)  # Programada por defecto
        notas = request.form.get('notas', '')

        # Combinar fecha y hora para crear un datetime completo
        fecha_hora = f"{fecha_entrevista} {hora_entrevista}"

        cursor = mysql.connection.cursor()
        try:
            # VERIFICAR SI EL STORED PROCEDURE EXISTE
            cursor.execute("SHOW PROCEDURE STATUS LIKE 'programarEntrevista'")
            sp_exists = cursor.fetchone()
            
            if sp_exists:
                # CORRECCIÓN: Pasar los parámetros en el orden correcto según la definición del SP
                # [id_postulacion, id_entrevistador, fecha_hora]
                cursor.callproc('programarEntrevista', [id_postulacion, id_entrevistador, fecha_hora])
                
                # Obtener el ID de la última entrevista insertada
                cursor.execute("SELECT LAST_INSERT_ID() as id_entrevista")
                id_entrevista_recien_creada = cursor.fetchone()['id_entrevista']
                
                # Actualizar el estado y las notas si se proporcionaron
                if id_estadoentrevista != 1 or notas:
                    cursor.execute("""
                        UPDATE entrevistas 
                        SET id_estadoentrevista = %s, notas = %s
                        WHERE id_entrevista = %s
                    """, (id_estadoentrevista, notas, id_entrevista_recien_creada))
            else:
                # Si no existe el SP, usar inserción directa
                cursor.execute("""
                    INSERT INTO entrevistas (id_postulacion, fecha_entrevista, id_entrevistador, id_estadoentrevista, notas)
                    VALUES (%s, %s, %s, %s, %s)
                """, (id_postulacion, fecha_hora, id_entrevistador, id_estadoentrevista, notas))
            
            mysql.connection.commit()
            flash('Entrevista programada exitosamente', 'success')
            
        except Exception as e:
            mysql.connection.rollback()
            error_msg = str(e)
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
        
        # Combinar fecha y hora
        fecha_hora = f"{fecha_entrevista} {hora_entrevista}"
        
        cursor = mysql.connection.cursor()
        try:
            cursor.execute("""
                UPDATE entrevistas 
                SET fecha_entrevista = %s, id_entrevistador = %s, 
                    id_estadoentrevista = %s, notas = %s
                WHERE id_entrevista = %s
            """, (fecha_hora, id_entrevistador, id_estadoentrevista, notas, id))
            
            mysql.connection.commit()
            flash('Entrevista actualizada exitosamente', 'success')
        except Exception as e:
            mysql.connection.rollback()
            flash(f'Error al actualizar entrevista: {str(e)}', 'danger')
        finally:
            cursor.close()
        
        return redirect(url_for('entrevistas'))
    
    else:
        # GET request - mostrar formulario de edición
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
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
            
        except Exception as e:
            flash(f'Error al cargar entrevista: {str(e)}', 'danger')
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
        id_estadoentrevista = request.form.get('id_estadoentrevista', 3)  # Completada por defecto
        
        cursor = mysql.connection.cursor()
        try:
            # Verificar si la entrevista existe
            cursor.execute("SELECT id_entrevista FROM entrevistas WHERE id_entrevista = %s", (id,))
            if not cursor.fetchone():
                flash('Entrevista no encontrada', 'danger')
                return redirect(url_for('entrevistas'))
            
            # Usar el stored procedure para registrar feedback
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
    
    # Para el método GET, obtener los estados de entrevista y mostrar el formulario
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        cursor.execute("SELECT * FROM estados_entrevistas ORDER BY id_estadoentrevista")
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
        # Verificar si la entrevista existe
        cursor.execute("SELECT id_entrevista FROM entrevistas WHERE id_entrevista = %s", (id,))
        if not cursor.fetchone():
            flash('Entrevista no encontrada', 'danger')
            return redirect(url_for('entrevistas'))
        
        # Eliminar la entrevista
        cursor.execute("DELETE FROM entrevistas WHERE id_entrevista = %s", (id,))
        mysql.connection.commit()
        flash('Entrevista eliminada exitosamente', 'success')
    except Exception as e:
        mysql.connection.rollback()
        flash(f'Error al eliminar entrevista: {str(e)}', 'danger')
    finally:
        cursor.close()
    
    return redirect(url_for('entrevistas'))

@app.route('/api/entrevistas/<int:id>')
@login_required
def api_obtener_entrevista(id):
    """API para obtener datos de una entrevista específica (para AJAX)"""
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        # Consulta más simple y robusta
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
        print(f"Error detallado en api_obtener_entrevista: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor al cargar los detalles de la entrevista'
        }), 500
    finally:
        cursor.close()

# Ruta para obtener postulaciones disponibles para entrevistas (API)
@app.route('/api/postulaciones-entrevistables')
@login_required
def api_postulaciones_entrevistables():
    """API para obtener postulaciones que pueden tener entrevistas"""
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        cursor.execute("""
            SELECT p.id_postulacion, c.nom_candidato, v.titulo_vacante,
                   CONCAT(c.nom_candidato, ' - ', v.titulo_vacante) as descripcion,
                   e.nom_etapa as etapa_actual
            FROM postulaciones p
            JOIN candidatos c ON p.id_candidato = c.id_candidato
            JOIN vacantes v ON p.id_vacante = v.id_vacante
            JOIN etapas e ON p.id_etapa = e.id_etapa
            WHERE p.id_etapa NOT IN (11,12)  -- Excluir etapas finales
            AND NOT EXISTS (
                SELECT 1 FROM entrevistas ent 
                WHERE ent.id_postulacion = p.id_postulacion 
                AND ent.id_estadoentrevista IN (1, 2)  -- Excluir si ya tiene entrevista programada o en progreso
            )
            ORDER BY c.nom_candidato
        """)
        postulaciones = cursor.fetchall()
        
        return jsonify({
            'success': True,
            'postulaciones': postulaciones
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500
    finally:
        cursor.close()

@app.route('/api/entrevistas-semana')
@login_required
def api_entrevistas_semana():
    """API para obtener entrevistas de la semana"""
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        cursor.execute("SELECT * FROM vEntrevistasSemana")
        data = cursor.fetchall()
        
        return jsonify({
            'success': True,
            'entrevistas': data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500
    finally:
        cursor.close()



# RUTAS PARA OFERTAS - VERSIÓN COMPLETA Y MEJORADA
@app.route('/ofertas')
@login_required
@role_required([1, 2, 9, 10])
def ofertas():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        # Obtener ofertas con información completa - CORREGIDO
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
        
        # Datos para formularios - CORREGIDO
        cursor.execute("""
            SELECT p.id_postulacion, c.nom_candidato, v.titulo_vacante,
                   CONCAT(c.nom_candidato, ' - ', v.titulo_vacante) as descripcion,
                   e.nom_etapa as etapa_actual
            FROM postulaciones p
            JOIN candidatos c ON p.id_candidato = c.id_candidato
            JOIN vacantes v ON p.id_vacante = v.id_vacante
            JOIN etapas e ON p.id_etapa = e.id_etapa
            WHERE p.id_etapa >= 4  -- Incluir etapas finales (4, 5, etc.)
            AND NOT EXISTS (
                SELECT 1 FROM ofertas o 
                WHERE o.id_postulacion = p.id_postulacion 
                AND o.id_estadoferta IN (1)  -- Excluir si ya tiene oferta pendiente
            )
            ORDER BY c.nom_candidato
        """)
        postulaciones = cursor.fetchall()
        
        cursor.execute("SELECT * FROM estados_ofertas ORDER BY id_estadoferta")
        estados_oferta = cursor.fetchall()
        
    except Exception as e:
        print(f"Error al cargar ofertas: {e}")
        flash(f'Error al cargar ofertas: {str(e)}', 'danger')
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
        id_estadoferta = request.form.get('id_estadoferta', 1)  # Pendiente por defecto
        
        cursor = mysql.connection.cursor()
        try:
            # VERIFICAR SI EL STORED PROCEDURE EXISTE
            cursor.execute("SHOW PROCEDURE STATUS LIKE 'ofertaEmitir'")
            sp_exists = cursor.fetchone()
            
            if sp_exists:
                # CORRECCIÓN: El SP espera solo 2 parámetros: [id_postulacion, monto_oferta]
                cursor.callproc('ofertaEmitir', [id_postulacion, monto_oferta])
                
                # Obtener el ID de la última oferta insertada
                cursor.execute("SELECT LAST_INSERT_ID() as id_oferta")
                id_oferta_recien_creada = cursor.fetchone()['id_oferta']
                
                # Actualizar el estado si se proporcionó uno diferente
                if id_estadoferta != 1:
                    cursor.execute("""
                        UPDATE ofertas 
                        SET id_estadoferta = %s
                        WHERE id_oferta = %s
                    """, (id_estadoferta, id_oferta_recien_creada))
            else:
                # Si no existe el SP, usar inserción directa
                cursor.execute("""
                    INSERT INTO ofertas (id_postulacion, monto_oferta, id_estadoferta)
                    VALUES (%s, %s, %s)
                """, (id_postulacion, monto_oferta, id_estadoferta))
            
            mysql.connection.commit()
            flash('Oferta emitida exitosamente', 'success')
            
        except Exception as e:
            mysql.connection.rollback()
            error_msg = str(e)
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
            cursor.execute("""
                UPDATE ofertas 
                SET monto_oferta = %s, id_estadoferta = %s, notas = %s
                WHERE id_oferta = %s
            """, (monto_oferta, id_estadoferta, notas, id))
            
            mysql.connection.commit()
            flash('Oferta actualizada exitosamente', 'success')
        except Exception as e:
            mysql.connection.rollback()
            flash(f'Error al actualizar oferta: {str(e)}', 'danger')
        finally:
            cursor.close()
        
        return redirect(url_for('ofertas'))
    
    else:
        # GET request - mostrar formulario de edición
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
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
            
        except Exception as e:
            flash(f'Error al cargar oferta: {str(e)}', 'danger')
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
            # VERIFICAR SI EL STORED PROCEDURE EXISTE
            cursor.execute("SHOW PROCEDURE STATUS LIKE 'ofertaDecidir'")
            sp_exists = cursor.fetchone()
            
            if sp_exists:
                # Llamar al stored procedure para decidir oferta
                cursor.callproc('ofertaDecidir', [id, id_estadoferta])
            else:
                # Si no existe el SP, usar actualización directa
                cursor.execute("""
                    UPDATE ofertas 
                    SET id_estadoferta = %s, fecha_decision = NOW()
                    WHERE id_oferta = %s
                """, (id_estadoferta, id))
            
            mysql.connection.commit()
            
            # Mensaje según el estado
            if id_estadoferta == '2':
                flash('Oferta marcada como ACEPTADA exitosamente', 'success')
            elif id_estadoferta == '3':
                flash('Oferta marcada como RECHAZADA exitosamente', 'warning')
            else:
                flash('Decisión de oferta registrada exitosamente', 'success')
                
        except Exception as e:
            mysql.connection.rollback()
            flash(f'Error al registrar decisión de oferta: {str(e)}', 'danger')
        finally:
            cursor.close()
    
    return redirect(url_for('ofertas'))

@app.route('/ofertas/eliminar/<int:id>', methods=['POST'])
@login_required
@role_required([1, 2, 9])
def eliminar_oferta(id):
    cursor = mysql.connection.cursor()
    try:
        # Verificar si la oferta existe
        cursor.execute("SELECT id_oferta FROM ofertas WHERE id_oferta = %s", (id,))
        if not cursor.fetchone():
            flash('Oferta no encontrada', 'danger')
            return redirect(url_for('ofertas'))
        
        # Verificar el estado de la oferta antes de eliminar
        cursor.execute("SELECT id_estadoferta FROM ofertas WHERE id_oferta = %s", (id,))
        oferta = cursor.fetchone()
        
        if oferta and oferta['id_estadoferta'] in [2, 3]:  # Aceptada o Rechazada
            flash('No se puede eliminar una oferta que ya ha sido decidida', 'danger')
        else:
            # Eliminar la oferta
            cursor.execute("DELETE FROM ofertas WHERE id_oferta = %s", (id,))
            mysql.connection.commit()
            flash('Oferta eliminada exitosamente', 'success')
    except Exception as e:
        mysql.connection.rollback()
        flash(f'Error al eliminar oferta: {str(e)}', 'danger')
    finally:
        cursor.close()
    
    return redirect(url_for('ofertas'))

# RUTAS PARA ESTADOS DE OFERTAS (si no existen)
@app.route('/estados-ofertas')
@login_required
@role_required([1, 2, 9])
def estados_ofertas():
    """Gestión de estados de ofertas (solo administradores)"""
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        cursor.execute("SELECT * FROM estados_ofertas ORDER BY id_estadoferta")
        estados = cursor.fetchall()
    except Exception as e:
        flash(f'Error al cargar estados de ofertas: {str(e)}', 'danger')
        estados = []
    cursor.close()
    return render_template('estados_ofertas.html', estados=estados)

# Ruta para reportes de ofertas
@app.route('/reportes/ofertas')
@login_required
@role_required([1, 2, 9])
def reportes_ofertas():
    """Reportes específicos de ofertas"""
    return render_template('reportes_ofertas.html')


@app.route('/api/ofertas/<int:id>')
@login_required
def api_obtener_oferta(id):
    """API para obtener datos de una oferta específica (para AJAX)"""
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
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
            # Convertir objetos datetime a strings para JSON (solo fecha_decision existe)
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
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500
    finally:
        cursor.close()

# Ruta para obtener postulaciones disponibles para ofertas (API)
@app.route('/api/postulaciones-ofertables')
@login_required
def api_postulaciones_ofertables():
    """API para obtener postulaciones que pueden recibir ofertas (etapa finalista)"""
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
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
            WHERE p.id_etapa = 5  -- Solo etapa finalista
            AND NOT EXISTS (
                SELECT 1 FROM ofertas o 
                WHERE o.id_postulacion = p.id_postulacion 
                AND o.id_estadoferta IN (1)  -- Excluir si ya tiene oferta pendiente
            )
            ORDER BY c.nom_candidato
        """)
        postulaciones = cursor.fetchall()
        
        return jsonify({
            'success': True,
            'postulaciones': postulaciones
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500
    finally:
        cursor.close()

@app.route('/api/estadisticas-ofertas')
@login_required
def api_estadisticas_ofertas():
    """API para obtener estadísticas de ofertas - CORREGIDO SIN fecha_emision"""
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        # Obtener estadísticas generales de ofertas
        cursor.execute("SELECT COUNT(*) as total FROM ofertas")
        total_ofertas = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(*) as total FROM ofertas WHERE id_estadoferta = 1")
        ofertas_pendientes = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(*) as total FROM ofertas WHERE id_estadoferta = 2")
        ofertas_aceptadas = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(*) as total FROM ofertas WHERE id_estadoferta = 3")
        ofertas_rechazadas = cursor.fetchone()['total']
        
        # Obtener monto promedio de ofertas aceptadas
        cursor.execute("SELECT AVG(monto_oferta) as promedio FROM ofertas WHERE id_estadoferta = 2")
        monto_promedio = cursor.fetchone()['promedio'] or 0
        
        # Obtener tasa de aceptación
        if total_ofertas > 0:
            tasa_aceptacion = (ofertas_aceptadas / total_ofertas) * 100
        else:
            tasa_aceptacion = 0
        
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
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500
    finally:
        cursor.close()

# Ruta para dashboard de ofertas
@app.route('/ofertas/dashboard')
@login_required
@role_required([1, 2, 9, 10])
def dashboard_ofertas():
    """Dashboard específico para ofertas"""
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        # Obtener ofertas recientes - ORDENADO POR ID en lugar de fecha_emision
        cursor.execute("""
            SELECT o.*, c.nom_candidato, v.titulo_vacante, eo.nom_estado as estado_oferta
            FROM ofertas o
            JOIN postulaciones p ON o.id_postulacion = p.id_postulacion
            JOIN candidatos c ON p.id_candidato = c.id_candidato
            JOIN vacantes v ON p.id_vacante = v.id_vacante
            JOIN estados_ofertas eo ON o.id_estadoferta = eo.id_estadoferta
            ORDER BY o.id_oferta DESC
            LIMIT 10
        """)
        ofertas_recientes = cursor.fetchall()
        
        # Obtener estadísticas rápidas - SIN fecha_emision
        cursor.execute("SELECT COUNT(*) as total FROM ofertas WHERE id_estadoferta = 1")
        pendientes = cursor.fetchone()['total']
        
        cursor.execute("SELECT AVG(monto_oferta) as promedio FROM ofertas WHERE id_estadoferta = 2")
        monto_promedio = cursor.fetchone()['promedio'] or 0
        
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


# RUTA PARA CALENDARIO
@app.route('/calendario')
@login_required
def calendario():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        cursor.execute("""
            SELECT e.id_entrevista, e.fecha_entrevista, c.nom_candidato, v.titulo_vacante, 
                   ent.nom_entrevistador, es.nom_estado as estado_entrevista,
                   CONCAT(c.nom_candidato, ' - ', v.titulo_vacante) as title,
                   e.fecha_entrevista as start,
                   DATE_ADD(e.fecha_entrevista, INTERVAL 1 HOUR) as end
            FROM entrevistas e
            JOIN postulaciones p ON e.id_postulacion = p.id_postulacion
            JOIN candidatos c ON p.id_candidato = c.id_candidato
            JOIN vacantes v ON p.id_vacante = v.id_vacante
            JOIN entrevistadores ent ON e.id_entrevistador = ent.id_entrevistador
            JOIN estados_entrevistas es ON e.id_estadoentrevista = es.id_estadoentrevista
            WHERE e.fecha_entrevista >= CURDATE()
            ORDER BY e.fecha_entrevista
        """)
        eventos = cursor.fetchall()
    except Exception as e:
        print(f"Error al cargar calendario: {e}")
        eventos = []
    
    cursor.close()
    return render_template('calendario.html', eventos=eventos)


# RUTAS PARA ENTREVISTADORES
@app.route('/entrevistadores')
@login_required
@role_required([1, 2, 9])
def entrevistadores():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        cursor.execute("""
            SELECT e.*, COUNT(ent.id_entrevista) as total_entrevistas
            FROM entrevistadores e
            LEFT JOIN entrevistas ent ON e.id_entrevistador = ent.id_entrevistador
            GROUP BY e.id_entrevistador
            ORDER BY e.nom_entrevistador
        """)
        entrevistadores = cursor.fetchall()
    except Exception as e:
        print(f"Error al cargar entrevistadores: {e}")
        flash(f'Error al cargar entrevistadores: {str(e)}', 'danger')
        entrevistadores = []
    cursor.close()
    return render_template('entrevistadores.html', entrevistadores=entrevistadores)

@app.route('/entrevistadores/crear', methods=['POST'])
@login_required
@role_required([1, 2, 9])
def crear_entrevistador():
    if request.method == 'POST':
        nom_entrevistador = request.form['nom_entrevistador']
        email = request.form.get('email', '')
        telefono = request.form.get('telefono', '')
        especialidad = request.form.get('especialidad', '')
        
        cursor = mysql.connection.cursor()
        try:
            cursor.execute("""
                INSERT INTO entrevistadores (nom_entrevistador, email, telefono, especialidad)
                VALUES (%s, %s, %s, %s)
            """, (nom_entrevistador, email, telefono, especialidad))
            mysql.connection.commit()
            flash('Entrevistador creado exitosamente', 'success')
        except Exception as e:
            mysql.connection.rollback()
            flash(f'Error al crear entrevistador: {str(e)}', 'danger')
        finally:
            cursor.close()
    
    return redirect(url_for('entrevistadores'))

@app.route('/entrevistadores/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required([1, 2, 9])
def editar_entrevistador(id):
    if request.method == 'POST':
        nom_entrevistador = request.form['nom_entrevistador']
        email = request.form.get('email', '')
        telefono = request.form.get('telefono', '')
        especialidad = request.form.get('especialidad', '')
        
        cursor = mysql.connection.cursor()
        try:
            cursor.execute("""
                UPDATE entrevistadores 
                SET nom_entrevistador = %s, email = %s, telefono = %s, especialidad = %s
                WHERE id_entrevistador = %s
            """, (nom_entrevistador, email, telefono, especialidad, id))
            mysql.connection.commit()
            flash('Entrevistador actualizado exitosamente', 'success')
        except Exception as e:
            mysql.connection.rollback()
            flash(f'Error al actualizar entrevistador: {str(e)}', 'danger')
        finally:
            cursor.close()
        
        return redirect(url_for('entrevistadores'))
    
    else:
        # GET request - mostrar formulario de edición
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        try:
            cursor.execute("SELECT * FROM entrevistadores WHERE id_entrevistador = %s", (id,))
            entrevistador = cursor.fetchone()
        except Exception as e:
            flash(f'Error al cargar entrevistador: {str(e)}', 'danger')
            return redirect(url_for('entrevistadores'))
        finally:
            cursor.close()
        
        if not entrevistador:
            flash('Entrevistador no encontrado', 'danger')
            return redirect(url_for('entrevistadores'))
        
        return render_template('editar_entrevistador.html', entrevistador=entrevistador)

@app.route('/entrevistadores/eliminar/<int:id>', methods=['POST'])
@login_required
@role_required([1, 2, 9])
def eliminar_entrevistador(id):
    cursor = mysql.connection.cursor()
    try:
        # Verificar si el entrevistador tiene entrevistas asignadas
        cursor.execute("SELECT COUNT(*) as total FROM entrevistas WHERE id_entrevistador = %s", (id,))
        result = cursor.fetchone()
        
        if result['total'] > 0:
            flash('No se puede eliminar el entrevistador porque tiene entrevistas asignadas', 'danger')
        else:
            cursor.execute("DELETE FROM entrevistadores WHERE id_entrevistador = %s", (id,))
            mysql.connection.commit()
            flash('Entrevistador eliminado exitosamente', 'success')
    except Exception as e:
        mysql.connection.rollback()
        flash(f'Error al eliminar entrevistador: {str(e)}', 'danger')
    finally:
        cursor.close()
    
    return redirect(url_for('entrevistadores'))

# RUTAS PARA USUARIOS DEL SISTEMA - VERSIÓN COMPLETA
@app.route('/usuarios')
@login_required
@role_required([1])  # Solo administradores
def usuarios():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        cursor.execute("""
            SELECT u.*, rs.nom_rol, e.nom_entrevistador,
                   CASE 
                       WHEN u.id_entrevistador IS NOT NULL THEN CONCAT('Entrevistador: ', e.nom_entrevistador)
                       ELSE 'Solo usuario sistema'
                   END as tipo_usuario
            FROM usuarios u 
            JOIN roles_sistema rs ON u.id_rolsistema = rs.id_rolsistema
            LEFT JOIN entrevistadores e ON u.id_entrevistador = e.id_entrevistador
            WHERE u.activo = 1
            ORDER BY u.username
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