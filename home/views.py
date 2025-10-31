from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from .models import users, pacientes, veterinarios, citas
from collections import Counter
from bson import ObjectId
from datetime import datetime, time, timedelta

# ---- Dashboard principal ----
def index(request):
    """Dashboard principal con estadísticas según el rol."""
    if "user" not in request.session:
        messages.warning(request, "Please log in first.")
        return redirect("login")

    username = request.session.get("user")
    rol = request.session.get("rol")
    user = users.find_one({"User": username})
    
    if not user:
        messages.error(request, "User not found.")
        return redirect("login")
    
    user_id = str(user["_id"])
    
    # Inicializar contexto
    context = {
        "rol": rol,
        "username": username,
    }
    
    # ========== ESTADÍSTICAS PARA ADMINISTRADOR ==========
    if rol == "Administrador":
        # Total de usuarios por rol
        total_users = users.count_documents({})
        total_clientes = users.count_documents({"Rol": "Cliente"})
        total_veterinarios_users = users.count_documents({"Rol": "Veterinario"})
        total_admins = users.count_documents({"Rol": "Administrador"})
        
        # Total de mascotas
        total_mascotas = pacientes.count_documents({})
        
        # Mascotas por especie
        especies = list(pacientes.find({}, {"especie": 1}))
        especies_counter = Counter([m.get("especie", "Unknown") for m in especies])
        especies_data = [{"especie": k, "cantidad": v} for k, v in especies_counter.most_common(5)]
        
        # Total de veterinarios (perfiles)
        total_veterinarios = veterinarios.count_documents({})
        
        # Citas totales
        total_citas = citas.count_documents({})
        citas_pendientes = citas.count_documents({"estado": "Pendiente"})
        citas_completadas = citas.count_documents({"estado": "Completada"})
        citas_canceladas = citas.count_documents({"estado": "Cancelada"})
        
        # Citas de hoy
        hoy = datetime.now().strftime("%Y-%m-%d")
        citas_hoy = citas.count_documents({"fecha": {"$regex": f"^{hoy}"}})
        
        # Citas de esta semana
        inicio_semana = (datetime.now() - timedelta(days=datetime.now().weekday())).strftime("%Y-%m-%d")
        citas_semana = citas.count_documents({"fecha": {"$gte": inicio_semana}})
        
        # Top 5 veterinarios con más citas
        todas_citas = list(citas.find({}, {"id_veterinario": 1}))
        vet_counter = Counter([c.get("id_veterinario") for c in todas_citas if c.get("id_veterinario")])
        top_vets = []
        for vet_id, count in vet_counter.most_common(5):
            vet = veterinarios.find_one({"_id": ObjectId(vet_id)})
            if vet:
                top_vets.append({
                    "nombre": vet.get("nombre", "Unknown"),
                    "especialidad": vet.get("especialidad", "N/A"),
                    "citas": count
                })
        
        context.update({
            "total_users": total_users,
            "total_clientes": total_clientes,
            "total_veterinarios_users": total_veterinarios_users,
            "total_admins": total_admins,
            "total_mascotas": total_mascotas,
            "especies_data": especies_data,
            "total_veterinarios": total_veterinarios,
            "total_citas": total_citas,
            "citas_pendientes": citas_pendientes,
            "citas_completadas": citas_completadas,
            "citas_canceladas": citas_canceladas,
            "citas_hoy": citas_hoy,
            "citas_semana": citas_semana,
            "top_vets": top_vets,
        })
    
    # ========== ESTADÍSTICAS PARA VETERINARIO ==========
    elif rol == "Veterinario":
        # Todas las citas (el veterinario ve todas)
        total_citas = citas.count_documents({})
        citas_pendientes = citas.count_documents({"estado": "Pendiente"})
        citas_completadas = citas.count_documents({"estado": "Completada"})
        
        # Citas de hoy
        hoy = datetime.now().strftime("%Y-%m-%d")
        citas_hoy_list = list(citas.find({"fecha": {"$regex": f"^{hoy}"}}))
        
        # Enriquecer citas de hoy con info de mascota y veterinario
        for c in citas_hoy_list:
            mascota = pacientes.find_one({"_id": ObjectId(c.get("id_paciente"))}) if c.get("id_paciente") else None
            vet = veterinarios.find_one({"_id": ObjectId(c.get("id_veterinario"))}) if c.get("id_veterinario") else None
            
            c["mascota_nombre"] = mascota.get("nombre", "Unknown") if mascota else "Unknown"
            c["veterinario_nombre"] = vet.get("nombre", "Unknown") if vet else "Unknown"
            
            try:
                fecha_cita = datetime.strptime(c.get("fecha", ""), "%Y-%m-%dT%H:%M")
                c["hora"] = fecha_cita.strftime("%H:%M")
            except:
                c["hora"] = "N/A"
        
        # Total de mascotas en el sistema
        total_mascotas = pacientes.count_documents({})
        
        # Próximas 5 citas
        todas_citas_futuras = list(citas.find({"fecha": {"$gte": datetime.now().strftime("%Y-%m-%dT%H:%M")}}).limit(5))
        proximas_citas = []
        for c in todas_citas_futuras:
            mascota = pacientes.find_one({"_id": ObjectId(c.get("id_paciente"))})
            vet = veterinarios.find_one({"_id": ObjectId(c.get("id_veterinario"))})
            
            try:
                fecha_dt = datetime.strptime(c.get("fecha", ""), "%Y-%m-%dT%H:%M")
                proximas_citas.append({
                    "mascota": mascota.get("nombre", "Unknown") if mascota else "Unknown",
                    "veterinario": vet.get("nombre", "Unknown") if vet else "Unknown",
                    "fecha": fecha_dt.strftime("%Y-%m-%d"),
                    "hora": fecha_dt.strftime("%H:%M"),
                    "motivo": c.get("motivo", "N/A")
                })
            except:
                pass
        
        context.update({
            "total_citas": total_citas,
            "citas_pendientes": citas_pendientes,
            "citas_completadas": citas_completadas,
            "citas_hoy": len(citas_hoy_list),
            "citas_hoy_list": citas_hoy_list,
            "total_mascotas": total_mascotas,
            "proximas_citas": proximas_citas,
        })
    
    # ========== ESTADÍSTICAS PARA CLIENTE ==========
    else:  # Cliente
        # Mascotas del cliente
        mis_mascotas = list(pacientes.find({"id_user": user_id}))
        total_mis_mascotas = len(mis_mascotas)
        
        # Especies de mis mascotas
        especies_mis_mascotas = Counter([m.get("especie", "Unknown") for m in mis_mascotas])
        
        # Citas del cliente
        mascota_ids = [str(m["_id"]) for m in mis_mascotas]
        mis_citas = list(citas.find({"id_paciente": {"$in": mascota_ids}}))
        
        total_mis_citas = len(mis_citas)
        mis_citas_pendientes = len([c for c in mis_citas if c.get("estado") == "Pendiente"])
        mis_citas_completadas = len([c for c in mis_citas if c.get("estado") == "Completada"])
        
        # Próximas citas
        proximas_citas = []
        for c in mis_citas:
            try:
                fecha_dt = datetime.strptime(c.get("fecha", ""), "%Y-%m-%dT%H:%M")
                if fecha_dt >= datetime.now():
                    mascota = pacientes.find_one({"_id": ObjectId(c.get("id_paciente"))})
                    vet = veterinarios.find_one({"_id": ObjectId(c.get("id_veterinario"))})
                    
                    proximas_citas.append({
                        "mascota": mascota.get("nombre", "Unknown") if mascota else "Unknown",
                        "veterinario": vet.get("nombre", "Unknown") if vet else "Unknown",
                        "fecha": fecha_dt.strftime("%Y-%m-%d"),
                        "hora": fecha_dt.strftime("%H:%M"),
                        "motivo": c.get("motivo", "N/A")
                    })
            except:
                pass
        
        # Ordenar por fecha
        proximas_citas = sorted(proximas_citas, key=lambda x: x["fecha"])[:5]
        
        # Historial de mascotas con más citas
        mascotas_con_citas = []
        for mascota in mis_mascotas:
            num_citas = citas.count_documents({"id_paciente": str(mascota["_id"])})
            mascotas_con_citas.append({
                "nombre": mascota.get("nombre", "Unknown"),
                "especie": mascota.get("especie", "Unknown"),
                "citas": num_citas
            })
        
        mascotas_con_citas = sorted(mascotas_con_citas, key=lambda x: x["citas"], reverse=True)
        
        context.update({
            "total_mis_mascotas": total_mis_mascotas,
            "mis_mascotas": mis_mascotas,
            "especies_mis_mascotas": dict(especies_mis_mascotas),
            "total_mis_citas": total_mis_citas,
            "mis_citas_pendientes": mis_citas_pendientes,
            "mis_citas_completadas": mis_citas_completadas,
            "proximas_citas": proximas_citas,
            "mascotas_con_citas": mascotas_con_citas,
        })
    
    return render(request, "index.html", context)


