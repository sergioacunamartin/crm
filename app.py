from flask import Flask, render_template, request, redirect, url_for, flash, session
from flaskext.mysql import MySQL
from datetime import datetime, date, timedelta
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
mysql=MySQL()
#Conexión con la base de datos
app.config['MYSQL_DATABASE_HOST']='localhost'
app.config['MYSQL_DATABASE_USER']='root'
app.config['MYSQL_DATABAE_PASSWORD']='123456'
app.config['MYSQL_DATABASE_DB']='crm'
mysql.init_app(app)
#login
@app.route('/', methods=['POST', 'GET'])
def login():
    if session.get('logeado') == True and session.get('level') == "Admin":
        return redirect('/admin/tareas')
    elif session.get('logeado') == True and session.get('level') == "Trabajador":
        return redirect('/trabajador/')
    elif session.get('logeado') == True and session.get('level') == "Cliente":
        return redirect('/cliente/')
    else:
        if request.method == "POST":
            email = request.form['email']
            password = request.form['pass']
            # Chequear que existe el email
            conexion = mysql.connect()
            cursor = conexion.cursor()
            cursor.execute("SELECT * FROM `cuentas` WHERE email=%s", (email))
            cuenta = cursor.fetchone()
            if cuenta is None:
                flash(f'No existe una cuenta con el email {email}', 'errorUser')
            elif not check_password_hash(cuenta[3], password):
                flash(f'La cuenta con el email {email} existe pero la contraseña es incorrecta ', 'errorPass')
            else:
                session['logeado'] = True
                session['username'] = cuenta[1]
                session['level'] = cuenta[4]
                if session['level'] == "Admin":
                    return redirect('/admin/tareas')
                elif session['level'] == "Trabajador":
                    return redirect('/trabajador/')
                elif session['level'] == "Cliente":
                    return redirect('/cliente/')
        return render_template("login.html")

#logOut
@app.route('/logout')
def logout():
    session.pop('logeado', None)
    session.pop('username', None)
    session.pop('level', None)
    return redirect('/')

#Administración de tareas*******************
@app.route('/admin/tareas/')
def admin_tareas():
    if session.get('logeado') == None:
        return redirect('/')
    elif session.get('logeado') == True and session.get('level') != "Admin":
        return redirect('/')
    else:
        fechaActual = datetime.today()
        conexion = mysql.connect()
        cursor = conexion.cursor()
        cursor.execute("SELECT id, fechaFin, estado FROM `tareas` ")
        fechasFin = cursor.fetchall()

        for fechaFin in fechasFin:
            diferenciaFecha = fechaFin[1] - fechaActual
            diferenciaFecha = int(diferenciaFecha.days)
            if diferenciaFecha >= 6:
                sql = "UPDATE tareas SET prioridad=%s WHERE id=%s;"
                datos = ("Baja", fechaFin[0])
                conexion = mysql.connect()
                cursor = conexion.cursor()
                # Se ejecuta el sql y los datos "values".
                cursor.execute(sql, datos)
                conexion.commit()
            elif diferenciaFecha == 5 or diferenciaFecha == 4:
                sql = "UPDATE tareas SET prioridad=%s WHERE id=%s;"
                datos = ("Media", fechaFin[0])
                conexion = mysql.connect()
                cursor = conexion.cursor()
                # Se ejecuta el sql y los datos "values".
                cursor.execute(sql, datos)
                conexion.commit()
            elif diferenciaFecha < 4:
                sql = "UPDATE tareas SET prioridad=%s WHERE id=%s;"
                datos = ("Alta", fechaFin[0])
                conexion = mysql.connect()
                cursor = conexion.cursor()
                # Se ejecuta el sql y los datos "values".
                cursor.execute(sql, datos)
                conexion.commit()
            if diferenciaFecha <= 0:
                sql = "UPDATE tareas SET prioridad=%s WHERE id=%s;"
                datos = ("Agotada", fechaFin[0])
                conexion = mysql.connect()
                cursor = conexion.cursor()
                # Se ejecuta el sql y los datos "values".
                cursor.execute(sql, datos)
                conexion.commit()
            if fechaFin[2] == "Finalizada":
                    sql = "UPDATE tareas SET prioridad=%s WHERE id=%s;"
                    datos = ("Ninguna", fechaFin[0])
                    cursor.execute(sql, datos)
                    conexion.commit()

        usuario = session.get('username')

        conexion = mysql.connect()
        cursor = conexion.cursor()

        cursor.execute("SELECT * FROM `tareas` INNER JOIN `trabajadores` ON tareas.idTrabajador=trabajadores.id INNER JOIN `clientes` ON tareas.idCliente=clientes.id ORDER BY tareas.Fecha DESC")
        tareas=cursor.fetchall()
        conexion.commit()

        if len(tareas) == 0:
            diferenciaFecha = 0;

        cursor.execute("SELECT * FROM `trabajadores` WHERE trabajadores.nombre!='admin'")
        trabajadores=cursor.fetchall()
        conexion.commit()

        cursor.execute("SELECT * FROM `clientes`")
        clientes = cursor.fetchall()
        conexion.commit()

        cursor.execute("SELECT id FROM `cuentas` WHERE cuentas.username=%s", (usuario))
        idCuentaUsuarioLogeado = cursor.fetchone()
        conexion.commit()

        cursor.execute("SELECT id FROM `trabajadores` WHERE idCT=%s", idCuentaUsuarioLogeado)
        idUsuarioLogeado = cursor.fetchone()
        conexion.commit()

        cursor.execute("SELECT * FROM `cuentas` WHERE cuentas.id=%s", idCuentaUsuarioLogeado)
        datosCuenta = cursor.fetchone()
        conexion.commit()

        cursor.execute("SELECT * FROM `trabajadores` WHERE trabajadores.id=%s", idUsuarioLogeado)
        datosTrabajador = cursor.fetchone()
        conexion.commit()

        cursor.execute("SELECT COUNT(prioridad) FROM tareas WHERE prioridad=%s", "Alta")
        tareasAlta = cursor.fetchone()
        conexion.commit()

        cursor.execute("SELECT COUNT(prioridad) FROM tareas WHERE prioridad=%s", "Media")
        tareasMedia = cursor.fetchone()
        conexion.commit()

        cursor.execute("SELECT COUNT(prioridad) FROM tareas WHERE prioridad=%s", "Baja")
        tareasBaja = cursor.fetchone()
        conexion.commit()

        cursor.execute("SELECT COUNT(estado) FROM tareas WHERE estado=%s", "Finalizada")
        tareasFinalizadas = cursor.fetchone()
        conexion.commit()

        return render_template('admin/tareas.html', tareas=tareas, trabajadores=trabajadores,
            clientes=clientes, idUsuarioLogeado=idUsuarioLogeado, tareasAlta=tareasAlta,
            tareasMedia=tareasMedia, tareasBaja=tareasBaja, tareasFinalizadas=tareasFinalizadas,
            datosTrabajador=datosTrabajador, datosCuenta=datosCuenta, diferenciaFecha=diferenciaFecha)

#FILTROS DE TAREAS
#Por nombre de trabajador
@app.route('/admin/tareas/ordenar-nombre-trabajador/')
def tareas_nombre_trabajador():
    if session.get('logeado') == None:
        return redirect('/')
    elif session.get('logeado') == True and session.get('level') != "Admin":
        return redirect('/')
    else:
        usuario = session.get('username')

        conexion = mysql.connect()
        cursor = conexion.cursor()
        cursor.execute("SELECT * FROM `tareas` INNER JOIN `trabajadores` ON tareas.idTrabajador=trabajadores.id INNER JOIN `clientes` ON tareas.idCliente=clientes.id ORDER BY trabajadores.nombre;")
        tareas = cursor.fetchall()
        conexion.commit()

        cursor.execute("SELECT * FROM `trabajadores` WHERE trabajadores.nombre!='admin'")
        trabajadores = cursor.fetchall()
        conexion.commit()

        cursor.execute("SELECT * FROM `clientes`")
        clientes = cursor.fetchall()
        conexion.commit()

        cursor.execute("SELECT id FROM `cuentas` WHERE cuentas.username=%s", (usuario))
        idCuentaUsuarioLogeado = cursor.fetchone()
        conexion.commit()

        cursor.execute("SELECT id FROM `trabajadores` WHERE idCT=%s", idCuentaUsuarioLogeado)
        idUsuarioLogeado = cursor.fetchone()
        conexion.commit()

        cursor.execute("SELECT * FROM `cuentas` WHERE cuentas.id=%s", idCuentaUsuarioLogeado)
        datosCuenta = cursor.fetchone()
        conexion.commit()

        cursor.execute("SELECT * FROM `trabajadores` WHERE trabajadores.id=%s", idUsuarioLogeado)
        datosTrabajador = cursor.fetchone()
        conexion.commit()

        cursor.execute("SELECT COUNT(prioridad) FROM tareas WHERE prioridad=%s", "Alta")
        tareasAlta = cursor.fetchone()
        conexion.commit()

        cursor.execute("SELECT COUNT(prioridad) FROM tareas WHERE prioridad=%s", "Media")
        tareasMedia = cursor.fetchone()
        conexion.commit()

        cursor.execute("SELECT COUNT(prioridad) FROM tareas WHERE prioridad=%s", "Baja")
        tareasBaja = cursor.fetchone()
        conexion.commit()

        cursor.execute("SELECT COUNT(estado) FROM tareas WHERE estado=%s", "Finalizada")
        tareasFinalizadas = cursor.fetchone()
        conexion.commit()

        return render_template('admin/tareas.html', tareas=tareas, trabajadores=trabajadores,
                           clientes=clientes, idUsuarioLogeado=idUsuarioLogeado, tareasAlta=tareasAlta,
                           tareasMedia=tareasMedia, tareasBaja=tareasBaja, tareasFinalizadas=tareasFinalizadas,
                           datosTrabajador=datosTrabajador, datosCuenta=datosCuenta)

#Por Prioridad
@app.route('/admin/tareas/ordenar-prioridad/')
def tareas_prioridad():
    if session.get('logeado') == None:
        return redirect('/')
    elif session.get('logeado') == True and session.get('level') != "Admin":
        return redirect('/')
    else:
        usuario = session.get('username')

        conexion = mysql.connect()
        cursor = conexion.cursor()
        cursor.execute("SELECT * FROM `tareas` INNER JOIN `trabajadores` ON tareas.idTrabajador=trabajadores.id INNER JOIN `clientes` ON tareas.idCliente=clientes.id ORDER BY case when prioridad = 'Alta' then 1 when prioridad = 'Media' then 2 when prioridad = 'Baja' then 3 when prioridad = 'Ninguna' then 4 end asc;")
        tareas = cursor.fetchall()
        conexion.commit()

        cursor.execute("SELECT * FROM `trabajadores` WHERE trabajadores.nombre!='admin'")
        trabajadores = cursor.fetchall()
        conexion.commit()

        cursor.execute("SELECT * FROM `clientes`")
        clientes = cursor.fetchall()
        conexion.commit()

        cursor.execute("SELECT id FROM `cuentas` WHERE cuentas.username=%s", (usuario))
        idCuentaUsuarioLogeado = cursor.fetchone()
        conexion.commit()

        cursor.execute("SELECT id FROM `trabajadores` WHERE idCT=%s", idCuentaUsuarioLogeado)
        idUsuarioLogeado = cursor.fetchone()
        conexion.commit()

        cursor.execute("SELECT * FROM `cuentas` WHERE cuentas.id=%s", idCuentaUsuarioLogeado)
        datosCuenta = cursor.fetchone()
        conexion.commit()

        cursor.execute("SELECT * FROM `trabajadores` WHERE trabajadores.id=%s", idUsuarioLogeado)
        datosTrabajador = cursor.fetchone()
        conexion.commit()

        cursor.execute("SELECT COUNT(prioridad) FROM tareas WHERE prioridad=%s", "Alta")
        tareasAlta = cursor.fetchone()
        conexion.commit()

        cursor.execute("SELECT COUNT(prioridad) FROM tareas WHERE prioridad=%s", "Media")
        tareasMedia = cursor.fetchone()
        conexion.commit()

        cursor.execute("SELECT COUNT(prioridad) FROM tareas WHERE prioridad=%s", "Baja")
        tareasBaja = cursor.fetchone()
        conexion.commit()

        cursor.execute("SELECT COUNT(estado) FROM tareas WHERE estado=%s", "Finalizada")
        tareasFinalizadas = cursor.fetchone()
        conexion.commit()

        return render_template('admin/tareas.html', tareas=tareas, trabajadores=trabajadores,
                               clientes=clientes, idUsuarioLogeado=idUsuarioLogeado, tareasAlta=tareasAlta,
                               tareasMedia=tareasMedia, tareasBaja=tareasBaja, tareasFinalizadas=tareasFinalizadas,
                               datosTrabajador=datosTrabajador, datosCuenta=datosCuenta)

#Por Estado
@app.route('/admin/tareas/ordenar-estado/')
def tareas_estado():
    if session.get('logeado') == None:
        return redirect('/')
    elif session.get('logeado') == True and session.get('level') != "Admin":
        return redirect('/')
    else:
        usuario = session.get('username')

        conexion = mysql.connect()
        cursor = conexion.cursor()
        cursor.execute("SELECT * FROM `tareas` INNER JOIN `trabajadores` ON tareas.idTrabajador=trabajadores.id INNER JOIN `clientes` ON tareas.idCliente=clientes.id ORDER BY case when estado = 'Por Empezar' then 1 when estado = 'En proceso' then 2 when estado = 'Finalizada' then 3 end asc;")
        tareas = cursor.fetchall()
        conexion.commit()

        cursor.execute("SELECT * FROM `trabajadores` WHERE trabajadores.nombre!='admin'")
        trabajadores = cursor.fetchall()
        conexion.commit()

        cursor.execute("SELECT * FROM `clientes`")
        clientes = cursor.fetchall()
        conexion.commit()

        cursor.execute("SELECT id FROM `cuentas` WHERE cuentas.username=%s", (usuario))
        idCuentaUsuarioLogeado = cursor.fetchone()
        conexion.commit()

        cursor.execute("SELECT id FROM `trabajadores` WHERE idCT=%s", idCuentaUsuarioLogeado)
        idUsuarioLogeado = cursor.fetchone()
        conexion.commit()

        cursor.execute("SELECT * FROM `cuentas` WHERE cuentas.id=%s", idCuentaUsuarioLogeado)
        datosCuenta = cursor.fetchone()
        conexion.commit()

        cursor.execute("SELECT * FROM `trabajadores` WHERE trabajadores.id=%s", idUsuarioLogeado)
        datosTrabajador = cursor.fetchone()
        conexion.commit()

        cursor.execute("SELECT COUNT(prioridad) FROM tareas WHERE prioridad=%s", "Alta")
        tareasAlta = cursor.fetchone()
        conexion.commit()

        cursor.execute("SELECT COUNT(prioridad) FROM tareas WHERE prioridad=%s", "Media")
        tareasMedia = cursor.fetchone()
        conexion.commit()

        cursor.execute("SELECT COUNT(prioridad) FROM tareas WHERE prioridad=%s", "Baja")
        tareasBaja = cursor.fetchone()
        conexion.commit()

        cursor.execute("SELECT COUNT(estado) FROM tareas WHERE estado=%s", "Finalizada")
        tareasFinalizadas = cursor.fetchone()
        conexion.commit()

        return render_template('admin/tareas.html', tareas=tareas, trabajadores=trabajadores,
                               clientes=clientes, idUsuarioLogeado=idUsuarioLogeado, tareasAlta=tareasAlta,
                               tareasMedia=tareasMedia, tareasBaja=tareasBaja, tareasFinalizadas=tareasFinalizadas,
                               datosTrabajador=datosTrabajador, datosCuenta=datosCuenta)

#Por Cliente
@app.route('/admin/tareas/cliente/')
def tareas_cliente():
    if session.get('logeado') == None:
        return redirect('/')
    elif session.get('logeado') == True and session.get('level') != "Admin":
        return redirect('/')
    else:
        usuario = session.get('username')

        conexion = mysql.connect()
        cursor = conexion.cursor()
        cursor.execute("SELECT * FROM `tareas` INNER JOIN `trabajadores` ON tareas.idTrabajador=trabajadores.id INNER JOIN `clientes` ON tareas.idCliente=clientes.id ORDER BY clientes.nombreEmpresa;")
        tareas = cursor.fetchall()
        conexion.commit()

        cursor.execute("SELECT * FROM `trabajadores` WHERE trabajadores.nombre!='admin'")
        trabajadores = cursor.fetchall()
        conexion.commit()

        cursor.execute("SELECT * FROM `clientes`")
        clientes = cursor.fetchall()
        conexion.commit()

        cursor.execute("SELECT id FROM `cuentas` WHERE cuentas.username=%s", (usuario))
        idCuentaUsuarioLogeado = cursor.fetchone()
        conexion.commit()

        cursor.execute("SELECT id FROM `trabajadores` WHERE idCT=%s", idCuentaUsuarioLogeado)
        idUsuarioLogeado = cursor.fetchone()
        conexion.commit()

        cursor.execute("SELECT * FROM `cuentas` WHERE cuentas.id=%s", idCuentaUsuarioLogeado)
        datosCuenta = cursor.fetchone()
        conexion.commit()

        cursor.execute("SELECT * FROM `trabajadores` WHERE trabajadores.id=%s", idUsuarioLogeado)
        datosTrabajador = cursor.fetchone()
        conexion.commit()

        cursor.execute("SELECT COUNT(prioridad) FROM tareas WHERE prioridad=%s", "Alta")
        tareasAlta = cursor.fetchone()
        conexion.commit()

        cursor.execute("SELECT COUNT(prioridad) FROM tareas WHERE prioridad=%s", "Media")
        tareasMedia = cursor.fetchone()
        conexion.commit()

        cursor.execute("SELECT COUNT(prioridad) FROM tareas WHERE prioridad=%s", "Baja")
        tareasBaja = cursor.fetchone()
        conexion.commit()

        cursor.execute("SELECT COUNT(estado) FROM tareas WHERE estado=%s", "Finalizada")
        tareasFinalizadas = cursor.fetchone()
        conexion.commit()

        return render_template('admin/tareas.html', tareas=tareas, trabajadores=trabajadores,
                               clientes=clientes, idUsuarioLogeado=idUsuarioLogeado, tareasAlta=tareasAlta,
                               tareasMedia=tareasMedia, tareasBaja=tareasBaja, tareasFinalizadas=tareasFinalizadas,
                               datosTrabajador=datosTrabajador, datosCuenta=datosCuenta)

#Borrar Tarea
@app.route('/admin/tareas/borrar/<int:id>')
def admin_tareas_borrar(id):
    #nos conectamos y de nuevo y borramos el registro
    conexion = mysql.connect()
    cursor = conexion.cursor()
    cursor.execute("SELECT titulo FROM `tareas` WHERE id=%s", id)
    tituloTareaBorrar = cursor.fetchone()
    cursor.execute("DELETE FROM `tareas` WHERE id=%s", id)
    flash(f"Tarea {tituloTareaBorrar[0]} borrada", "tarea-borrada")
    conexion.commit()
    return redirect('/admin/tareas')

#Editar Tarea
@app.route('/admin/tareas/editar/<int:id>')
def admin_tareas_editar(id):
    conexion = mysql.connect()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM `tareas` INNER JOIN `trabajadores` ON tareas.idTrabajador=trabajadores.id INNER JOIN `clientes` ON tareas.idCliente=clientes.id WHERE tareas.id=%s", (id))
    tareas = cursor.fetchall()
    conexion.commit()

    cursor.execute("SELECT * FROM `trabajadores`")
    trabajadores = cursor.fetchall()
    conexion.commit()

    cursor.execute("SELECT * FROM `clientes`")
    clientes = cursor.fetchall()
    conexion.commit()

    return render_template('/admin/editar_tarea.html', tareas=tareas, trabajadores=trabajadores, clientes=clientes)

#Actualizar Tarea
@app.route('/admin/tareas/actualizar/', methods=['POST'])
def admin_actualizar_tareas():
    idTarea = int(request.form['txtId'])
    idCliente = request.form['selectCliente']
    nuevoIdCliente = request.form['selectNuevoCliente']
    idTrabajador = request.form['selectTrabajador']
    nuevoIdTrabajador = request.form['selectNuevoTrabajador']
    tituloTarea = request.form['txtTitulo']
    nuevoTituloTarea = request.form['txtNuevoTitulo']
    descripcionTarea = request.form['txtDescripcion']
    nuevaDescripcionTarea = request.form['txtNuevaDescripcion']
    estadoTarea = request.form['selectEstado']
    nuevoEstadoTarea = request.form['selectNuevoEstado']
    prioridadTarea = request.form['selectPrioridad']
    nuevaPrioridadTarea = request.form['selectNuevaPrioridad']

    datosActuales = [idCliente, idTrabajador, tituloTarea, descripcionTarea, estadoTarea, prioridadTarea]
    datosNuevos = [nuevoIdCliente, nuevoIdTrabajador, nuevoTituloTarea, nuevaDescripcionTarea, nuevoEstadoTarea, nuevaPrioridadTarea]

    fechaActual = datetime.today()

    if datosActuales == datosNuevos:
        flash(f"No ha habido cambios en la tarea {nuevoTituloTarea}", "tarea-sin-cambios")
        return redirect('/admin/tareas')
    else:
        if nuevaPrioridadTarea == "Ninguna" and nuevoEstadoTarea != "Finalizada":
            flash(f"Una tarea con la prioridad 'ninguna' solo puede tener el estado 'finalizada'", "tarea-ninguna")
        else:
            if nuevaPrioridadTarea == prioridadTarea:
                sql = "UPDATE tareas SET idTrabajador=%s, idCliente=%s, titulo=%s, descripcion=%s, estado=%s, prioridad=%s WHERE id=%s;"
                datos = (nuevoIdTrabajador, nuevoIdCliente, nuevoTituloTarea, nuevaDescripcionTarea, nuevoEstadoTarea, nuevaPrioridadTarea, idTarea)
                conexion = mysql.connect()
                cursor = conexion.cursor()
                # Se ejecuta el sql y los datos "values".
                cursor.execute(sql, datos)
                flash(f"Tarea {nuevoTituloTarea} actualizada", "actualizada")
                conexion.commit()
            else:
                if nuevaPrioridadTarea == "Alta":
                    fechaFin = fechaActual + timedelta(3)
                    sql = "UPDATE tareas SET idTrabajador=%s, idCliente=%s, titulo=%s, descripcion=%s, estado=%s, prioridad=%s, fechaFin=%s, fechaUltimaActualizacion=%s WHERE id=%s;"
                    datos = (nuevoIdTrabajador, nuevoIdCliente, nuevoTituloTarea, nuevaDescripcionTarea, nuevoEstadoTarea, nuevaPrioridadTarea, fechaFin, fechaActual, idTarea)
                    conexion = mysql.connect()
                    cursor = conexion.cursor()
                    # Se ejecuta el sql y los datos "values".
                    cursor.execute(sql, datos)
                    flash(f"Tarea {nuevoTituloTarea} actualizada", "actualizada")
                    conexion.commit()
                elif nuevaPrioridadTarea == "Media":
                        fechaFin = fechaActual + timedelta(5)
                        sql = "UPDATE tareas SET idTrabajador=%s, idCliente=%s, titulo=%s, descripcion=%s, estado=%s, prioridad=%s, fechaFin=%s, fechaUltimaActualizacion=%s WHERE id=%s;"
                        datos = (nuevoIdTrabajador, nuevoIdCliente, nuevoTituloTarea, nuevaDescripcionTarea, nuevoEstadoTarea, nuevaPrioridadTarea, fechaFin, fechaActual, idTarea)
                        conexion = mysql.connect()
                        cursor = conexion.cursor()
                        # Se ejecuta el sql y los datos "values".
                        cursor.execute(sql, datos)
                        flash(f"Tarea {nuevoTituloTarea} actualizada", "actualizada")
                        conexion.commit()
                else:
                    fechaFin = fechaActual + timedelta(7)
                    sql = "UPDATE tareas SET idTrabajador=%s, idCliente=%s, titulo=%s, descripcion=%s, estado=%s, prioridad=%s, fechaFin=%s, fechaUltimaActualizacion=%s WHERE id=%s;"
                    datos = (nuevoIdTrabajador, nuevoIdCliente, nuevoTituloTarea, nuevaDescripcionTarea, nuevoEstadoTarea, nuevaPrioridadTarea, fechaFin, fechaActual, idTarea)
                    conexion = mysql.connect()
                    cursor = conexion.cursor()
                    # Se ejecuta el sql y los datos "values".
                    cursor.execute(sql, datos)
                    flash(f"Tarea {nuevoTituloTarea} actualizada", "actualizada")
                    conexion.commit()
    return redirect('/admin/tareas/')