#  ---- REGISTRO DE USUARIO ----
def register(request):
    """Registro de nuevo usuario con campos adicionales: Phone y Address"""
    if request.method == "POST":
        user = request.POST.get("user")
        email = request.POST.get("email")
        password = request.POST.get("password")
        phone = request.POST.get("phone", "")  # Campo nuevo - opcional
        address = request.POST.get("address", "")  # Campo nuevo - opcional

        # Validar que el email no esté registrado
        if users.find_one({"Email": email}):
            messages.error(request, "This email is already registered.")
            return redirect("register")

        # Validar que el username no esté registrado
        if users.find_one({"User": user}):
            messages.error(request, "This username is already taken.")
            return redirect("register")

        # Crear nuevo usuario con todos los campos
        users.insert_one({
            "User": user,
            "Email": email,
            "Password": password,  # IMPORTANTE: En producción, hashea la contraseña
            "Phone": phone,
            "Address": address,
            "Rol": "Cliente"  # Por defecto es Cliente
        })
        
        messages.success(request, "Registration successful! Please log in.")
        return redirect("login")

    return render(request, "register.html")

# ---- Inicio de sesión ----
def login(request):
    if request.method == "POST":
        email = request.POST["email"]
        password = request.POST["password"]
        user = users.find_one({"Email": email, "Password": password})

        if user:
            request.session["user"] = user["User"]
            request.session["rol"] = user["Rol"]

            messages.success(request, f"Bienvenido {user['User']}")
            return redirect("index")
        else:
            messages.error(request, "Credenciales incorrectas.")
            return redirect("login")

    return render(request, "login.html")

# ---- Cerrar sesión ----
def logout(request):
    request.session.flush()
    messages.info(request, "Has cerrado sesión correctamente.")
    return redirect("index")


# ------------------ CRUD de Pacientes ------------------

def list_pacientes(request):
    """Lista los pacientes del usuario o todos si es admin."""
    if "user" not in request.session:
        messages.warning(request, "Debes iniciar sesión para ver tus pacientes.")
        return redirect("login")

    rol = request.session.get("rol")
    username = request.session.get("user")

    if rol == "Administrador":
        data = list(pacientes.find())
    else:
        user = users.find_one({"User": username})
        data = list(pacientes.find({"id_user": str(user["_id"])}))

    # Convertir ObjectId a str y renombrar el campo
    for p in data:
        p["id"] = str(p["_id"])
        del p["_id"]

    return render(request, "patients_list.html", {"patients": data, "rol": rol, "username": username})


def add_paciente(request):
    """Agrega un nuevo paciente."""
    if "user" not in request.session:
        messages.warning(request, "Inicia sesión primero.")
        return redirect("login")

    if request.method == "POST":
        nombre = request.POST["nombre"]
        especie = request.POST["especie"]
        raza = request.POST["raza"]
        user = users.find_one({"User": request.session["user"]})

        pacientes.insert_one({
            "nombre": nombre,
            "especie": especie,
            "raza": raza,
            "id_user": str(user["_id"])
        })

        messages.success(request, "Paciente agregado exitosamente.")
        return redirect("list_pacientes")

    return render(request, "patients_form.html", {"action": "Add"})


def edit_paciente(request, id):
    """Edita los datos de un paciente."""
    paciente = pacientes.find_one({"_id": ObjectId(id)})

    if not paciente:
        messages.error(request, "Paciente no encontrado.")
        return redirect("list_pacientes")

    if request.method == "POST":
        nombre = request.POST["nombre"]
        especie = request.POST["especie"]
        raza = request.POST["raza"]

        pacientes.update_one({"_id": ObjectId(id)}, {"$set": {
            "nombre": nombre,
            "especie": especie,
            "raza": raza
        }})

        messages.success(request, "Paciente actualizado correctamente.")
        return redirect("list_pacientes")

    return render(request, "patients_form.html", {"action": "Edit", "paciente": paciente})


def delete_paciente(request, id):
    """Elimina un paciente."""
    pacientes.delete_one({"_id": ObjectId(id)})
    messages.info(request, "Paciente eliminado.")
    return redirect("list_pacientes")

# ------------------ CRUD de Veterinarios ------------------

def list_veterinarios(request):
    """Lista todos los veterinarios (solo admin)."""
    if "user" not in request.session:
        messages.warning(request, "Please log in first.")
        return redirect("login")

    rol = request.session.get("rol")
    if rol != "Administrador":
        messages.error(request, "Access denied. Administrator privileges required.")
        return redirect("index")

    # Obtener todos los veterinarios
    data = list(veterinarios.find())
    for v in data:
        v["id"] = str(v["_id"])

    context = {
        "vets": data,
        "rol": rol,
        "username": request.session.get("user")
    }

    return render(request, "vets_list.html", context)