#Guardar Tarea
@app.route('/admin/tareas/guardar', methods=['POST'])
def admin_tareas_guardar():
    idCliente = request.form['selectGuardarCliente']
    idTrabajador=request.form['selectGuardarTrabajador']
    fecha = datetime.now()
    tituloTarea=request.form['txtGuardarTitulo']
    descripcionTarea=request.form['txtGuardarDescripcion']
    estadoTarea=request.form['selectGuardarEstado']
    prioridadTarea=request.form['selectGuardarPrioridad']

    diasLimitePrioridadBaja = timedelta(7)
    diasLimitePrioridadMedia = timedelta(5)
    diasLimitePrioridadAlta = timedelta(3)

    if prioridadTarea == "Alta":
        fechaLimite = fecha + diasLimitePrioridadAlta
    elif prioridadTarea == "Media":
        fechaLimite = fecha + diasLimitePrioridadMedia
    else:
        fechaLimite = fecha + diasLimitePrioridadBaja

    sql="INSERT INTO `tareas` (`id`, `idTrabajador`, `idCliente`, `fecha`, `titulo`, `descripcion`, `estado`, `prioridad`, `FechaFin`, `FechaUltimaActualizacion`) VALUES (NULL,%s,%s,%s,%s,%s,%s,%s,%s,%s);"
    datos=(idTrabajador, idCliente, fecha, tituloTarea, descripcionTarea, estadoTarea, prioridadTarea, fechaLimite, fecha)
    conexion = mysql.connect()
    cursor = conexion.cursor()
    #Se ejecuta el sql y los datos "values".
    cursor.execute(sql, datos)
    flash(f"Tarea {tituloTarea} guardada", "guardada")
    conexion.commit()

    return redirect('/admin/tareas')

#Administración trabajadores*******************************************************************************************
@app.route('/admin/trabajadores/')
def admin_trabajadores():
    if session.get('logeado') == None:
        return redirect('/')
    elif session.get('logeado') == True and session.get('level') != "Admin":
        return redirect('/')
    else:
        usuario = session.get('username')

        conexion = mysql.connect()
        cursor = conexion.cursor()

        cursor.execute("SELECT id FROM `cuentas` WHERE cuentas.username=%s", usuario)
        idCuentaUsuarioLogeado = cursor.fetchone()
        conexion.commit()

        cursor.execute("SELECT id FROM `trabajadores` WHERE idCT=%s", idCuentaUsuarioLogeado)
        idUsuarioLogeado = cursor.fetchone()
        conexion.commit()

        cursor.execute("SELECT * FROM `trabajadores` INNER JOIN `cuentas` ON trabajadores.idCT=cuentas.id WHERE cuentas.username!='admin' ORDER BY trabajadores.nombre")
        trabajadores=cursor.fetchall()
        print(trabajadores)
        conexion.commit()
        return render_template('admin/trabajadores.html', trabajadores=trabajadores,  idUsuarioLogeado=idUsuarioLogeado)

@app.route('/admin/trabajadores/guardar', methods=['POST', 'GET'])
def admin_trabajadores_guardar():
    if request.method == "POST":
        nombreTrabajador = request.form['txtGuardarNombre']
        dptoTrabajador = request.form['selectGuardarDepartamento']
        usuarioTrabajador = request.form['txtGuardarUsuario']
        emailTrabajador = request.form['txtGuardarEmail']
        passTrabajador = request.form['txtGuardarPass']
        nivelTrabajador = request.form['selectGuardarNivel']

        #Chequear si el email o el usuario existe
        conexion = mysql.connect()
        cursor = conexion.cursor()
        cursor.execute("SELECT email FROM `cuentas` WHERE email=%s", (emailTrabajador))
        email = cursor.fetchone()
        cursor.execute("SELECT username FROM `cuentas` WHERE username=%s", (usuarioTrabajador))
        username = cursor.fetchone()
        if email is None and username is None:
            cursor.execute("INSERT INTO `cuentas` VALUES (NULL,%s,%s,%s,%s);", (usuarioTrabajador, emailTrabajador, generate_password_hash(passTrabajador), nivelTrabajador))
            conexion.commit()
            cursor.execute("SELECT id FROM `cuentas` WHERE email=%s", (emailTrabajador))
            idCuentaTrabajador = cursor.fetchone()
            cursor.execute("INSERT INTO `trabajadores` VALUES (NULL,%s,%s,%s);", (idCuentaTrabajador, nombreTrabajador, dptoTrabajador))
            conexion.commit()
            flash(f"Trabajador {nombreTrabajador} registrado", "trabajador-guardado")
        elif email is not None and username is not None:
            flash(f"El email {emailTrabajador} y el usuario {usuarioTrabajador} ya existen", "email-usuario-existe")
        elif email is not None:
            flash(f"El email {emailTrabajador} ya existe", "email-existe")
        elif username is not None:
            flash(f"El usuario {usuarioTrabajador} ya existe", "usuario-existe")

    return redirect('/admin/trabajadores')

@app.route('/admin/trabajadores/borrar/<int:id>')
def admin_trabajadores_borrar(id):
    conexion = mysql.connect()
    cursor = conexion.cursor()
    cursor.execute("SELECT nombre FROM `trabajadores` WHERE trabajadores.id=%s", (id))
    nombreTrabajador = cursor.fetchone()
    cursor.execute("SELECT idTrabajador FROM `tareas` WHERE tareas.idTrabajador=%s", (id))
    idTrabajadorTarea = cursor.fetchone()
    if idTrabajadorTarea is None:
        flash(f"El trabajador {nombreTrabajador[0]} ha sido borrado", "trabajador-borrado")
        cursor.execute("SELECT idCT FROM `trabajadores` WHERE id=%s", (id))
        idCuentaTrabajador = cursor.fetchone()
        cursor.execute("DELETE FROM `trabajadores` WHERE id=%s", (id))
        conexion.commit()
        cursor.execute("DELETE FROM `cuentas` WHERE id=%s", (idCuentaTrabajador))
        conexion.commit()   
    else:
        flash(f"El trabajador {nombreTrabajador[0]} está asignado a una o más tareas y no se puede borrar", "trabajador-asignado")
    return redirect('/admin/trabajadores')

@app.route('/admin/trabajadores/actualizar/', methods=['POST'])
def admin_actualizar_trabajadores():
    idTrabajador = int(request.form['txtId'])
    idCT = int(request.form['txtIdCT'])
    nombreTrabajador = request.form['txtNombre']
    nuevoNombreTrabajador = request.form['txtNuevoNombre']
    dptoTrabajador = request.form['selectDepartamento']
    nuevoDptoTrabajador = request.form['selectNuevoDepartamento']
    usuarioTrabajador = request.form['txtUsuario']
    nuevoUsarioTrabajador = request.form['txtNuevoUsuario']
    emailTrabajador = request.form['txtEmail']
    nuevoEmailTrabajador = request.form['txtNuevoEmail']
    passTrabajador = request.form['txtPass']
    nuevoPassTrabajador = request.form['txtNuevoPass']
    nivelTrabajador = request.form['selectNivel']
    nuevoNivelTrabajador = request.form['selectNuevoNivel']

    datosActuales = [nombreTrabajador, dptoTrabajador, usuarioTrabajador, emailTrabajador, passTrabajador, nivelTrabajador ]
    datosNuevos = [nuevoNombreTrabajador, nuevoDptoTrabajador, nuevoUsarioTrabajador, nuevoEmailTrabajador, nuevoPassTrabajador, nuevoNivelTrabajador]

    if datosActuales == datosNuevos:
        flash(f"No ha habido cambios en el registro del trabajador {nuevoNombreTrabajador}", "trabajador-sin-cambios")
        return redirect('/admin/trabajadores')
    else:
        if emailTrabajador == nuevoEmailTrabajador and usuarioTrabajador == nuevoUsarioTrabajador:
            sqlTrabajador = "UPDATE trabajadores SET nombre=%s, departamento=%s WHERE id=%s;"
            datosTrabajador = (nuevoNombreTrabajador, nuevoDptoTrabajador, idTrabajador)
            conexion = mysql.connect()
            cursor = conexion.cursor()
            # Se ejecuta el sql y los datos "values".
            cursor.execute(sqlTrabajador, datosTrabajador)
            conexion.commit()
            conexion = mysql.connect()
            cursor = conexion.cursor()
            sqlCuentaTrabajador = "UPDATE cuentas SET username=%s, email=%s, password=%s, level=%s WHERE id=%s;"
            datosCuentaTrabajador = (nuevoUsarioTrabajador, nuevoEmailTrabajador, generate_password_hash(nuevoPassTrabajador), nuevoNivelTrabajador, idCT)
            cursor.execute(sqlCuentaTrabajador, datosCuentaTrabajador)
            conexion.commit()
            flash(f"Trabajador {nuevoNombreTrabajador} Actualizado", "trabajador-actualizado")
        elif emailTrabajador != nuevoEmailTrabajador and usuarioTrabajador == nuevoUsarioTrabajador:
            conexion = mysql.connect()
            cursor = conexion.cursor()
            cursor.execute("SELECT email FROM `cuentas` WHERE email=%s", nuevoEmailTrabajador)
            email = cursor.fetchone()
            if email is None:
                sqlTrabajador = "UPDATE trabajadores SET nombre=%s, departamento=%s WHERE id=%s;"
                datosTrabajador = (nuevoNombreTrabajador, nuevoDptoTrabajador, idTrabajador)
                conexion = mysql.connect()
                cursor = conexion.cursor()
                # Se ejecuta el sql y los datos "values".
                cursor.execute(sqlTrabajador, datosTrabajador)
                conexion.commit()
                conexion = mysql.connect()
                cursor = conexion.cursor()
                if passTrabajador == nuevoPassTrabajador:
                    sqlCuentaTrabajador = "UPDATE cuentas SET email=%s, level=%s WHERE id=%s;"
                    datosCuentaTrabajador = (nuevoEmailTrabajador, nuevoNivelTrabajador, idCT)
                    cursor.execute(sqlCuentaTrabajador, datosCuentaTrabajador)
                    conexion.commit()
                    flash(f"Trabajador {nuevoNombreTrabajador} Actualizado", "trabajador-actualizado")
                else:
                    sqlCuentaTrabajador = "UPDATE cuentas SET email=%s, password=%s, level=%s WHERE id=%s;"
                    datosCuentaTrabajador = (nuevoEmailTrabajador, generate_password_hash(nuevoPassTrabajador),
                    nuevoNivelTrabajador, idCT)
                    cursor.execute(sqlCuentaTrabajador, datosCuentaTrabajador)
                    conexion.commit()
                    flash(f"Trabajador {nuevoNombreTrabajador} Actualizado", "trabajador-actualizado")
            elif email is not None:
                flash(f"El email {nuevoEmailTrabajador} ya existe", "email-existe")
                return redirect(f'/admin/trabajadores/')

        elif emailTrabajador == nuevoEmailTrabajador and usuarioTrabajador != nuevoUsarioTrabajador:
            conexion = mysql.connect()
            cursor = conexion.cursor()
            cursor.execute("SELECT username FROM `cuentas` WHERE username=%s", (nuevoUsarioTrabajador))
            usuario = cursor.fetchone()
            if usuario is None:
                sqlTrabajador = "UPDATE trabajadores SET nombre=%s, departamento=%s WHERE id=%s;"
                datosTrabajador = (nuevoNombreTrabajador, nuevoDptoTrabajador, idTrabajador)
                conexion = mysql.connect()
                cursor = conexion.cursor()
                # Se ejecuta el sql y los datos "values".
                cursor.execute(sqlTrabajador, datosTrabajador)
                conexion.commit()
                conexion = mysql.connect()
                cursor = conexion.cursor()
                if passTrabajador == nuevoPassTrabajador:
                    sqlCuentaTrabajador = "UPDATE cuentas SET username=%s, level=%s WHERE id=%s;"
                    datosCuentaTrabajador = (nuevoUsarioTrabajador, nuevoNivelTrabajador, idCT)
                    cursor.execute(sqlCuentaTrabajador, datosCuentaTrabajador)
                    conexion.commit()
                    flash(f"Trabajador {nuevoNombreTrabajador} Actualizado", "trabajador-actualizado")
                else:
                    sqlCuentaTrabajador = "UPDATE cuentas SET username=%s, password=%s, level=%s WHERE id=%s;"
                    datosCuentaTrabajador = (nuevoUsarioTrabajador, generate_password_hash(nuevoPassTrabajador),
                                             nuevoNivelTrabajador, idCT)
                    cursor.execute(sqlCuentaTrabajador, datosCuentaTrabajador)
                    conexion.commit()
                    flash(f"Trabajador {nuevoNombreTrabajador} Actualizado", "trabajador-actualizado")
            elif usuario is not None:
                flash(f"El usuario {nuevoUsarioTrabajador} ya existe", "usuario-existe")
                return redirect(f'/admin/trabajadores/')

        elif emailTrabajador != nuevoEmailTrabajador and usuarioTrabajador != nuevoUsarioTrabajador:
            conexion = mysql.connect()
            cursor = conexion.cursor()
            cursor.execute("SELECT username FROM `cuentas` WHERE username=%s", (nuevoUsarioTrabajador))
            usuario = cursor.fetchone()
            cursor.execute("SELECT email FROM `cuentas` WHERE email=%s", (nuevoEmailTrabajador))
            email = cursor.fetchone()
            if email is None and usuario is None:
                sqlTrabajador = "UPDATE trabajadores SET nombre=%s, departamento=%s WHERE id=%s;"
                datosTrabajador = (nuevoNombreTrabajador, nuevoDptoTrabajador, idTrabajador)
                conexion = mysql.connect()
                cursor = conexion.cursor()
                # Se ejecuta el sql y los datos "values".
                cursor.execute(sqlTrabajador, datosTrabajador)
                conexion.commit()
                conexion = mysql.connect()
                cursor = conexion.cursor()
                if passTrabajador == nuevoPassTrabajador:
                    sqlCuentaTrabajador = "UPDATE cuentas SET username=%s, email=%s, level=%s WHERE id=%s;"
                    datosCuentaTrabajador = (nuevoUsarioTrabajador, nuevoEmailTrabajador, nuevoNivelTrabajador, idCT)
                    cursor.execute(sqlCuentaTrabajador, datosCuentaTrabajador)
                    conexion.commit()
                    flash(f"Trabajador {nuevoNombreTrabajador} Actualizado", "trabajador-actualizado")
                else:
                    sqlCuentaTrabajador = "UPDATE cuentas SET username=%s, email=%s, password=%s, level=%s WHERE id=%s;"
                    datosCuentaTrabajador = (
                    nuevoUsarioTrabajador, nuevoEmailTrabajador, generate_password_hash(nuevoPassTrabajador),
                    nuevoNivelTrabajador, idCT)
                    cursor.execute(sqlCuentaTrabajador, datosCuentaTrabajador)
                    conexion.commit()
                    flash(f"Trabajador {nuevoNombreTrabajador} Actualizado", "trabajador-actualizado")
            elif email is not None and usuario is not None:
                flash(f"El email {nuevoEmailTrabajador} y el usuario {nuevoUsarioTrabajador} ya existen","email-usuario-existe")
                return redirect(f'/admin/trabajadores/')
            elif email is not None:
                flash(f"El email {nuevoEmailTrabajador} ya existe", "email-existe")
                return redirect(f'/admin/trabajadores/')
            elif usuario is not None:
                flash(f"El usuario {nuevoUsarioTrabajador} ya existe", "usuario-existe")
                return redirect(f'/admin/trabajadores/')
    return redirect('/admin/trabajadores')