def add_veterinario(request):
    """Agrega un nuevo veterinario con información completa."""
    if request.session.get("rol") != "Administrador":
        messages.error(request, "Only administrators can add veterinarians.")
        return redirect("index")

    if request.method == "POST":
        nombre = request.POST.get("nombre")
        especialidad = request.POST.get("especialidad")
        email = request.POST.get("email", "")  # Campo nuevo - opcional
        phone = request.POST.get("phone", "")  # Campo nuevo - opcional
        license = request.POST.get("license", "")  # Campo nuevo - opcional

        # Validar que el nombre no esté vacío
        if not nombre or not especialidad:
            messages.error(request, "Name and specialty are required.")
            return redirect("add_veterinario")

        # Validar que el email no esté en uso (si se proporciona)
        if email and veterinarios.find_one({"email": email}):
            messages.error(request, "A veterinarian with this email already exists.")
            return redirect("add_veterinario")

        # Validar que la licencia no esté en uso (si se proporciona)
        if license and veterinarios.find_one({"license": license}):
            messages.error(request, "A veterinarian with this license number already exists.")
            return redirect("add_veterinario")

        # Insertar nuevo veterinario con todos los campos
        veterinarios.insert_one({
            "nombre": nombre,
            "especialidad": especialidad,
            "email": email,
            "phone": phone,
            "license": license
        })
        
        messages.success(request, f"Dr. {nombre} added successfully.")
        return redirect("list_veterinarios")

    return render(request, "vets_form.html", {"action": "Add", "vet": {}})


def edit_veterinario(request, id):
    """Edita un veterinario existente con información completa."""
    if request.session.get("rol") != "Administrador":
        messages.error(request, "Only administrators can edit veterinarians.")
        return redirect("index")

    vet = veterinarios.find_one({"_id": ObjectId(id)})
    if not vet:
        messages.error(request, "Veterinarian not found.")
        return redirect("list_veterinarios")

    if request.method == "POST":
        nombre = request.POST.get("nombre")
        especialidad = request.POST.get("especialidad")
        email = request.POST.get("email", "")  # Campo nuevo
        phone = request.POST.get("phone", "")  # Campo nuevo
        license = request.POST.get("license", "")  # Campo nuevo

        # Validar que el nombre no esté vacío
        if not nombre or not especialidad:
            messages.error(request, "Name and specialty are required.")
            return render(request, "vets_form.html", {"action": "Edit", "vet": vet})

        # Validar que el email no esté en uso por otro veterinario
        if email:
            existing_email = veterinarios.find_one({
                "email": email,
                "_id": {"$ne": ObjectId(id)}
            })
            if existing_email:
                messages.error(request, "Another veterinarian already has this email.")
                return render(request, "vets_form.html", {"action": "Edit", "vet": vet})

        # Validar que la licencia no esté en uso por otro veterinario
        if license:
            existing_license = veterinarios.find_one({
                "license": license,
                "_id": {"$ne": ObjectId(id)}
            })
            if existing_license:
                messages.error(request, "Another veterinarian already has this license number.")
                return render(request, "vets_form.html", {"action": "Edit", "vet": vet})

        # Actualizar veterinario
        veterinarios.update_one({"_id": ObjectId(id)}, {"$set": {
            "nombre": nombre,
            "especialidad": especialidad,
            "email": email,
            "phone": phone,
            "license": license
        }})
        
        messages.success(request, f"Dr. {nombre} updated successfully.")
        return redirect("list_veterinarios")

    return render(request, "vets_form.html", {"action": "Edit", "vet": vet})


def delete_veterinario(request, id):
    """Elimina un veterinario del sistema."""
    if request.session.get("rol") != "Administrador":
        messages.error(request, "Only administrators can delete veterinarians.")
        return redirect("index")

    vet = veterinarios.find_one({"_id": ObjectId(id)})
    if not vet:
        messages.error(request, "Veterinarian not found.")
        return redirect("list_veterinarios")

    # Opcional: Verificar si el veterinario tiene citas pendientes
    # from tu_archivo_db import citas
    # citas_pendientes = citas.count_documents({
    #     "veterinario_id": str(id),
    #     "estado": "Pendiente"
    # })
    # if citas_pendientes > 0:
    #     messages.error(request, f"Cannot delete Dr. {vet['nombre']}. There are {citas_pendientes} pending appointments.")
    #     return redirect("list_veterinarios")

    veterinarios.delete_one({"_id": ObjectId(id)})
    messages.info(request, f"Dr. {vet['nombre']} has been deleted from the system.")
    return redirect("list_veterinarios")

# ------------------ CRUD de Citas ------------------




# -------------------- FUNCIÓN AUXILIAR: ACTUALIZAR ESTADOS AUTOMÁTICAMENTE --------------------
def actualizar_estados_citas_automaticamente():
    """
    Actualiza automáticamente el estado de las citas a 'Completada' 
    cuando ha pasado el tiempo suficiente desde su inicio.
    
    Reglas:
    - Citas normales (duración 1 hora): Se completan después de 1 hora
    - Citas veterinarias (duración >1 hora): Se completan después de su duración especificada
    """
    try:
        ahora = datetime.now()
        
        # Buscar todas las citas pendientes
        citas_pendientes = citas.find({"estado": "Pendiente"})
        
        citas_actualizadas = 0
        
        for cita in citas_pendientes:
            try:
                # Obtener la fecha de inicio de la cita
                fecha_inicio = datetime.strptime(cita.get("fecha", ""), "%Y-%m-%dT%H:%M")
                
                # Obtener la duración (por defecto 1 hora)
                duracion = cita.get("duracion", 1)
                
                # Calcular cuándo debería completarse
                fecha_completado = fecha_inicio + timedelta(hours=duracion)
                
                # Si ya pasó el tiempo, marcar como completada
                if ahora >= fecha_completado:
                    citas.update_one(
                        {"_id": cita["_id"]},
                        {"$set": {"estado": "Completada"}}
                    )
                    citas_actualizadas += 1
                    
            except Exception as e:
                # Si hay error con una cita específica, continuar con las demás
                print(f"Error procesando cita {cita.get('_id')}: {e}")
                continue
        
        if citas_actualizadas > 0:
            print(f"✅ {citas_actualizadas} citas actualizadas a 'Completada'")
            
    except Exception as e:
        print(f"❌ Error al actualizar estados: {e}")


# -------------------- LISTAR CITAS (CON CONTADORES CORRECTOS) --------------------