#Ordenar por nombre descendente
@app.route('/admin/trabajadores/z-a')
def admin_trabajadores_z_a():
    if session.get('logeado') == None:
        return redirect('/')
    elif session.get('logeado') == True and session.get('level') != "Admin":
        return redirect('/')
    else:
        usuario = session.get('username')

        conexion = mysql.connect()
        cursor = conexion.cursor()

        cursor.execute("SELECT id FROM `cuentas` WHERE cuentas.username=%s", usuario)
        idCuentaUsuarioLogeado = cursor.fetchone()
        conexion.commit()

        cursor.execute("SELECT id FROM `trabajadores` WHERE idCT=%s", idCuentaUsuarioLogeado)
        idUsuarioLogeado = cursor.fetchone()
        conexion.commit()

        cursor.execute("SELECT * FROM `trabajadores` INNER JOIN `cuentas` ON trabajadores.idCT=cuentas.id WHERE cuentas.username!='admin' ORDER BY trabajadores.nombre DESC")
        trabajadores = cursor.fetchall()
        conexion.commit()

        return render_template('admin/trabajadores.html', trabajadores=trabajadores,  idUsuarioLogeado=idUsuarioLogeado)

#Ordenar por email
@app.route('/admin/trabajadores/email')
def admin_trabajadores_email():
    if session.get('logeado') == None:
        return redirect('/')
    elif session.get('logeado') == True and session.get('level') != "Admin":
        return redirect('/')
    else:
        usuario = session.get('username')

        conexion = mysql.connect()
        cursor = conexion.cursor()

        cursor.execute("SELECT id FROM `cuentas` WHERE cuentas.username=%s", usuario)
        idCuentaUsuarioLogeado = cursor.fetchone()
        conexion.commit()

        cursor.execute("SELECT id FROM `trabajadores` WHERE idCT=%s", idCuentaUsuarioLogeado)
        idUsuarioLogeado = cursor.fetchone()
        conexion.commit()

        cursor.execute("SELECT * FROM `trabajadores` INNER JOIN `cuentas` ON trabajadores.idCT=cuentas.id WHERE cuentas.username!='admin' ORDER BY cuentas.email")
        trabajadores = cursor.fetchall()
        conexion.commit()

        return render_template('admin/trabajadores.html', trabajadores=trabajadores,  idUsuarioLogeado=idUsuarioLogeado)

#Ordenar por departamento
@app.route('/admin/trabajadores/dpto')
def admin_trabajadores_dpto():
    if session.get('logeado') == None:
        return redirect('/')
    elif session.get('logeado') == True and session.get('level') != "Admin":
        return redirect('/')
    else:
        usuario = session.get('username')

        conexion = mysql.connect()
        cursor = conexion.cursor()

        cursor.execute("SELECT id FROM `cuentas` WHERE cuentas.username=%s", usuario)
        idCuentaUsuarioLogeado = cursor.fetchone()
        conexion.commit()

        cursor.execute("SELECT id FROM `trabajadores` WHERE idCT=%s", idCuentaUsuarioLogeado)
        idUsuarioLogeado = cursor.fetchone()
        conexion.commit()

        cursor.execute("SELECT * FROM `trabajadores` INNER JOIN `cuentas` ON trabajadores.idCT=cuentas.id WHERE cuentas.username!='admin' ORDER BY trabajadores.departamento")
        trabajadores = cursor.fetchall()
        conexion.commit()

        return render_template('admin/trabajadores.html', trabajadores=trabajadores,  idUsuarioLogeado=idUsuarioLogeado)


#Administración clientes*******************************************************************************************
@app.route('/admin/clientes/')
def admin_clientes():
    if session.get('logeado') == None:
        return redirect('/')
    elif session.get('logeado') == True and session.get('level') != "Admin":
        return redirect('/')
    else:
        usuario = session.get('username')

        conexion = mysql.connect()
        cursor = conexion.cursor()

        cursor.execute("SELECT id FROM `cuentas` WHERE cuentas.username=%s", (usuario))
        idCuentaUsuarioLogeado = cursor.fetchone()
        conexion.commit()

        cursor.execute("SELECT id FROM `trabajadores` WHERE idCT=%s", idCuentaUsuarioLogeado)
        idUsuarioLogeado = cursor.fetchone()
        conexion.commit()

        cursor.execute("SELECT * FROM `cuentas` WHERE cuentas.id=%s", idCuentaUsuarioLogeado)
        datosCuenta = cursor.fetchone()
        conexion.commit()

        cursor.execute("SELECT * FROM `trabajadores` WHERE trabajadores.id=%s", idUsuarioLogeado)
        datosTrabajador = cursor.fetchone()
        conexion.commit()

        cursor.execute("SELECT * FROM `clientes` INNER JOIN `cuentas` ON clientes.idCC=cuentas.id ORDER BY clientes.nombreEmpresa ASC")
        clientes=cursor.fetchall()
        conexion.commit()
        return render_template('admin/clientes.html', clientes=clientes,  idUsuarioLogeado=idUsuarioLogeado, datosTrabajador=datosTrabajador, datosCuenta=datosCuenta)


@app.route('/admin/clientes/z-a')
def admin_clientes_a_z():
    if session.get('logeado') == None:
        return redirect('/')
    elif session.get('logeado') == True and session.get('level') != "Admin":
        return redirect('/')
    else:
        usuario = session.get('username')

        conexion = mysql.connect()
        cursor = conexion.cursor()

        cursor.execute("SELECT id FROM `cuentas` WHERE cuentas.username=%s", (usuario))
        idCuentaUsuarioLogeado = cursor.fetchone()
        conexion.commit()

        cursor.execute("SELECT id FROM `trabajadores` WHERE idCT=%s", idCuentaUsuarioLogeado)
        idUsuarioLogeado = cursor.fetchone()
        conexion.commit()

        cursor.execute("SELECT * FROM `cuentas` WHERE cuentas.id=%s", idCuentaUsuarioLogeado)
        datosCuenta = cursor.fetchone()
        conexion.commit()

        cursor.execute("SELECT * FROM `trabajadores` WHERE trabajadores.id=%s", idUsuarioLogeado)
        datosTrabajador = cursor.fetchone()
        conexion.commit()

        cursor.execute(
            "SELECT * FROM `clientes` INNER JOIN `cuentas` ON clientes.idCC=cuentas.id ORDER BY clientes.nombreEmpresa DESC")
        clientes = cursor.fetchall()
        conexion.commit()
        return render_template('admin/clientes.html', clientes=clientes, idUsuarioLogeado=idUsuarioLogeado,
                           datosTrabajador=datosTrabajador, datosCuenta=datosCuenta)

@app.route('/admin/clientes/email')
def admin_clientes_email():
    if session.get('logeado') == None:
        return redirect('/')
    elif session.get('logeado') == True and session.get('level') != "Admin":
        return redirect('/')
    else:
        usuario = session.get('username')

        conexion = mysql.connect()
        cursor = conexion.cursor()

        cursor.execute("SELECT id FROM `cuentas` WHERE cuentas.username=%s", (usuario))
        idCuentaUsuarioLogeado = cursor.fetchone()
        conexion.commit()

        cursor.execute("SELECT id FROM `trabajadores` WHERE idCT=%s", idCuentaUsuarioLogeado)
        idUsuarioLogeado = cursor.fetchone()
        conexion.commit()

        cursor.execute("SELECT * FROM `cuentas` WHERE cuentas.id=%s", idCuentaUsuarioLogeado)
        datosCuenta = cursor.fetchone()
        conexion.commit()

        cursor.execute("SELECT * FROM `trabajadores` WHERE trabajadores.id=%s", idUsuarioLogeado)
        datosTrabajador = cursor.fetchone()
        conexion.commit()

        cursor.execute(
            "SELECT * FROM `clientes` INNER JOIN `cuentas` ON clientes.idCC=cuentas.id ORDER BY cuentas.email")
        clientes = cursor.fetchall()
        conexion.commit()
        return render_template('admin/clientes.html', clientes=clientes, idUsuarioLogeado=idUsuarioLogeado,
                           datosTrabajador=datosTrabajador, datosCuenta=datosCuenta)

#Guardar Cliente
@app.route('/admin/clientes/guardar', methods=['POST', 'GET'])
def admin_clientes_guardar():
    if request.method == "POST":
        nombreCliente = request.form['txtGuardarNombre']
        usuarioCliente = request.form['txtGuardarUsuario']
        emailCliente = request.form['txtGuardarEmail']
        passCliente = request.form['txtGuardarPass']
        nivelCliente = "Cliente"

        #Chequear si el email o el usuario existe
        conexion = mysql.connect()
        cursor = conexion.cursor()
        cursor.execute("SELECT email FROM `cuentas` WHERE email=%s", emailCliente)
        email = cursor.fetchone()
        cursor.execute("SELECT username FROM `cuentas` WHERE username=%s", usuarioCliente)
        username = cursor.fetchone()
        if email is None and username is None:
            cursor.execute("INSERT INTO `cuentas` VALUES (NULL,%s,%s,%s,%s);", (usuarioCliente, emailCliente, generate_password_hash(passCliente), nivelCliente))
            conexion.commit()
            cursor.execute("SELECT id FROM `cuentas` WHERE email=%s", emailCliente)
            idCuentaCliente = cursor.fetchone()
            cursor.execute("INSERT INTO `clientes` VALUES (NULL,%s,%s);", (idCuentaCliente, nombreCliente))
            conexion.commit()
            flash(f"Cliente {nombreCliente} registrado", "cliente-guardado")
        elif email is not None and username is not None:
            flash(f"El email {emailCliente} y el usuario {usuarioCliente} ya existen", "email-usuario-existe")
        elif email is not None:
            flash(f"El email {emailCliente} ya existe", "email-existe")
        elif username is not None:
            flash(f"El usuario {usuarioCliente} ya existe", "usuario-existe")

    return redirect('/admin/clientes')