def list_citas(request):
    """Lista todas las citas según el rol."""
    if "user" not in request.session:
        messages.warning(request, "Please log in first.")
        return redirect("login")

    # Actualizar estados automáticamente
    actualizar_estados_citas_automaticamente()

    rol = request.session.get("rol")
    username = request.session.get("user")

    data = []

    # Obtener citas según rol...
    if rol == "Administrador":
        data = list(citas.find())
    elif rol == "Veterinario":
        data = list(citas.find())
    else:
        user = users.find_one({"User": username})
        if not user:
            messages.error(request, "User not found.")
            return redirect("index")
        user_id = str(user["_id"])
        mascotas = list(pacientes.find({"id_user": user_id}))
        mascota_ids = [str(m["_id"]) for m in mascotas]
        data = list(citas.find({"id_paciente": {"$in": mascota_ids}}))

    # 🔹 ORDENAR POR FECHA DESCENDENTE (MÁS RECIENTE PRIMERO)
    # Esto se hace antes de procesar los datos
    data.sort(key=lambda x: x.get("fecha", "1970-01-01T00:00"), reverse=True)

    # Calcular contadores
    total_citas = len(data)
    pendientes = len([c for c in data if c.get("estado") == "Pendiente"])
    completadas = len([c for c in data if c.get("estado") == "Completada"])
    canceladas = len([c for c in data if c.get("estado") == "Cancelada"])

    # Enriquecer datos
    current_user = users.find_one({"User": username})
    current_user_id = str(current_user["_id"]) if current_user else None
    
    for c in data:
        if "_id" in c:
            c["id"] = str(c["_id"])
            c["id_str"] = str(c["_id"])
        else:
            c["id"] = None
            c["id_str"] = None

        # 🔹 GUARDAR FECHA ORIGINAL PARA EL FRONTEND
        c["fecha_original"] = c.get("fecha", "")

        # Buscar datos de la mascota
        if "id_paciente" in c:
            mascota = pacientes.find_one({"_id": ObjectId(c["id_paciente"])})
            if mascota:
                c["mascota_nombre"] = mascota.get("nombre", "Unknown Pet")
                c["mascota_especie"] = mascota.get("especie", "Unknown")
                c["mascota_owner_id"] = mascota.get("id_user")

        # Buscar datos del veterinario
        if "id_veterinario" in c:
            vet = veterinarios.find_one({"_id": ObjectId(c["id_veterinario"])})
            if vet:
                c["veterinario_nombre"] = vet.get("nombre", "Unknown Vet")

        # Separar fecha y hora para mostrar bonito
        try:
            fecha_cita = datetime.strptime(c.get("fecha", ""), "%Y-%m-%dT%H:%M")
            c["fecha"] = fecha_cita.strftime("%Y-%m-%d")
            c["hora"] = fecha_cita.strftime("%H:%M")
        except Exception:
            c["fecha"] = c.get("fecha", "")
            c["hora"] = ""

        # Sistema de permisos
        c["puede_editar"] = False
        c["puede_cancelar"] = False
        
        if rol == "Administrador":
            c["puede_editar"] = True
            c["puede_cancelar"] = True
        elif rol == "Cliente":
            if c.get("mascota_owner_id") == current_user_id:
                if c.get("estado") == "Pendiente":
                    c["puede_editar"] = True
                    c["puede_cancelar"] = True
        elif rol == "Veterinario":
            if c.get("id_veterinario") == current_user_id:
                if c.get("estado") == "Pendiente":
                    c["puede_editar"] = True
                c["puede_cancelar"] = False

    return render(request, "appointments_list.html", {
        "citas": data,
        "rol": rol,
        "username": username,
        "total_citas": total_citas,
        "pendientes": pendientes,
        "completadas": completadas,
        "canceladas": canceladas
    })

# -------------------- CANCELAR CITA (NUEVO) --------------------
def cancel_cita(request, id):
    """
    Cancela una cita cambiando su estado a 'Cancelada'.
    NO elimina la cita de la base de datos.
    """
    if "user" not in request.session:
        messages.warning(request, "Please log in first.")
        return redirect("login")
    
    cita = citas.find_one({"_id": ObjectId(id)})
    if not cita:
        messages.error(request, "Appointment not found.")
        return redirect("list_citas")

    # 🔹 VALIDAR PERMISOS
    username = request.session.get("user")
    rol = request.session.get("rol")
    current_user = users.find_one({"User": username})
    
    if not current_user:
        messages.error(request, "User not found.")
        return redirect("list_citas")
    
    current_user_id = str(current_user["_id"])
    
    # Verificar permisos según el rol
    tiene_permiso = False
    
    if rol == "Administrador":
        # Admin puede cancelar cualquier cita
        tiene_permiso = True
    
    elif rol == "Cliente":
        # Cliente solo puede cancelar citas de sus mascotas
        mascota = pacientes.find_one({"_id": ObjectId(cita.get("id_paciente"))})
        if mascota and mascota.get("id_user") == current_user_id:
            tiene_permiso = True
    
    elif rol == "Veterinario":
        # Los veterinarios NO pueden cancelar citas
        messages.error(request, "Veterinarians cannot cancel appointments. Please contact the pet owner or an administrator.")
        return redirect("list_citas")
    
    if not tiene_permiso:
        messages.error(request, "You don't have permission to cancel this appointment.")
        return redirect("list_citas")

    # Verificar que la cita esté pendiente
    if cita.get("estado") != "Pendiente":
        messages.warning(request, f"Cannot cancel an appointment that is already {cita.get('estado')}.")
        return redirect("list_citas")

    # 🔹 Cambiar estado a "Cancelada" (NO eliminar)
    citas.update_one(
        {"_id": ObjectId(id)},
        {"$set": {
            "estado": "Cancelada",
            "fecha_cancelacion": datetime.now().strftime("%Y-%m-%dT%H:%M")
        }}
    )
    
    messages.info(request, "Appointment cancelled successfully.")
    return redirect("list_citas")