#Borrar cliente
@app.route('/admin/clientes/borrar/<int:id>')
def admin_clientes_borrar(id):
    conexion = mysql.connect()
    cursor = conexion.cursor()
    cursor.execute("SELECT nombreEmpresa FROM `clientes` WHERE clientes.id=%s", (id))
    nombreCliente = cursor.fetchone()
    cursor.execute("SELECT idCliente FROM `tareas` WHERE tareas.idCliente=%s", (id))
    idClienteTarea = cursor.fetchone()
    if idClienteTarea is None:
        flash(f"El cliente {nombreCliente[0]} ha sido borrado", "cliente-borrado")
        cursor.execute("SELECT idCC FROM `clientes` WHERE id=%s", (id))
        idCuentaCliente = cursor.fetchone()
        cursor.execute("DELETE FROM `clientes` WHERE id=%s", (id))
        conexion.commit()
        cursor.execute("DELETE FROM `cuentas` WHERE id=%s", (idCuentaCliente))
        conexion.commit()
    else:
        flash(f"El cliente {nombreCliente[0]} está asignado a una o más tareas y no se puede borrar", "cliente-asignado")
    return redirect('/admin/clientes')


#Editar clientes
@app.route('/admin/clientes/actualizar/', methods=['POST'])
def admin_actualizar_clientes():
    idCliente = int(request.form['txtId'])
    idCC = int(request.form['txtIdCC'])
    nombreCliente = request.form['txtNombre']
    nuevoNombreCliente = request.form['txtNuevoNombre']
    usuarioCliente = request.form['txtUsuario']
    nuevoUsuarioCliente = request.form['txtNuevoUsuario']
    emailCliente = request.form['txtEmail']
    nuevoEmailCliente = request.form['txtNuevoEmail']
    passCliente = request.form['txtPass']
    nuevoPassCliente = request.form['txtNuevoPass']

    datosActuales = [nombreCliente, usuarioCliente, emailCliente, passCliente]
    datosNuevos = [nuevoNombreCliente, nuevoUsuarioCliente, nuevoEmailCliente, nuevoPassCliente]

    if datosActuales == datosNuevos:
        flash(f"No ha habido cambios en el registro del cliente {nuevoNombreCliente}", "cliente-sin-cambios")
        return redirect('/admin/clientes')
    else:
        if emailCliente == nuevoEmailCliente and usuarioCliente == nuevoUsuarioCliente:
            sqlCliente= "UPDATE clientes SET nombreEmpresa=%s WHERE id=%s;"
            datosCliente = (nuevoNombreCliente, idCliente)
            conexion = mysql.connect()
            cursor = conexion.cursor()
            # Se ejecuta el sql y los datos "values".
            cursor.execute(sqlCliente, datosCliente)
            conexion.commit()
            conexion = mysql.connect()
            cursor = conexion.cursor()
            sqlCuentaCliente = "UPDATE cuentas SET username=%s, email=%s, password=%s WHERE id=%s;"
            datosCuentaCliente = (nuevoUsuarioCliente, nuevoEmailCliente, generate_password_hash(nuevoPassCliente), idCC)
            cursor.execute(sqlCuentaCliente, datosCuentaCliente)
            conexion.commit()
            flash(f"Cliente {nuevoNombreCliente} Actualizado", "cliente-actualizado")
        elif emailCliente != nuevoEmailCliente and usuarioCliente == nuevoUsuarioCliente:
            conexion = mysql.connect()
            cursor = conexion.cursor()
            cursor.execute("SELECT email FROM `cuentas` WHERE email=%s", nuevoEmailCliente)
            email = cursor.fetchone()
            if email is None:
                sqlCliente = "UPDATE clientes SET nombreEmpresa=%s WHERE id=%s;"
                datosCliente = (nuevoNombreCliente, idCliente)
                conexion = mysql.connect()
                cursor = conexion.cursor()
                # Se ejecuta el sql y los datos "values".
                cursor.execute(sqlCliente, datosCliente)
                conexion.commit()
                conexion = mysql.connect()
                cursor = conexion.cursor()
                sqlCuentaCliente = "UPDATE cuentas SET username=%s, email=%s, password=%s WHERE id=%s;"
                datosCuentaCliente = (
                nuevoUsuarioCliente, nuevoEmailCliente, generate_password_hash(nuevoPassCliente), idCC)
                cursor.execute(sqlCuentaCliente, datosCuentaCliente)
                conexion.commit()
                flash(f"Cliente {nuevoNombreCliente} Actualizado", "cliente-actualizado")
            elif email is not None:
                flash(f"El email {nuevoEmailCliente} ya existe", "email-existe")
                return redirect(f'/admin/clientes/')

        elif emailCliente == nuevoEmailCliente and usuarioCliente != nuevoUsuarioCliente:
            conexion = mysql.connect()
            cursor = conexion.cursor()
            cursor.execute("SELECT username FROM `cuentas` WHERE username=%s", nuevoUsuarioCliente)
            usuario = cursor.fetchone()
            if usuario is None:
                sqlCliente = "UPDATE clientes SET nombreEmpresa=%s WHERE id=%s;"
                datosCliente = (nuevoNombreCliente, idCliente)
                conexion = mysql.connect()
                cursor = conexion.cursor()
                # Se ejecuta el sql y los datos "values".
                cursor.execute(sqlCliente, datosCliente)
                conexion.commit()
                conexion = mysql.connect()
                cursor = conexion.cursor()
                sqlCuentaCliente = "UPDATE cuentas SET username=%s, email=%s, password=%s WHERE id=%s;"
                datosCuentaCliente = (nuevoUsuarioCliente, nuevoEmailCliente, generate_password_hash(nuevoPassCliente), idCC)
                cursor.execute(sqlCuentaCliente, datosCuentaCliente)
                conexion.commit()
                flash(f"Cliente {nuevoNombreCliente} Actualizado", "cliente-actualizado")
            elif usuario is not None:
                flash(f"El usuario {nuevoUsuarioCliente} ya existe", "usuario-existe")
                return redirect(f'/admin/clientes/')

        elif emailCliente != nuevoEmailCliente and usuarioCliente != nuevoUsuarioCliente:
            conexion = mysql.connect()
            cursor = conexion.cursor()
            cursor.execute("SELECT username FROM `cuentas` WHERE username=%s", nuevoUsuarioCliente)
            usuario = cursor.fetchone()
            cursor.execute("SELECT email FROM `cuentas` WHERE email=%s", nuevoEmailCliente)
            email = cursor.fetchone()
            if email is None and usuario is None:
                sqlCliente = "UPDATE clientes SET nombreEmpresa=%s WHERE id=%s;"
                datosCliente = (nuevoNombreCliente, idCliente)
                conexion = mysql.connect()
                cursor = conexion.cursor()
                # Se ejecuta el sql y los datos "values".
                cursor.execute(sqlCliente, datosCliente)
                conexion.commit()
                conexion = mysql.connect()
                cursor = conexion.cursor()
                sqlCuentaCliente = "UPDATE cuentas SET username=%s, email=%s, password=%s WHERE id=%s;"
                datosCuentaCliente = (nuevoUsuarioCliente, nuevoEmailCliente, generate_password_hash(nuevoPassCliente), idCC)
                cursor.execute(sqlCuentaCliente, datosCuentaCliente)
                conexion.commit()
                flash(f"Cliente {nuevoNombreCliente} Actualizado", "cliente-actualizado")
            elif email is not None and usuario is not None:
                flash(f"El email {nuevoEmailCliente} y el usuario {nuevoUsuarioCliente} ya existen","email-usuario-existe")
                return redirect(f'/admin/clientes/')
            elif email is not None:
                flash(f"El email {nuevoEmailCliente} ya existe", "email-existe")
                return redirect(f'/admin/clientes/')
            elif usuario is not None:
                flash(f"El usuario {nuevoUsuarioCliente} ya existe", "usuario-existe")
                return redirect(f'/admin/clientes/')
    return redirect('/admin/clientes')

#Recompensas
@app.route('/admin/recompensas/')
def admin_recompensas():
    if session.get('logeado') == None:
        return redirect('/')
    elif session.get('logeado') == True and session.get('level') != "Admin":
        return redirect('/')
    else:
        usuario = session.get('username')

        conexion = mysql.connect()
        cursor = conexion.cursor()
        cursor.execute("SELECT id FROM `cuentas` WHERE cuentas.username=%s", (usuario))
        idCuentaUsuarioLogeado = cursor.fetchone()
        conexion.commit()

        cursor.execute("SELECT id FROM `trabajadores` WHERE idCT=%s", idCuentaUsuarioLogeado)
        idUsuarioLogeado = cursor.fetchone()
        conexion.commit()

        cursor.execute("SELECT * FROM `cuentas` WHERE cuentas.id=%s", idCuentaUsuarioLogeado)
        datosCuenta = cursor.fetchone()
        conexion.commit()

        cursor.execute("SELECT * FROM `trabajadores` WHERE trabajadores.id=%s", idUsuarioLogeado)
        datosTrabajador = cursor.fetchone()
        conexion.commit()

        sqlRecompensa = "SELECT nombre, departamento, count(estado) FROM tareas INNER JOIN trabajadores ON tareas.idTrabajador=trabajadores.id WHERE estado=%s GROUP BY trabajadores.nombre"
        datosRecompensa = "Finalizada"
        cursor.execute(sqlRecompensa, datosRecompensa)
        recompensas = cursor.fetchall()
        conexion.commit()
        return render_template('admin/recompensas.html', idUsuarioLogeado=idUsuarioLogeado, recompensas=recompensas,
                           datosTrabajador=datosTrabajador, datosCuenta=datosCuenta)

#ordenar recompensas Z-A
@app.route('/admin/recompensas/z-a')
def admin_recompensas_z_a():
    if session.get('logeado') == None:
        return redirect('/')
    elif session.get('logeado') == True and session.get('level') != "Admin":
        return redirect('/')
    else:
        usuario = session.get('username')

        conexion = mysql.connect()
        cursor = conexion.cursor()
        cursor.execute("SELECT id FROM `cuentas` WHERE cuentas.username=%s", (usuario))
        idCuentaUsuarioLogeado = cursor.fetchone()
        conexion.commit()

        cursor.execute("SELECT id FROM `trabajadores` WHERE idCT=%s", idCuentaUsuarioLogeado)
        idUsuarioLogeado = cursor.fetchone()
        conexion.commit()

        cursor.execute("SELECT * FROM `cuentas` WHERE cuentas.id=%s", idCuentaUsuarioLogeado)
        datosCuenta = cursor.fetchone()
        conexion.commit()

        cursor.execute("SELECT * FROM `trabajadores` WHERE trabajadores.id=%s", idUsuarioLogeado)
        datosTrabajador = cursor.fetchone()
        conexion.commit()

        sqlRecompensa = "SELECT nombre, departamento, count(estado) FROM tareas INNER JOIN trabajadores ON tareas.idTrabajador=trabajadores.id WHERE estado=%s GROUP BY trabajadores.nombre ORDER BY trabajadores.nombre DESC"
        datosRecompensa = "Finalizada"
        cursor.execute(sqlRecompensa, datosRecompensa)
        recompensas = cursor.fetchall()
        conexion.commit()
        return render_template('admin/recompensas.html', idUsuarioLogeado=idUsuarioLogeado, recompensas=recompensas,
                               datosTrabajador=datosTrabajador, datosCuenta=datosCuenta)


#ordenar por email
@app.route('/admin/recompensas/departamento')
def admin_recompensas_departamento():
    usuario = session.get('username')

    conexion = mysql.connect()
    cursor = conexion.cursor()

    cursor.execute("SELECT id FROM `cuentas` WHERE cuentas.username=%s", (usuario))
    idCuentaUsuarioLogeado = cursor.fetchone()
    conexion.commit()

    cursor.execute("SELECT id FROM `trabajadores` WHERE idCT=%s", idCuentaUsuarioLogeado)
    idUsuarioLogeado = cursor.fetchone()
    conexion.commit()

    cursor.execute("SELECT * FROM `cuentas` WHERE cuentas.id=%s", idCuentaUsuarioLogeado)
    datosCuenta = cursor.fetchone()
    conexion.commit()

    cursor.execute("SELECT * FROM `trabajadores` WHERE trabajadores.id=%s", idUsuarioLogeado)
    datosTrabajador = cursor.fetchone()
    conexion.commit()

    sqlRecompensa = "SELECT nombre, departamento, count(estado) FROM tareas INNER JOIN trabajadores ON tareas.idTrabajador=trabajadores.id WHERE estado=%s GROUP BY trabajadores.nombre ORDER BY trabajadores.departamento"
    datosRecompensa = "Finalizada"
    cursor.execute(sqlRecompensa, datosRecompensa)
    recompensas = cursor.fetchall()
    conexion.commit()
    return render_template('admin/recompensas.html', idUsuarioLogeado=idUsuarioLogeado, recompensas=recompensas,
                           datosTrabajador=datosTrabajador, datosCuenta=datosCuenta)

#Acceso Trabajador
@app.route('/trabajador/')
def trabajador():
    if session.get('logeado') == None:
        return redirect('/')
    elif session.get('logeado') == True and session.get('level') != "Trabajador":
        return redirect('/')
    else:
        fechaActual = datetime.today()
        conexion = mysql.connect()
        cursor = conexion.cursor()
        cursor.execute("SELECT id, fechaFin, estado FROM `tareas` ")
        fechasFin = cursor.fetchall()

        for fechaFin in fechasFin:
            diferenciaFecha = fechaFin[1] - fechaActual
            diferenciaFecha = int(diferenciaFecha.days)
            if diferenciaFecha >= 6:
                sql = "UPDATE tareas SET prioridad=%s WHERE id=%s;"
                datos = ("Baja", fechaFin[0])
                conexion = mysql.connect()
                cursor = conexion.cursor()
                # Se ejecuta el sql y los datos "values".
                cursor.execute(sql, datos)
                conexion.commit()
            elif diferenciaFecha == 5 or diferenciaFecha == 4:
                sql = "UPDATE tareas SET prioridad=%s WHERE id=%s;"
                datos = ("Media", fechaFin[0])
                conexion = mysql.connect()
                cursor = conexion.cursor()
                # Se ejecuta el sql y los datos "values".
                cursor.execute(sql, datos)
                conexion.commit()
            elif diferenciaFecha < 4:
                sql = "UPDATE tareas SET prioridad=%s WHERE id=%s;"
                datos = ("Alta", fechaFin[0])
                conexion = mysql.connect()
                cursor = conexion.cursor()
                # Se ejecuta el sql y los datos "values".
                cursor.execute(sql, datos)
                conexion.commit()
            if diferenciaFecha <= 0:
                sql = "UPDATE tareas SET prioridad=%s WHERE id=%s;"
                datos = ("Agotada", fechaFin[0])
                conexion = mysql.connect()
                cursor = conexion.cursor()
                # Se ejecuta el sql y los datos "values".
                cursor.execute(sql, datos)
                conexion.commit()
            if fechaFin[2] == "Finalizada":
                    sql = "UPDATE tareas SET prioridad=%s WHERE id=%s;"
                    datos = ("Ninguna", fechaFin[0])
                    cursor.execute(sql, datos)
                    conexion.commit()

        usuario = session.get('username')

        conexion = mysql.connect()
        cursor = conexion.cursor()

        cursor.execute("SELECT id FROM `cuentas` WHERE cuentas.username=%s", usuario)
        idCuentaUsuarioLogeado = cursor.fetchone()
        conexion.commit()

        cursor.execute("SELECT id FROM `trabajadores` WHERE idCT=%s", idCuentaUsuarioLogeado)
        idUsuarioLogeado = cursor.fetchone()
        conexion.commit()

        cursor.execute("SELECT * FROM `tareas` INNER JOIN `trabajadores` ON tareas.idTrabajador=trabajadores.id INNER JOIN `clientes` ON tareas.idCliente=clientes.id WHERE tareas.idTrabajador=%s ORDER BY tareas.Fecha DESC;", idUsuarioLogeado)
        tareas=cursor.fetchall()
        conexion.commit()

        sqlContadorTareasAlta = "SELECT COUNT(prioridad) FROM tareas WHERE prioridad=%s and tareas.idTrabajador=%s"
        datosContadorTareasAlta = "Alta", idUsuarioLogeado
        cursor.execute(sqlContadorTareasAlta, datosContadorTareasAlta)
        tareasAlta = cursor.fetchone()
        conexion.commit()

        sqlContadorTareasMedia = "SELECT COUNT(prioridad) FROM tareas WHERE prioridad=%s and tareas.idTrabajador=%s"
        datosContadorTareasMedia = "Media", idUsuarioLogeado
        cursor.execute(sqlContadorTareasMedia, datosContadorTareasMedia)
        tareasMedia = cursor.fetchone()
        conexion.commit()

        sqlContadorTareasBaja ="SELECT COUNT(prioridad) FROM tareas WHERE prioridad=%s and tareas.idTrabajador=%s"
        datosContadorTareasBaja = "Baja", idUsuarioLogeado
        cursor.execute(sqlContadorTareasBaja, datosContadorTareasBaja)
        tareasBaja = cursor.fetchone()
        conexion.commit()

        sqlContadorTareas = "SELECT COUNT(estado) FROM tareas WHERE estado=%s and tareas.idTrabajador=%s"
        datosContadorTareas = "Finalizada", idUsuarioLogeado
        cursor.execute(sqlContadorTareas, datosContadorTareas)
        tareasFinalizadas = cursor.fetchone()
        conexion.commit()

        return render_template('trabajador/index.html', tareas=tareas, idUsuarioLogeado=idUsuarioLogeado, tareasAlta=tareasAlta,
            tareasMedia=tareasMedia, tareasBaja=tareasBaja, tareasFinalizadas=tareasFinalizadas)


#Actualizar Tarea
@app.route('/trabajador/actualizar-tarea/', methods=['POST'])
def trabajador_actualizar_tarea():
    idTarea = int(request.form['txtId'])
    tituloTarea = request.form['txtTitulo']
    estadoTarea = request.form['selectEstado']
    nuevoEstadoTarea = request.form['selectNuevoEstado']

    if estadoTarea == nuevoEstadoTarea:
        flash(f"No ha habido cambios en la tarea {tituloTarea}", "tarea-sin-cambios")
        return redirect('/trabajador/')
    else:
        sql = "UPDATE tareas SET estado=%s WHERE id=%s;"
        datos = (nuevoEstadoTarea, idTarea)
        conexion = mysql.connect()
        cursor = conexion.cursor()
        # Se ejecuta el sql y los datos "values".
        cursor.execute(sql, datos)
        if nuevoEstadoTarea == "Finalizada":
            flash(f"Tarea {tituloTarea} finalizada. Si necesita abrir nuevamente la tarea contacta con un administrador", "abrir-tarea")
        else:
            flash(f"Tarea {tituloTarea} actualizada", "actualizada")
        conexion.commit()
    return redirect('/trabajador/')

@app.route('/trabajador/cliente/')
def trabajador_cliente():
    if session.get('logeado') == None:
        return redirect('/')
    elif session.get('logeado') == True and session.get('level') != "Trabajador":
        return redirect('/')
    else:
        fechaActual = datetime.today()
        conexion = mysql.connect()
        cursor = conexion.cursor()
        cursor.execute("SELECT id, fechaFin, estado FROM `tareas` ")
        fechasFin = cursor.fetchall()

        for fechaFin in fechasFin:
            diferenciaFecha = fechaFin[1] - fechaActual
            diferenciaFecha = int(diferenciaFecha.days)
            if diferenciaFecha >= 6:
                sql = "UPDATE tareas SET prioridad=%s WHERE id=%s;"
                datos = ("Baja", fechaFin[0])
                conexion = mysql.connect()
                cursor = conexion.cursor()
                # Se ejecuta el sql y los datos "values".
                cursor.execute(sql, datos)
                conexion.commit()
            elif diferenciaFecha == 5 or diferenciaFecha == 4:
                sql = "UPDATE tareas SET prioridad=%s WHERE id=%s;"
                datos = ("Media", fechaFin[0])
                conexion = mysql.connect()
                cursor = conexion.cursor()
                # Se ejecuta el sql y los datos "values".
                cursor.execute(sql, datos)
                conexion.commit()
            elif diferenciaFecha < 4:
                sql = "UPDATE tareas SET prioridad=%s WHERE id=%s;"
                datos = ("Alta", fechaFin[0])
                conexion = mysql.connect()
                cursor = conexion.cursor()
                # Se ejecuta el sql y los datos "values".
                cursor.execute(sql, datos)
                conexion.commit()
            if fechaFin[2] == "Finalizada":
                    sql = "UPDATE tareas SET prioridad=%s WHERE id=%s;"
                    datos = ("Ninguna", fechaFin[0])
                    cursor.execute(sql, datos)
                    conexion.commit()

        usuario = session.get('username')

        conexion = mysql.connect()
        cursor = conexion.cursor()

        cursor.execute("SELECT id FROM `cuentas` WHERE cuentas.username=%s", usuario)
        idCuentaUsuarioLogeado = cursor.fetchone()
        conexion.commit()

        cursor.execute("SELECT id FROM `trabajadores` WHERE idCT=%s", idCuentaUsuarioLogeado)
        idUsuarioLogeado = cursor.fetchone()
        conexion.commit()

        cursor.execute("SELECT * FROM `tareas` INNER JOIN `trabajadores` ON tareas.idTrabajador=trabajadores.id INNER JOIN `clientes` ON tareas.idCliente=clientes.id WHERE tareas.idTrabajador=%s ORDER BY clientes.nombreEmpresa;", idUsuarioLogeado)
        tareas=cursor.fetchall()
        conexion.commit()

        sqlContadorTareasAlta = "SELECT COUNT(prioridad) FROM tareas WHERE prioridad=%s and tareas.idTrabajador=%s"
        datosContadorTareasAlta = "Alta", idUsuarioLogeado
        cursor.execute(sqlContadorTareasAlta, datosContadorTareasAlta)
        tareasAlta = cursor.fetchone()
        conexion.commit()

        sqlContadorTareasMedia = "SELECT COUNT(prioridad) FROM tareas WHERE prioridad=%s and tareas.idTrabajador=%s"
        datosContadorTareasMedia = "Media", idUsuarioLogeado
        cursor.execute(sqlContadorTareasMedia, datosContadorTareasMedia)
        tareasMedia = cursor.fetchone()
        conexion.commit()

        sqlContadorTareasBaja ="SELECT COUNT(prioridad) FROM tareas WHERE prioridad=%s and tareas.idTrabajador=%s"
        datosContadorTareasBaja = "Baja", idUsuarioLogeado
        cursor.execute(sqlContadorTareasBaja, datosContadorTareasBaja)
        tareasBaja = cursor.fetchone()
        conexion.commit()

        sqlContadorTareas = "SELECT COUNT(estado) FROM tareas WHERE estado=%s and tareas.idTrabajador=%s"
        datosContadorTareas = "Finalizada", idUsuarioLogeado
        cursor.execute(sqlContadorTareas, datosContadorTareas)
        tareasFinalizadas = cursor.fetchone()
        conexion.commit()

        return render_template('trabajador/index.html', tareas=tareas, idUsuarioLogeado=idUsuarioLogeado, tareasAlta=tareasAlta,
            tareasMedia=tareasMedia, tareasBaja=tareasBaja, tareasFinalizadas=tareasFinalizadas)