# -------------------- AGENDAR CITA (SIN CAMBIOS MAYORES) --------------------
def add_cita(request):
    """Agrega una nueva cita con validaciones."""
    if "user" not in request.session:
        messages.warning(request, "Please log in first.")
        return redirect("login")

    username = request.session.get("user")
    rol = request.session.get("rol")
    user = users.find_one({"User": username})
    
    if not user:
        messages.error(request, "User not found.")
        return redirect("index")
    
    user_id = str(user["_id"])

    mascotas = []
    
    if rol == "Cliente":
        for m in pacientes.find({"id_user": user_id}):
            m["id"] = str(m["_id"])
            m["display_name"] = f"{m.get('nombre', 'Unknown')} ({m.get('especie', 'Unknown')})"
            mascotas.append(m)
    else:
        for m in pacientes.find():
            m["id"] = str(m["_id"])
            owner = users.find_one({"_id": ObjectId(m.get("id_user"))}) if m.get("id_user") else None
            owner_name = owner.get("User", "Unknown Owner") if owner else "Unknown Owner"
            m["display_name"] = f"{m.get('nombre', 'Unknown')} ({m.get('especie', 'Unknown')}) - Owner: {owner_name}"
            mascotas.append(m)

    vets = []
    for v in veterinarios.find():
        v["id"] = str(v["_id"])
        vets.append(v)

    if request.method == "POST":
        id_paciente = request.POST.get("paciente")
        id_veterinario = request.POST.get("veterinario")
        fecha = request.POST.get("fecha")
        motivo = request.POST.get("motivo")
        duracion = int(request.POST.get("duracion", 1))

        if not fecha:
            messages.error(request, "Please select a valid date and time.")
            return render(request, "appointments_form.html", {
                "mascotas": mascotas,
                "vets": vets,
                "action": "Add",
                "rol": rol
            })

        fecha_cita = datetime.strptime(fecha, "%Y-%m-%dT%H:%M")
        hora = fecha_cita.time()

        # Validaciones de horario
        if hora < time(8, 0) or hora >= time(19, 0):
            messages.error(request, "Appointments must be between 8:00 a.m. and 7:00 p.m.")
            return render(request, "appointments_form.html", {
                "mascotas": mascotas,
                "vets": vets,
                "action": "Add",
                "rol": rol
            })

        if time(12, 0) <= hora < time(14, 0):
            messages.error(request, "Lunch time (12–2 p.m.) is unavailable.")
            return render(request, "appointments_form.html", {
                "mascotas": mascotas,
                "vets": vets,
                "action": "Add",
                "rol": rol
            })

        # Calcular fin de la cita
        fecha_fin = fecha_cita + timedelta(hours=duracion)

        # Verificar disponibilidad del veterinario
        citas_veterinario = list(citas.find({
            "id_veterinario": id_veterinario,
            "estado": {"$ne": "Cancelada"}  # Ignorar citas canceladas
        }))
        
        conflicto_encontrado = False
        for cita_existente in citas_veterinario:
            try:
                fecha_existente = datetime.strptime(cita_existente.get("fecha", ""), "%Y-%m-%dT%H:%M")
                
                if "fecha_fin" in cita_existente:
                    fecha_fin_existente = datetime.strptime(cita_existente["fecha_fin"], "%Y-%m-%dT%H:%M")
                else:
                    fecha_fin_existente = fecha_existente + timedelta(hours=1)
                
                if fecha_cita < fecha_fin_existente and fecha_fin > fecha_existente:
                    conflicto_encontrado = True
                    break
                    
            except Exception:
                continue
        
        if conflicto_encontrado:
            messages.error(request, "This veterinarian is already booked during that time.")
            return render(request, "appointments_form.html", {
                "mascotas": mascotas,
                "vets": vets,
                "action": "Add",
                "rol": rol
            })

        # Insertar cita
        citas.insert_one({
            "id_paciente": id_paciente,
            "id_veterinario": id_veterinario,
            "fecha": fecha,
            "fecha_fin": fecha_fin.strftime("%Y-%m-%dT%H:%M"),
            "motivo": motivo,
            "estado": "Pendiente",
            "duracion": duracion,
            "fecha_creacion": datetime.now().strftime("%Y-%m-%dT%H:%M")
        })
        messages.success(request, "Appointment successfully scheduled.")
        return redirect("list_citas")

    return render(request, "appointments_form.html", {
        "mascotas": mascotas,
        "vets": vets,
        "action": "Add",
        "rol": rol
    })