@app.route('/trabajador/estado/')
def trabajador_estado():
    if session.get('logeado') == None:
        return redirect('/')
    elif session.get('logeado') == True and session.get('level') != "Trabajador":
        return redirect('/')
    else:
        fechaActual = datetime.today()
        conexion = mysql.connect()
        cursor = conexion.cursor()
        cursor.execute("SELECT id, fechaFin, estado FROM `tareas` ")
        fechasFin = cursor.fetchall()

        for fechaFin in fechasFin:
            diferenciaFecha = fechaFin[1] - fechaActual
            diferenciaFecha = int(diferenciaFecha.days)
            if diferenciaFecha >= 6:
                sql = "UPDATE tareas SET prioridad=%s WHERE id=%s;"
                datos = ("Baja", fechaFin[0])
                conexion = mysql.connect()
                cursor = conexion.cursor()
                # Se ejecuta el sql y los datos "values".
                cursor.execute(sql, datos)
                conexion.commit()
            elif diferenciaFecha == 5 or diferenciaFecha == 4:
                sql = "UPDATE tareas SET prioridad=%s WHERE id=%s;"
                datos = ("Media", fechaFin[0])
                conexion = mysql.connect()
                cursor = conexion.cursor()
                # Se ejecuta el sql y los datos "values".
                cursor.execute(sql, datos)
                conexion.commit()
            elif diferenciaFecha < 4:
                sql = "UPDATE tareas SET prioridad=%s WHERE id=%s;"
                datos = ("Alta", fechaFin[0])
                conexion = mysql.connect()
                cursor = conexion.cursor()
                # Se ejecuta el sql y los datos "values".
                cursor.execute(sql, datos)
                conexion.commit()
            if fechaFin[2] == "Finalizada":
                    sql = "UPDATE tareas SET prioridad=%s WHERE id=%s;"
                    datos = ("Ninguna", fechaFin[0])
                    cursor.execute(sql, datos)
                    conexion.commit()

        usuario = session.get('username')

        conexion = mysql.connect()
        cursor = conexion.cursor()

        cursor.execute("SELECT id FROM `cuentas` WHERE cuentas.username=%s", usuario)
        idCuentaUsuarioLogeado = cursor.fetchone()
        conexion.commit()

        cursor.execute("SELECT id FROM `trabajadores` WHERE idCT=%s", idCuentaUsuarioLogeado)
        idUsuarioLogeado = cursor.fetchone()
        conexion.commit()

        cursor.execute("SELECT * FROM `tareas` INNER JOIN `trabajadores` ON tareas.idTrabajador=trabajadores.id INNER JOIN`clientes` ON tareas.idCliente=clientes.id WHERE tareas.idTrabajador=%s ORDER BY case when estado = 'Por Empezar' then 1 when estado = 'En proceso' then 2 when estado = 'Finalizada' then 3 end asc;", idUsuarioLogeado)
        tareas=cursor.fetchall()
        conexion.commit()

        sqlContadorTareasAlta = "SELECT COUNT(prioridad) FROM tareas WHERE prioridad=%s and tareas.idTrabajador=%s"
        datosContadorTareasAlta = "Alta", idUsuarioLogeado
        cursor.execute(sqlContadorTareasAlta, datosContadorTareasAlta)
        tareasAlta = cursor.fetchone()
        conexion.commit()

        sqlContadorTareasMedia = "SELECT COUNT(prioridad) FROM tareas WHERE prioridad=%s and tareas.idTrabajador=%s"
        datosContadorTareasMedia = "Media", idUsuarioLogeado
        cursor.execute(sqlContadorTareasMedia, datosContadorTareasMedia)
        tareasMedia = cursor.fetchone()
        conexion.commit()

        sqlContadorTareasBaja ="SELECT COUNT(prioridad) FROM tareas WHERE prioridad=%s and tareas.idTrabajador=%s"
        datosContadorTareasBaja = "Baja", idUsuarioLogeado
        cursor.execute(sqlContadorTareasBaja, datosContadorTareasBaja)
        tareasBaja = cursor.fetchone()
        conexion.commit()

        sqlContadorTareas = "SELECT COUNT(estado) FROM tareas WHERE estado=%s and tareas.idTrabajador=%s"
        datosContadorTareas = "Finalizada", idUsuarioLogeado
        cursor.execute(sqlContadorTareas, datosContadorTareas)
        tareasFinalizadas = cursor.fetchone()
        conexion.commit()

        return render_template('trabajador/index.html', tareas=tareas, idUsuarioLogeado=idUsuarioLogeado, tareasAlta=tareasAlta,
            tareasMedia=tareasMedia, tareasBaja=tareasBaja, tareasFinalizadas=tareasFinalizadas)

@app.route('/trabajador/prioridad/')
def trabajador_prioridad():
    if session.get('logeado') == None:
        return redirect('/')
    elif session.get('logeado') == True and session.get('level') != "Trabajador":
        return redirect('/')
    else:
        fechaActual = datetime.today()
        conexion = mysql.connect()
        cursor = conexion.cursor()
        cursor.execute("SELECT id, fechaFin, estado FROM `tareas` ")
        fechasFin = cursor.fetchall()

        for fechaFin in fechasFin:
            diferenciaFecha = fechaFin[1] - fechaActual
            diferenciaFecha = int(diferenciaFecha.days)
            if diferenciaFecha >= 6:
                sql = "UPDATE tareas SET prioridad=%s WHERE id=%s;"
                datos = ("Baja", fechaFin[0])
                conexion = mysql.connect()
                cursor = conexion.cursor()
                # Se ejecuta el sql y los datos "values".
                cursor.execute(sql, datos)
                conexion.commit()
            elif diferenciaFecha == 5 or diferenciaFecha == 4:
                sql = "UPDATE tareas SET prioridad=%s WHERE id=%s;"
                datos = ("Media", fechaFin[0])
                conexion = mysql.connect()
                cursor = conexion.cursor()
                # Se ejecuta el sql y los datos "values".
                cursor.execute(sql, datos)
                conexion.commit()
            elif diferenciaFecha < 4:
                sql = "UPDATE tareas SET prioridad=%s WHERE id=%s;"
                datos = ("Alta", fechaFin[0])
                conexion = mysql.connect()
                cursor = conexion.cursor()
                # Se ejecuta el sql y los datos "values".
                cursor.execute(sql, datos)
                conexion.commit()
            if fechaFin[2] == "Finalizada":
                    sql = "UPDATE tareas SET prioridad=%s WHERE id=%s;"
                    datos = ("Ninguna", fechaFin[0])
                    cursor.execute(sql, datos)
                    conexion.commit()

        usuario = session.get('username')

        conexion = mysql.connect()
        cursor = conexion.cursor()

        cursor.execute("SELECT id FROM `cuentas` WHERE cuentas.username=%s", usuario)
        idCuentaUsuarioLogeado = cursor.fetchone()
        conexion.commit()

        cursor.execute("SELECT id FROM `trabajadores` WHERE idCT=%s", idCuentaUsuarioLogeado)
        idUsuarioLogeado = cursor.fetchone()
        conexion.commit()

        cursor.execute("SELECT * FROM `tareas` INNER JOIN `trabajadores` ON tareas.idTrabajador=trabajadores.id INNER JOIN`clientes` ON tareas.idCliente=clientes.id WHERE tareas.idTrabajador=%s ORDER BY case when prioridad = 'Alta' then 1 when prioridad = 'Media' then 2 when prioridad = 'Baja' then 3 when prioridad = 'Ninguna' then 4 end asc;", idUsuarioLogeado)
        tareas=cursor.fetchall()
        conexion.commit()

        sqlContadorTareasAlta = "SELECT COUNT(prioridad) FROM tareas WHERE prioridad=%s and tareas.idTrabajador=%s"
        datosContadorTareasAlta = "Alta", idUsuarioLogeado
        cursor.execute(sqlContadorTareasAlta, datosContadorTareasAlta)
        tareasAlta = cursor.fetchone()
        conexion.commit()

        sqlContadorTareasMedia = "SELECT COUNT(prioridad) FROM tareas WHERE prioridad=%s and tareas.idTrabajador=%s"
        datosContadorTareasMedia = "Media", idUsuarioLogeado
        cursor.execute(sqlContadorTareasMedia, datosContadorTareasMedia)
        tareasMedia = cursor.fetchone()
        conexion.commit()

        sqlContadorTareasBaja ="SELECT COUNT(prioridad) FROM tareas WHERE prioridad=%s and tareas.idTrabajador=%s"
        datosContadorTareasBaja = "Baja", idUsuarioLogeado
        cursor.execute(sqlContadorTareasBaja, datosContadorTareasBaja)
        tareasBaja = cursor.fetchone()
        conexion.commit()

        sqlContadorTareas = "SELECT COUNT(estado) FROM tareas WHERE estado=%s and tareas.idTrabajador=%s"
        datosContadorTareas = "Finalizada", idUsuarioLogeado
        cursor.execute(sqlContadorTareas, datosContadorTareas)
        tareasFinalizadas = cursor.fetchone()
        conexion.commit()

        return render_template('trabajador/index.html', tareas=tareas, idUsuarioLogeado=idUsuarioLogeado, tareasAlta=tareasAlta,
            tareasMedia=tareasMedia, tareasBaja=tareasBaja, tareasFinalizadas=tareasFinalizadas)

@app.route('/cliente/')
def cliente():
    if session.get('logeado') == None:
        return redirect('/')
    elif session.get('logeado') == True and session.get('level') != "Cliente":
        return redirect('/')
    else:
        fechaActual = datetime.today()
        conexion = mysql.connect()
        cursor = conexion.cursor()
        cursor.execute("SELECT id, fechaFin, estado FROM `tareas` ")
        fechasFin = cursor.fetchall()

        for fechaFin in fechasFin:
            diferenciaFecha = fechaFin[1] - fechaActual
            diferenciaFecha = int(diferenciaFecha.days)
            if diferenciaFecha >= 6:
                sql = "UPDATE tareas SET prioridad=%s WHERE id=%s;"
                datos = ("Baja", fechaFin[0])
                conexion = mysql.connect()
                cursor = conexion.cursor()
                # Se ejecuta el sql y los datos "values".
                cursor.execute(sql, datos)
                conexion.commit()
            elif diferenciaFecha == 5 or diferenciaFecha == 4:
                sql = "UPDATE tareas SET prioridad=%s WHERE id=%s;"
                datos = ("Media", fechaFin[0])
                conexion = mysql.connect()
                cursor = conexion.cursor()
                # Se ejecuta el sql y los datos "values".
                cursor.execute(sql, datos)
                conexion.commit()
            elif diferenciaFecha < 4:
                sql = "UPDATE tareas SET prioridad=%s WHERE id=%s;"
                datos = ("Alta", fechaFin[0])
                conexion = mysql.connect()
                cursor = conexion.cursor()
                # Se ejecuta el sql y los datos "values".
                cursor.execute(sql, datos)
                conexion.commit()
            if fechaFin[2] == "Finalizada":
                sql = "UPDATE tareas SET prioridad=%s WHERE id=%s;"
                datos = ("Ninguna", fechaFin[0])
                cursor.execute(sql, datos)
                conexion.commit()

        usuario = session.get('username')

        conexion = mysql.connect()
        cursor = conexion.cursor()

        cursor.execute("SELECT id FROM `cuentas` WHERE cuentas.username=%s", usuario)
        idCuentaUsuarioLogeado = cursor.fetchone()
        conexion.commit()

        cursor.execute("SELECT id FROM `clientes` WHERE idCC=%s", idCuentaUsuarioLogeado)
        idUsuarioLogeado = cursor.fetchone()
        conexion.commit()

        cursor.execute("SELECT * FROM `tareas` INNER JOIN `clientes` ON tareas.idCliente=clientes.id WHERE tareas.idCliente=%s;", idUsuarioLogeado)
        tareas = cursor.fetchall()
        conexion.commit()


        sqlContadorTareasAlta = "SELECT COUNT(prioridad) FROM tareas WHERE prioridad=%s and tareas.idCliente=%s"
        datosContadorTareasAlta = "Alta", idUsuarioLogeado
        cursor.execute(sqlContadorTareasAlta, datosContadorTareasAlta)
        tareasAlta = cursor.fetchone()
        conexion.commit()

        sqlContadorTareasMedia = "SELECT COUNT(prioridad) FROM tareas WHERE prioridad=%s and tareas.idCliente=%s"
        datosContadorTareasMedia = "Media", idUsuarioLogeado
        cursor.execute(sqlContadorTareasMedia, datosContadorTareasMedia)
        tareasMedia = cursor.fetchone()
        conexion.commit()

        sqlContadorTareasBaja = "SELECT COUNT(prioridad) FROM tareas WHERE prioridad=%s and tareas.idCliente=%s"
        datosContadorTareasBaja = "Baja", idUsuarioLogeado
        cursor.execute(sqlContadorTareasBaja, datosContadorTareasBaja)
        tareasBaja = cursor.fetchone()
        conexion.commit()

        sqlContadorTareas = "SELECT COUNT(estado) FROM tareas WHERE estado=%s and tareas.idCliente=%s"
        datosContadorTareas = "Finalizada", idUsuarioLogeado
        cursor.execute(sqlContadorTareas, datosContadorTareas)
        tareasFinalizadas = cursor.fetchone()
        conexion.commit()

        return render_template('cliente/index.html', tareas=tareas, idUsuarioLogeado=idUsuarioLogeado,
                               tareasAlta=tareasAlta, tareasMedia=tareasMedia, tareasBaja=tareasBaja, tareasFinalizadas=tareasFinalizadas)


@app.route('/cliente/estado/')
def cliente_estado():
    if session.get('logeado') == None:
        return redirect('/')
    elif session.get('logeado') == True and session.get('level') != "Cliente":
        return redirect('/')
    else:
        fechaActual = datetime.today()
        conexion = mysql.connect()
        cursor = conexion.cursor()
        cursor.execute("SELECT id, fechaFin, estado FROM `tareas` ")
        fechasFin = cursor.fetchall()

        for fechaFin in fechasFin:
            diferenciaFecha = fechaFin[1] - fechaActual
            diferenciaFecha = int(diferenciaFecha.days)
            if diferenciaFecha >= 6:
                sql = "UPDATE tareas SET prioridad=%s WHERE id=%s;"
                datos = ("Baja", fechaFin[0])
                conexion = mysql.connect()
                cursor = conexion.cursor()
                # Se ejecuta el sql y los datos "values".
                cursor.execute(sql, datos)
                conexion.commit()
            elif diferenciaFecha == 5 or diferenciaFecha == 4:
                sql = "UPDATE tareas SET prioridad=%s WHERE id=%s;"
                datos = ("Media", fechaFin[0])
                conexion = mysql.connect()
                cursor = conexion.cursor()
                # Se ejecuta el sql y los datos "values".
                cursor.execute(sql, datos)
                conexion.commit()
            elif diferenciaFecha < 4:
                sql = "UPDATE tareas SET prioridad=%s WHERE id=%s;"
                datos = ("Alta", fechaFin[0])
                conexion = mysql.connect()
                cursor = conexion.cursor()
                # Se ejecuta el sql y los datos "values".
                cursor.execute(sql, datos)
                conexion.commit()
            if fechaFin[2] == "Finalizada":
                sql = "UPDATE tareas SET prioridad=%s WHERE id=%s;"
                datos = ("Ninguna", fechaFin[0])
                cursor.execute(sql, datos)
                conexion.commit()

        usuario = session.get('username')

        conexion = mysql.connect()
        cursor = conexion.cursor()

        cursor.execute("SELECT id FROM `cuentas` WHERE cuentas.username=%s", usuario)
        idCuentaUsuarioLogeado = cursor.fetchone()
        conexion.commit()

        cursor.execute("SELECT id FROM `clientes` WHERE idCC=%s", idCuentaUsuarioLogeado)
        idUsuarioLogeado = cursor.fetchone()
        conexion.commit()

        cursor.execute("SELECT * FROM `tareas` INNER JOIN `clientes` ON tareas.idCliente=clientes.id WHERE tareas.idCliente=%s ORDER BY case when estado = 'Por Empezar' then 1 when estado = 'En proceso' then 2 when estado = 'Finalizada' then 3 end asc;", idUsuarioLogeado)
        tareas = cursor.fetchall()
        conexion.commit()

        sqlContadorTareasAlta = "SELECT COUNT(prioridad) FROM tareas WHERE prioridad=%s and tareas.idCliente=%s"
        datosContadorTareasAlta = "Alta", idUsuarioLogeado
        cursor.execute(sqlContadorTareasAlta, datosContadorTareasAlta)
        tareasAlta = cursor.fetchone()
        conexion.commit()

        sqlContadorTareasMedia = "SELECT COUNT(prioridad) FROM tareas WHERE prioridad=%s and tareas.idCliente=%s"
        datosContadorTareasMedia = "Media", idUsuarioLogeado
        cursor.execute(sqlContadorTareasMedia, datosContadorTareasMedia)
        tareasMedia = cursor.fetchone()
        conexion.commit()

        sqlContadorTareasBaja = "SELECT COUNT(prioridad) FROM tareas WHERE prioridad=%s and tareas.idCliente=%s"
        datosContadorTareasBaja = "Baja", idUsuarioLogeado
        cursor.execute(sqlContadorTareasBaja, datosContadorTareasBaja)
        tareasBaja = cursor.fetchone()
        conexion.commit()

        sqlContadorTareas = "SELECT COUNT(estado) FROM tareas WHERE estado=%s and tareas.idCliente=%s"
        datosContadorTareas = "Finalizada", idUsuarioLogeado
        cursor.execute(sqlContadorTareas, datosContadorTareas)
        tareasFinalizadas = cursor.fetchone()
        conexion.commit()

        return render_template('cliente/index.html', tareas=tareas, idUsuarioLogeado=idUsuarioLogeado,
                               tareasAlta=tareasAlta, tareasMedia=tareasMedia, tareasBaja=tareasBaja, tareasFinalizadas=tareasFinalizadas)

@app.route('/cliente/prioridad/')
def cliente_prioridad():
    if session.get('logeado') == None:
        return redirect('/')
    elif session.get('logeado') == True and session.get('level') != "Cliente":
        return redirect('/')
    else:
        fechaActual = datetime.today()
        conexion = mysql.connect()
        cursor = conexion.cursor()
        cursor.execute("SELECT id, fechaFin, estado FROM `tareas` ")
        fechasFin = cursor.fetchall()

        for fechaFin in fechasFin:
            diferenciaFecha = fechaFin[1] - fechaActual
            diferenciaFecha = int(diferenciaFecha.days)
            if diferenciaFecha >= 6:
                sql = "UPDATE tareas SET prioridad=%s WHERE id=%s;"
                datos = ("Baja", fechaFin[0])
                conexion = mysql.connect()
                cursor = conexion.cursor()
                # Se ejecuta el sql y los datos "values".
                cursor.execute(sql, datos)
                conexion.commit()
            elif diferenciaFecha == 5 or diferenciaFecha == 4:
                sql = "UPDATE tareas SET prioridad=%s WHERE id=%s;"
                datos = ("Media", fechaFin[0])
                conexion = mysql.connect()
                cursor = conexion.cursor()
                # Se ejecuta el sql y los datos "values".
                cursor.execute(sql, datos)
                conexion.commit()
            elif diferenciaFecha < 4:
                sql = "UPDATE tareas SET prioridad=%s WHERE id=%s;"
                datos = ("Alta", fechaFin[0])
                conexion = mysql.connect()
                cursor = conexion.cursor()
                # Se ejecuta el sql y los datos "values".
                cursor.execute(sql, datos)
                conexion.commit()
            if fechaFin[2] == "Finalizada":
                sql = "UPDATE tareas SET prioridad=%s WHERE id=%s;"
                datos = ("Ninguna", fechaFin[0])
                cursor.execute(sql, datos)
                conexion.commit()

        usuario = session.get('username')

        conexion = mysql.connect()
        cursor = conexion.cursor()

        cursor.execute("SELECT id FROM `cuentas` WHERE cuentas.username=%s", usuario)
        idCuentaUsuarioLogeado = cursor.fetchone()
        conexion.commit()

        cursor.execute("SELECT id FROM `clientes` WHERE idCC=%s", idCuentaUsuarioLogeado)
        idUsuarioLogeado = cursor.fetchone()
        conexion.commit()

        cursor.execute("SELECT * FROM `tareas` INNER JOIN `clientes` ON tareas.idCliente=clientes.id WHERE tareas.idCliente=%s ORDER BY case when prioridad = 'Agotada' then 1 when prioridad = 'Alta' then 2 when prioridad = 'Media' then 3 when prioridad = 'Baja' then 4 when prioridad = 'Ninguna' then 5 end asc;", idUsuarioLogeado)
        tareas = cursor.fetchall()
        conexion.commit()

        sqlContadorTareasAlta = "SELECT COUNT(prioridad) FROM tareas WHERE prioridad=%s and tareas.idCliente=%s"
        datosContadorTareasAlta = "Alta", idUsuarioLogeado
        cursor.execute(sqlContadorTareasAlta, datosContadorTareasAlta)
        tareasAlta = cursor.fetchone()
        conexion.commit()

        sqlContadorTareasMedia = "SELECT COUNT(prioridad) FROM tareas WHERE prioridad=%s and tareas.idCliente=%s"
        datosContadorTareasMedia = "Media", idUsuarioLogeado
        cursor.execute(sqlContadorTareasMedia, datosContadorTareasMedia)
        tareasMedia = cursor.fetchone()
        conexion.commit()

        sqlContadorTareasBaja = "SELECT COUNT(prioridad) FROM tareas WHERE prioridad=%s and tareas.idCliente=%s"
        datosContadorTareasBaja = "Baja", idUsuarioLogeado
        cursor.execute(sqlContadorTareasBaja, datosContadorTareasBaja)
        tareasBaja = cursor.fetchone()
        conexion.commit()

        sqlContadorTareas = "SELECT COUNT(estado) FROM tareas WHERE estado=%s and tareas.idCliente=%s"
        datosContadorTareas = "Finalizada", idUsuarioLogeado
        cursor.execute(sqlContadorTareas, datosContadorTareas)
        tareasFinalizadas = cursor.fetchone()
        conexion.commit()

        return render_template('cliente/index.html', tareas=tareas, idUsuarioLogeado=idUsuarioLogeado,
                               tareasAlta=tareasAlta, tareasMedia=tareasMedia, tareasBaja=tareasBaja, tareasFinalizadas=tareasFinalizadas)

@app.route('/cliente/titulo/')
def cliente_titulo():
    if session.get('logeado') == None:
        return redirect('/')
    elif session.get('logeado') == True and session.get('level') != "Cliente":
        return redirect('/')
    else:
        fechaActual = datetime.today()
        conexion = mysql.connect()
        cursor = conexion.cursor()
        cursor.execute("SELECT id, fechaFin, estado FROM `tareas` ")
        fechasFin = cursor.fetchall()

        for fechaFin in fechasFin:
            diferenciaFecha = fechaFin[1] - fechaActual
            diferenciaFecha = int(diferenciaFecha.days)
            if diferenciaFecha >= 6:
                sql = "UPDATE tareas SET prioridad=%s WHERE id=%s;"
                datos = ("Baja", fechaFin[0])
                conexion = mysql.connect()
                cursor = conexion.cursor()
                # Se ejecuta el sql y los datos "values".
                cursor.execute(sql, datos)
                conexion.commit()
            elif diferenciaFecha == 5 or diferenciaFecha == 4:
                sql = "UPDATE tareas SET prioridad=%s WHERE id=%s;"
                datos = ("Media", fechaFin[0])
                conexion = mysql.connect()
                cursor = conexion.cursor()
                # Se ejecuta el sql y los datos "values".
                cursor.execute(sql, datos)
                conexion.commit()
            elif diferenciaFecha < 4:
                sql = "UPDATE tareas SET prioridad=%s WHERE id=%s;"
                datos = ("Alta", fechaFin[0])
                conexion = mysql.connect()
                cursor = conexion.cursor()
                # Se ejecuta el sql y los datos "values".
                cursor.execute(sql, datos)
                conexion.commit()
            if fechaFin[2] == "Finalizada":
                sql = "UPDATE tareas SET prioridad=%s WHERE id=%s;"
                datos = ("Ninguna", fechaFin[0])
                cursor.execute(sql, datos)
                conexion.commit()

        usuario = session.get('username')

        conexion = mysql.connect()
        cursor = conexion.cursor()

        cursor.execute("SELECT id FROM `cuentas` WHERE cuentas.username=%s", usuario)
        idCuentaUsuarioLogeado = cursor.fetchone()
        conexion.commit()

        cursor.execute("SELECT id FROM `clientes` WHERE idCC=%s", idCuentaUsuarioLogeado)
        idUsuarioLogeado = cursor.fetchone()
        conexion.commit()

        cursor.execute("SELECT * FROM `tareas` INNER JOIN `clientes` ON tareas.idCliente=clientes.id WHERE tareas.idCliente=%s ORDER BY tareas.titulo", idUsuarioLogeado)
        tareas = cursor.fetchall()
        conexion.commit()

        sqlContadorTareasAlta = "SELECT COUNT(prioridad) FROM tareas WHERE prioridad=%s and tareas.idCliente=%s"
        datosContadorTareasAlta = "Alta", idUsuarioLogeado
        cursor.execute(sqlContadorTareasAlta, datosContadorTareasAlta)
        tareasAlta = cursor.fetchone()
        conexion.commit()

        sqlContadorTareasMedia = "SELECT COUNT(prioridad) FROM tareas WHERE prioridad=%s and tareas.idCliente=%s"
        datosContadorTareasMedia = "Media", idUsuarioLogeado
        cursor.execute(sqlContadorTareasMedia, datosContadorTareasMedia)
        tareasMedia = cursor.fetchone()
        conexion.commit()

        sqlContadorTareasBaja = "SELECT COUNT(prioridad) FROM tareas WHERE prioridad=%s and tareas.idCliente=%s"
        datosContadorTareasBaja = "Baja", idUsuarioLogeado
        cursor.execute(sqlContadorTareasBaja, datosContadorTareasBaja)
        tareasBaja = cursor.fetchone()
        conexion.commit()

        sqlContadorTareas = "SELECT COUNT(estado) FROM tareas WHERE estado=%s and tareas.idCliente=%s"
        datosContadorTareas = "Finalizada", idUsuarioLogeado
        cursor.execute(sqlContadorTareas, datosContadorTareas)
        tareasFinalizadas = cursor.fetchone()
        conexion.commit()

        return render_template('cliente/index.html', tareas=tareas, idUsuarioLogeado=idUsuarioLogeado,
                               tareasAlta=tareasAlta, tareasMedia=tareasMedia, tareasBaja=tareasBaja, tareasFinalizadas=tareasFinalizadas)

if __name__ == '__main__':
    app.run(debug=True)