# -------------------- EDITAR CITA (SIN CAMBIOS) --------------------
def edit_cita(request, id):
    """Edita una cita con validación de permisos."""
    if "user" not in request.session:
        messages.warning(request, "Please log in first.")
        return redirect("login")
    
    cita = citas.find_one({"_id": ObjectId(id)})
    if not cita:
        messages.error(request, "Appointment not found.")
        return redirect("list_citas")

    username = request.session.get("user")
    rol = request.session.get("rol")
    current_user = users.find_one({"User": username})
    
    if not current_user:
        messages.error(request, "User not found.")
        return redirect("list_citas")
    
    current_user_id = str(current_user["_id"])
    
    # Verificar permisos
    tiene_permiso = False
    
    if rol == "Administrador":
        tiene_permiso = True
    elif rol == "Cliente":
        mascota = pacientes.find_one({"_id": ObjectId(cita.get("id_paciente"))})
        if mascota and mascota.get("id_user") == current_user_id:
            if cita.get("estado") == "Pendiente":
                tiene_permiso = True
    elif rol == "Veterinario":
        if cita.get("id_veterinario") == current_user_id:
            if cita.get("estado") == "Pendiente":
                tiene_permiso = True
    
    if not tiene_permiso:
        messages.error(request, "You don't have permission to edit this appointment.")
        return redirect("list_citas")
    
    # ============================================
    # 🔧 SECCIÓN MODIFICADA - Obtener mascotas y vets
    # ============================================
    
    if rol == "Cliente":
        # 🔹 CLIENTE: Solo sus propias mascotas
        mascotas = []
        for m in pacientes.find({"id_user": current_user_id}):
            m["id"] = str(m["_id"])
            # 🔹 AGREGAR display_name para clientes
            m["display_name"] = f"{m.get('nombre', 'Unknown')} ({m.get('especie', 'Unknown')})"
            mascotas.append(m)
        
        # 🔹 VERIFICAR si tiene mascotas
        if not mascotas:
            messages.warning(request, "You don't have any registered pets. Please add a pet first.")
            return redirect("add_mascota")
    
    else:
        # 🔹 ADMIN/VET: Todas las mascotas
        mascotas = []
        for m in pacientes.find():
            m["id"] = str(m["_id"])
            owner = users.find_one({"_id": ObjectId(m.get("id_user"))}) if m.get("id_user") else None
            owner_name = owner.get("User", "Unknown") if owner else "Unknown"
            m["display_name"] = f"{m.get('nombre', 'Unknown')} ({m.get('especie', 'Unknown')}) - Owner: {owner_name}"
            mascotas.append(m)
    
    # Obtener veterinarios
    vets = []
    for v in veterinarios.find():
        v["id"] = str(v["_id"])
        vets.append(v)

    # ============================================
    # 🔧 SECCIÓN MODIFICADA - Procesar formulario (POST)
    # ============================================
    
    if request.method == "POST":
        id_paciente = request.POST.get("paciente")
        id_veterinario = request.POST.get("veterinario")
        fecha_str = request.POST.get("fecha")
        motivo = request.POST.get("motivo", "").strip()
        
        # Validaciones
        if not all([id_paciente, id_veterinario, fecha_str, motivo]):
            messages.error(request, "Please fill all required fields.")
            # Re-renderizar con los datos actuales
            cita["id_str"] = str(cita["_id"])
            return render(request, "appointments_form.html", {
                "cita": cita,
                "mascotas": mascotas,
                "vets": vets,
                "action": "Edit",
                "rol": rol,
                "username": username
            })
        
        # Validar que la mascota pertenezca al usuario (si es cliente)
        if rol == "Cliente":
            mascota_seleccionada = pacientes.find_one({"_id": ObjectId(id_paciente)})
            if not mascota_seleccionada or mascota_seleccionada.get("id_user") != current_user_id:
                messages.error(request, "You can only edit appointments for your own pets.")
                cita["id_str"] = str(cita["_id"])
                return render(request, "appointments_form.html", {
                    "cita": cita,
                    "mascotas": mascotas,
                    "vets": vets,
                    "action": "Edit",
                    "rol": rol,
                    "username": username
                })
        
        # Validar formato de fecha
        try:
            from datetime import datetime, timedelta
            fecha_obj = datetime.strptime(fecha_str, "%Y-%m-%dT%H:%M")
        except ValueError:
            messages.error(request, "Invalid date format.")
            cita["id_str"] = str(cita["_id"])
            return render(request, "appointments_form.html", {
                "cita": cita,
                "mascotas": mascotas,
                "vets": vets,
                "action": "Edit",
                "rol": rol,
                "username": username
            })
        
        # Validaciones de fecha
        now = datetime.now()
        minimum_time = now + timedelta(hours=1)
        
        if fecha_obj < minimum_time:
            messages.error(request, "Appointments must be scheduled at least 1 hour in advance.")
            cita["id_str"] = str(cita["_id"])
            return render(request, "appointments_form.html", {
                "cita": cita,
                "mascotas": mascotas,
                "vets": vets,
                "action": "Edit",
                "rol": rol,
                "username": username
            })
        
        # No puede ser fin de semana
        if fecha_obj.weekday() >= 5:
            messages.error(request, "Appointments are only available Monday through Friday.")
            cita["id_str"] = str(cita["_id"])
            return render(request, "appointments_form.html", {
                "cita": cita,
                "mascotas": mascotas,
                "vets": vets,
                "action": "Edit",
                "rol": rol,
                "username": username
            })
        
        # Verificar horario de oficina (8 AM - 7 PM)
        hour = fecha_obj.hour
        if hour < 8 or hour >= 19:
            messages.error(request, "Appointments must be between 8:00 AM and 7:00 PM.")
            cita["id_str"] = str(cita["_id"])
            return render(request, "appointments_form.html", {
                "cita": cita,
                "mascotas": mascotas,
                "vets": vets,
                "action": "Edit",
                "rol": rol,
                "username": username
            })
        
        # Verificar horario de almuerzo (12 PM - 2 PM)
        if 12 <= hour < 14:
            messages.error(request, "No appointments during lunch break (12:00 PM - 2:00 PM).")
            cita["id_str"] = str(cita["_id"])
            return render(request, "appointments_form.html", {
                "cita": cita,
                "mascotas": mascotas,
                "vets": vets,
                "action": "Edit",
                "rol": rol,
                "username": username
            })
        
        # Actualizar la cita
        citas.update_one({"_id": ObjectId(id)}, {"$set": {
            "id_paciente": id_paciente,
            "id_veterinario": id_veterinario,
            "fecha": fecha_obj.strftime("%Y-%m-%dT%H:%M"),
            "motivo": motivo,
        }})
        
        messages.success(request, "Appointment updated successfully.")
        return redirect("list_citas")

    # ============================================
    # Preparar datos de la cita para el formulario
    # ============================================
    
    cita["id_str"] = str(cita["_id"])
    # 🔹 Convertir los ObjectId a strings para el template
    cita["id_paciente"] = str(cita.get("id_paciente", ""))
    cita["id_veterinario"] = str(cita.get("id_veterinario", ""))

    return render(request, "appointments_form.html", {
        "cita": cita,
        "mascotas": mascotas,
        "vets": vets,
        "action": "Edit",
        "rol": rol,
        "username": username
    })



# ============================================
# PANEL DE ADMINISTRADOR - USUARIOS
# ============================================

def admin_users_list(request):
    """Lista de usuarios del sistema (solo admin)."""
    if "user" not in request.session:
        messages.warning(request, "Please log in first.")
        return redirect("login")

    rol = request.session.get("rol")
    if rol != "Administrador":
        messages.error(request, "Access denied. Administrator privileges required.")
        return redirect("index")

    # Obtener todos los usuarios
    usuarios_list = list(users.find())
    
    # Agregar ID como string para cada usuario
    for u in usuarios_list:
        u["id"] = str(u["_id"])
    
    # Calcular totales por rol
    total_usuarios = len(usuarios_list)
    total_admins = len([u for u in usuarios_list if u.get("Rol") == "Administrador"])
    total_vets = len([u for u in usuarios_list if u.get("Rol") == "Veterinario"])
    total_clients = len([u for u in usuarios_list if u.get("Rol") == "Cliente"])

    context = {
        "rol": rol,
        "username": request.session.get("user"),
        "usuarios": usuarios_list,
        "total_usuarios": total_usuarios,
        "total_admins": total_admins,
        "total_vets": total_vets,
        "total_clients": total_clients,
    }

    return render(request, "admin_users_list.html", context)


def admin_users_add(request):
    """Crea un nuevo usuario con rol específico (con Phone y Address)."""
    if request.session.get("rol") != "Administrador":
        messages.error(request, "Access denied. Administrator privileges required.")
        return redirect("index")

    if request.method == "POST":
        user_field = request.POST.get("user")
        email = request.POST.get("email")
        password = request.POST.get("password")
        phone = request.POST.get("phone", "")  # Campo nuevo - opcional
        address = request.POST.get("address", "")  # Campo nuevo - opcional
        rol = request.POST.get("rol")

        # Validar que el username no exista
        if users.find_one({"User": user_field}):
            messages.error(request, "A user with that username already exists.")
            return redirect("admin_users_add")

        # Validar que el email no exista
        if users.find_one({"Email": email}):
            messages.error(request, "A user with that email already exists.")
            return redirect("admin_users_add")

        # Crear nuevo usuario
        users.insert_one({
            "User": user_field,
            "Email": email,
            "Password": password,  # IMPORTANTE: En producción, hashea la contraseña
            "Phone": phone,
            "Address": address,
            "Rol": rol
        })
        
        messages.success(request, f"User '{user_field}' created successfully.")
        return redirect("admin_users_list")

    return render(request, "admin_users_form.html", {"action": "Add"})


def admin_users_edit(request, id):
    """Edita los datos de un usuario (ahora incluye Phone y Address)."""
    if request.session.get("rol") != "Administrador":
        messages.error(request, "Access denied. Administrator privileges required.")
        return redirect("index")

    usuario = users.find_one({"_id": ObjectId(id)})
    if not usuario:
        messages.error(request, "User not found.")
        return redirect("admin_users_list")

    if request.method == "POST":
        user_field = request.POST.get("user")
        email = request.POST.get("email")
        phone = request.POST.get("phone", "")  # Campo nuevo
        address = request.POST.get("address", "")  # Campo nuevo
        rol = request.POST.get("rol")

        # Validar que el nuevo username no esté en uso por otro usuario
        existing_user = users.find_one({"User": user_field, "_id": {"$ne": ObjectId(id)}})
        if existing_user:
            messages.error(request, "Another user already has that username.")
            return render(request, "admin_users_form.html", {
                "usuario": usuario, 
                "action": "Edit"
            })

        # Validar que el nuevo email no esté en uso por otro usuario
        existing_email = users.find_one({"Email": email, "_id": {"$ne": ObjectId(id)}})
        if existing_email:
            messages.error(request, "Another user already has that email.")
            return render(request, "admin_users_form.html", {
                "usuario": usuario, 
                "action": "Edit"
            })

        # Actualizar usuario (sin cambiar la contraseña)
        users.update_one({"_id": ObjectId(id)}, {"$set": {
            "User": user_field,
            "Email": email,
            "Phone": phone,
            "Address": address,
            "Rol": rol
        }})
        
        messages.success(request, "User updated successfully.")
        return redirect("admin_users_list")

    # Preparar datos para el template
    usuario["mongo_id"] = str(usuario["_id"])
    return render(request, "admin_users_form.html", {"usuario": usuario, "action": "Edit"})


def admin_users_reset_password(request, id):
    """Resetea la contraseña de un usuario."""
    if request.session.get("rol") != "Administrador":
        messages.error(request, "Access denied. Administrator privileges required.")
        return redirect("index")

    usuario = users.find_one({"_id": ObjectId(id)})
    if not usuario:
        messages.error(request, "User not found.")
        return redirect("admin_users_list")

    if request.method == "POST":
        new_password = request.POST.get("password")
        
        # IMPORTANTE: En producción, hashea la contraseña
        users.update_one({"_id": ObjectId(id)}, {"$set": {
            "Password": new_password
        }})
        
        messages.success(request, f"Password for '{usuario['User']}' has been reset successfully.")
        return redirect("admin_users_list")

    usuario["mongo_id"] = str(usuario["_id"])
    return render(request, "admin_users_reset.html", {"usuario": usuario})


def admin_users_delete(request, id):
    """Elimina un usuario del sistema."""
    if request.session.get("rol") != "Administrador":
        messages.error(request, "Access denied. Administrator privileges required.")
        return redirect("index")

    usuario = users.find_one({"_id": ObjectId(id)})
    if not usuario:
        messages.error(request, "User not found.")
        return redirect("admin_users_list")

    # Prevenir que el admin se elimine a sí mismo
    if str(usuario["_id"]) == request.session.get("user_id"):
        messages.error(request, "You cannot delete your own account.")
        return redirect("admin_users_list")

    users.delete_one({"_id": ObjectId(id)})
    messages.success(request, f"User '{usuario['User']}' deleted successfully.")
    return redirect("admin_users_list")



#=================================#REPORTES#=============================

def reports(request):
    """Sistema de reportes con filtros avanzados."""
    if "user" not in request.session:
        messages.warning(request, "Please log in first.")
        return redirect("login")

    username = request.session.get("user")
    rol = request.session.get("rol")
    
    # Solo Admin y Veterinarios pueden acceder a reportes
    if rol not in ["Administrador", "Veterinario"]:
        messages.error(request, "You don't have permission to access reports.")
        return redirect("index")
    
    # Obtener parámetros de filtro
    report_type = request.GET.get("type", "appointments")  # appointments, pets, users, veterinarians
    start_date = request.GET.get("start_date", "")
    end_date = request.GET.get("end_date", "")
    status = request.GET.get("status", "")
    veterinarian_id = request.GET.get("veterinarian", "")
    
    context = {
        "rol": rol,
        "username": username,
        "report_type": report_type,
        "start_date": start_date,
        "end_date": end_date,
        "status": status,
        "veterinarian_id": veterinarian_id,
    }
    
    # ========== REPORTE DE CITAS ==========
    if report_type == "appointments":
        # Construir query de filtrado
        query = {}
        
        # Filtro por fecha
        if start_date and end_date:
            query["fecha"] = {
                "$gte": start_date,
                "$lte": end_date + "T23:59"
            }
        
        # Filtro por estado
        if status:
            query["estado"] = status
        
        # Filtro por veterinario
        if veterinarian_id:
            query["id_veterinario"] = veterinarian_id
        
        # Obtener citas
        citas_data = list(citas.find(query))
        
        # Enriquecer datos
        for c in citas_data:
            c["id_str"] = str(c["_id"])
            
            # Mascota
            mascota = pacientes.find_one({"_id": ObjectId(c.get("id_paciente"))}) if c.get("id_paciente") else None
            c["mascota_nombre"] = mascota.get("nombre", "Unknown") if mascota else "Unknown"
            c["mascota_especie"] = mascota.get("especie", "N/A") if mascota else "N/A"
            
            # Dueño
            if mascota:
                owner = users.find_one({"_id": ObjectId(mascota.get("id_user"))}) if mascota.get("id_user") else None
                c["owner_name"] = owner.get("User", "Unknown") if owner else "Unknown"
            else:
                c["owner_name"] = "Unknown"
            
            # Veterinario
            vet = veterinarios.find_one({"_id": ObjectId(c.get("id_veterinario"))}) if c.get("id_veterinario") else None
            c["veterinario_nombre"] = vet.get("nombre", "Unknown") if vet else "Unknown"
            c["veterinario_especialidad"] = vet.get("especialidad", "N/A") if vet else "N/A"
            
            # Formatear fecha
            try:
                fecha_dt = datetime.strptime(c.get("fecha", ""), "%Y-%m-%dT%H:%M")
                c["fecha_formatted"] = fecha_dt.strftime("%Y-%m-%d")
                c["hora_formatted"] = fecha_dt.strftime("%H:%M")
            except:
                c["fecha_formatted"] = "N/A"
                c["hora_formatted"] = "N/A"
        
        # Estadísticas del reporte
        total_citas = len(citas_data)
        total_pendientes = len([c for c in citas_data if c.get("estado") == "Pendiente"])
        total_completadas = len([c for c in citas_data if c.get("estado") == "Completada"])
        total_canceladas = len([c for c in citas_data if c.get("estado") == "Cancelada"])
        
        context.update({
            "citas_data": citas_data,
            "total_citas": total_citas,
            "total_pendientes": total_pendientes,
            "total_completadas": total_completadas,
            "total_canceladas": total_canceladas,
        })
    
    # ========== REPORTE DE MASCOTAS ==========
    elif report_type == "pets":
        mascotas_data = list(pacientes.find())
        
        # Enriquecer con dueño y número de citas
        for m in mascotas_data:
            m["id_str"] = str(m["_id"])
            
            # Dueño
            owner = users.find_one({"_id": ObjectId(m.get("id_user"))}) if m.get("id_user") else None
            m["owner_name"] = owner.get("User", "Unknown") if owner else "Unknown"
            m["owner_email"] = owner.get("Email", "N/A") if owner else "N/A"
            
            # Número de citas
            m["total_citas"] = citas.count_documents({"id_paciente": str(m["_id"])})
        
        # Estadísticas
        total_mascotas = len(mascotas_data)
        especies_counter = {}
        for m in mascotas_data:
            especie = m.get("especie", "Unknown")
            especies_counter[especie] = especies_counter.get(especie, 0) + 1
        
        context.update({
            "mascotas_data": mascotas_data,
            "total_mascotas": total_mascotas,
            "especies_counter": especies_counter,
        })
    
    # ========== REPORTE DE VETERINARIOS ==========
    elif report_type == "veterinarians":
        vets_data = list(veterinarios.find())
        
        # Enriquecer con estadísticas
        for v in vets_data:
            v["id_str"] = str(v["_id"])
            
            # Contar citas
            v["total_citas"] = citas.count_documents({"id_veterinario": str(v["_id"])})
            v["citas_pendientes"] = citas.count_documents({
                "id_veterinario": str(v["_id"]),
                "estado": "Pendiente"
            })
            v["citas_completadas"] = citas.count_documents({
                "id_veterinario": str(v["_id"]),
                "estado": "Completada"
            })
        
        # Ordenar por número de citas
        vets_data = sorted(vets_data, key=lambda x: x["total_citas"], reverse=True)
        
        total_veterinarios = len(vets_data)
        total_citas_all = sum([v["total_citas"] for v in vets_data])
        
        context.update({
            "vets_data": vets_data,
            "total_veterinarios": total_veterinarios,
            "total_citas_all": total_citas_all,
        })
    
    # ========== REPORTE DE USUARIOS ==========
    elif report_type == "users":
        if rol != "Administrador":
            messages.error(request, "Only administrators can view user reports.")
            return redirect("index")
        
        users_data = list(users.find())
        
        # Enriquecer con estadísticas
        for u in users_data:
            u["id_str"] = str(u["_id"])
            
            # Si es cliente, contar mascotas y citas
            if u.get("Rol") == "Cliente":
                u["total_mascotas"] = pacientes.count_documents({"id_user": str(u["_id"])})
                
                # Citas de sus mascotas
                mascotas_ids = [str(m["_id"]) for m in pacientes.find({"id_user": str(u["_id"])})]
                u["total_citas"] = citas.count_documents({"id_paciente": {"$in": mascotas_ids}})
            else:
                u["total_mascotas"] = 0
                u["total_citas"] = 0
        
        # Estadísticas por rol
        total_users = len(users_data)
        total_clientes = len([u for u in users_data if u.get("Rol") == "Cliente"])
        total_veterinarios = len([u for u in users_data if u.get("Rol") == "Veterinario"])
        total_admins = len([u for u in users_data if u.get("Rol") == "Administrador"])
        
        context.update({
            "users_data": users_data,
            "total_users": total_users,
            "total_clientes": total_clientes,
            "total_veterinarios": total_veterinarios,
            "total_admins": total_admins,
        })
    
    # Obtener lista de veterinarios para el filtro
    all_vets = []
    for v in veterinarios.find():
        all_vets.append({
            "id": str(v["_id"]),
            "nombre": v.get("nombre", "Unknown"),
            "especialidad": v.get("especialidad", "N/A")
        })
    
    context["all_vets"] = all_vets
    
    return render(request, "reports.html", context)



def edit_profile(request):
    """Vista para editar el perfil del usuario."""
    
    # Verificar si el usuario está logueado
    if "user" not in request.session:
        messages.warning(request, "Please log in to edit your profile.")
        return redirect("login")
    
    username = request.session.get("user")
    rol = request.session.get("rol")
    
    # Buscar el usuario en la base de datos
    user = users.find_one({"User": username})
    
    if not user:
        messages.error(request, "User not found.")
        return redirect("index")
    
    # Si es veterinario, obtener también sus datos de veterinario
    vet_data = None
    if rol == "Veterinario":
        vet_data = veterinarios.find_one({"id_user": str(user["_id"])})
    
    if request.method == "POST":
        # Obtener datos del formulario
        email = request.POST.get("email", "").strip()
        password_actual = request.POST.get("password_actual", "").strip()
        password_nueva = request.POST.get("password_nueva", "").strip()
        password_confirmar = request.POST.get("password_confirmar", "").strip()
        
        # Datos de veterinario (si aplica)
        especialidad = request.POST.get("especialidad", "").strip()
        telefono = request.POST.get("telefono", "").strip()
        
        # Validaciones
        if not email:
            messages.error(request, "Email is required.")
            return redirect("edit_profile")
        
        # Validar email único
        existing_user = users.find_one({"Email": email, "_id": {"$ne": user["_id"]}})
        if existing_user:
            messages.error(request, "This email is already in use by another user.")
            return redirect("edit_profile")
        
        # Actualizar datos básicos
        update_data = {
            "Email": email
        }
        
        # Si quiere cambiar la contraseña
        if password_nueva:
            # Verificar contraseña actual
            if password_actual != user.get("Password", ""):
                messages.error(request, "Current password is incorrect.")
                return redirect("edit_profile")
            
            # Verificar que las nuevas contraseñas coincidan
            if password_nueva != password_confirmar:
                messages.error(request, "New passwords do not match.")
                return redirect("edit_profile")
            
            # Validar longitud mínima
            if len(password_nueva) < 6:
                messages.error(request, "Password must be at least 6 characters long.")
                return redirect("edit_profile")
            
            update_data["Password"] = password_nueva
        
        # Actualizar usuario
        users.update_one(
            {"_id": user["_id"]},
            {"$set": update_data}
        )
        
        # Si es veterinario, actualizar sus datos también
        if rol == "Veterinario" and vet_data:
            vet_update = {}
            
            if especialidad:
                vet_update["especialidad"] = especialidad
            
            if telefono:
                vet_update["telefono"] = telefono
            
            if vet_update:
                veterinarios.update_one(
                    {"_id": vet_data["_id"]},
                    {"$set": vet_update}
                )
        
        messages.success(request, "Profile updated successfully!")
        return redirect("edit_profile")
    
    # GET request - mostrar formulario
    return render(request, "edit_profile.html", {
        "username": username,
        "rol": rol,
        "user": user,
        "vet_data": vet_data
    })
