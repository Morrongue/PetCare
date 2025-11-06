from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from .models import users, pacientes, veterinarios, citas, historia_clinica
from collections import Counter
from bson import ObjectId
from datetime import datetime, timedelta
from datetime import time as dt_time 
import os
import time 
import base64

ROL_FIELD = "Rol"  


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
        
        # ✅ CAMBIO: Total de veterinarios de USERS
        total_veterinarios = users.count_documents({"Rol": "Veterinario"})
        
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
        
        # ✅ CAMBIO: Top 5 veterinarios de USERS con más citas
        todas_citas = list(citas.find({}, {"id_veterinario": 1}))
        vet_counter = Counter([c.get("id_veterinario") for c in todas_citas if c.get("id_veterinario")])
        top_vets = []
        for vet_id, count in vet_counter.most_common(5):
            vet = users.find_one({
                "_id": ObjectId(vet_id),
                "Rol": "Veterinario"
            })
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
        # ✅ CAMBIO: Citas del veterinario actual, no todas
        total_citas = citas.count_documents({"id_veterinario": user_id})
        citas_pendientes = citas.count_documents({
            "id_veterinario": user_id,
            "estado": "Pendiente"
        })
        citas_completadas = citas.count_documents({
            "id_veterinario": user_id,
            "estado": "Completada"
        })
        
        # Citas de hoy del veterinario
        hoy = datetime.now().strftime("%Y-%m-%d")
        citas_hoy_list = list(citas.find({
            "id_veterinario": user_id,
            "fecha": {"$regex": f"^{hoy}"}
        }))
        
        # Enriquecer citas de hoy con info de mascota y veterinario
        for c in citas_hoy_list:
            mascota = pacientes.find_one({"_id": ObjectId(c.get("id_paciente"))}) if c.get("id_paciente") else None
            # ✅ CAMBIO: Buscar vet en USERS
            vet = users.find_one({
                "_id": ObjectId(c.get("id_veterinario")),
                "Rol": "Veterinario"
            }) if c.get("id_veterinario") else None
            
            c["mascota_nombre"] = mascota.get("nombre", "Unknown") if mascota else "Unknown"
            c["veterinario_nombre"] = vet.get("nombre", "Unknown") if vet else "Unknown"
            
            try:
                fecha_cita = datetime.strptime(c.get("fecha", ""), "%Y-%m-%dT%H:%M")
                c["hora"] = fecha_cita.strftime("%H:%M")
            except:
                c["hora"] = "N/A"
        
        # Total de mascotas en el sistema
        total_mascotas = pacientes.count_documents({})
        
        # ✅ CAMBIO: Próximas 5 citas del veterinario
        todas_citas_futuras = list(citas.find({
            "id_veterinario": user_id,
            "fecha": {"$gte": datetime.now().strftime("%Y-%m-%dT%H:%M")}
        }).sort("fecha", 1).limit(5))
        
        proximas_citas = []
        for c in todas_citas_futuras:
            mascota = pacientes.find_one({"_id": ObjectId(c.get("id_paciente"))})
            # ✅ CAMBIO: Buscar vet en USERS
            vet = users.find_one({
                "_id": ObjectId(c.get("id_veterinario")),
                "Rol": "Veterinario"
            })
            
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
                    # ✅ CAMBIO: Buscar vet en USERS
                    vet = users.find_one({
                        "_id": ObjectId(c.get("id_veterinario")),
                        "Rol": "Veterinario"
                    })
                    
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
        messages.warning(request, "Please log in first.")
        return redirect("login")

    rol = request.session.get("rol")
    username = request.session.get("user")

    if rol == "Administrador":
        data = list(pacientes.find())
    else:
        user = users.find_one({"User": username})
        data = list(pacientes.find({"id_user": str(user["_id"])}))

    # Convertir ObjectId a str
    for p in data:
        p["id"] = str(p["_id"])

    return render(request, "patients_list.html", {
        "patients": data,
        "rol": rol,
        "username": username
    })


def add_paciente(request):
    """Agrega un nuevo paciente con foto de perfil."""
    if "user" not in request.session:
        messages.warning(request, "Please log in first.")
        return redirect("login")

    if request.method == "POST":
        nombre = request.POST.get("nombre", "").strip()
        especie = request.POST.get("especie", "").strip()
        raza = request.POST.get("raza", "").strip()
        
        # Validar campos requeridos
        if not nombre or not especie or not raza:
            messages.error(request, "Name, species, and breed are required.")
            return redirect("add_paciente")
        
        user = users.find_one({"User": request.session["user"]})
        
        # Preparar datos del paciente
        paciente_data = {
            "nombre": nombre,
            "especie": especie,
            "raza": raza,
            "id_user": str(user["_id"]),
            "profile_picture": None
        }

        # ===================================================
        # MANEJO DE FOTO DE PERFIL - BASE64
        # ===================================================
        
        if 'profile_picture' in request.FILES:
            profile_picture = request.FILES['profile_picture']
            
            # Validar que tenga contenido
            if profile_picture.size == 0:
                messages.error(request, "The uploaded file is empty.")
                return redirect("add_paciente")
            
            # Validar tipo de archivo
            allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
            if profile_picture.content_type not in allowed_types:
                messages.error(request, "Invalid file type. Only JPG, PNG, GIF, and WEBP are allowed.")
                return redirect("add_paciente")
            
            # Validar tamaño (5MB máximo)
            if profile_picture.size > 5 * 1024 * 1024:
                messages.error(request, "File size must be less than 5MB.")
                return redirect("add_paciente")
            
            try:
                # Leer archivo y convertir a Base64
                file_content = profile_picture.read()
                base64_image = base64.b64encode(file_content).decode('utf-8')
                
                # Crear Data URI
                data_uri = f"data:{profile_picture.content_type};base64,{base64_image}"
                
                # Agregar a los datos
                paciente_data["profile_picture"] = data_uri
                
                print(f"✅ Foto guardada para {nombre}: {len(base64_image)} caracteres")
                
            except Exception as e:
                print(f"❌ Error procesando imagen: {str(e)}")
                messages.error(request, f"Error processing image: {str(e)}")
                return redirect("add_paciente")

        # Insertar paciente
        result = pacientes.insert_one(paciente_data)
        print(f"✅ Paciente insertado con ID: {result.inserted_id}")
        
        messages.success(request, f"{nombre} added successfully to your pets.")
        return redirect("list_pacientes")

    # GET request
    return render(request, "patients_form.html", {
        "action": "Add",
        "paciente": {},
        "rol": request.session.get("rol"),
        "username": request.session.get("user")
    })


def edit_paciente(request, id):
    """Edita los datos de un paciente con foto de perfil."""
    if "user" not in request.session:
        messages.warning(request, "Please log in first.")
        return redirect("login")
    
    paciente = pacientes.find_one({"_id": ObjectId(id)})

    if not paciente:
        messages.error(request, "Pet not found.")
        return redirect("list_pacientes")

    if request.method == "POST":
        nombre = request.POST.get("nombre", "").strip()
        especie = request.POST.get("especie", "").strip()
        raza = request.POST.get("raza", "").strip()
        remove_profile_picture = request.POST.get("remove_profile_picture", "") == "true"
        
        # Validar campos requeridos
        if not nombre or not especie or not raza:
            messages.error(request, "Name, species, and breed are required.")
            return render(request, "patients_form.html", {
                "action": "Edit",
                "paciente": paciente,
                "rol": request.session.get("rol"),
                "username": request.session.get("user")
            })
        
        # Preparar datos de actualización
        update_data = {
            "nombre": nombre,
            "especie": especie,
            "raza": raza
        }

        # ===================================================
        # MANEJO DE FOTO DE PERFIL
        # ===================================================
        
        # Opción 1: Eliminar foto actual
        if remove_profile_picture:
            update_data["profile_picture"] = None
            print(f"🗑️ Eliminando foto de {nombre}")
        
        # Opción 2: Subir nueva foto
        if 'profile_picture' in request.FILES and not remove_profile_picture:
            profile_picture = request.FILES['profile_picture']
            
            # Validar que tenga contenido
            if profile_picture.size == 0:
                messages.error(request, "The uploaded file is empty.")
                return render(request, "patients_form.html", {
                    "action": "Edit",
                    "paciente": paciente,
                    "rol": request.session.get("rol"),
                    "username": request.session.get("user")
                })
            
            # Validar tipo de archivo
            allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
            if profile_picture.content_type not in allowed_types:
                messages.error(request, "Invalid file type. Only JPG, PNG, GIF, and WEBP are allowed.")
                return render(request, "patients_form.html", {
                    "action": "Edit",
                    "paciente": paciente,
                    "rol": request.session.get("rol"),
                    "username": request.session.get("user")
                })
            
            # Validar tamaño (5MB máximo)
            if profile_picture.size > 5 * 1024 * 1024:
                messages.error(request, "File size must be less than 5MB.")
                return render(request, "patients_form.html", {
                    "action": "Edit",
                    "paciente": paciente,
                    "rol": request.session.get("rol"),
                    "username": request.session.get("user")
                })
            
            try:
                # Leer archivo y convertir a Base64
                file_content = profile_picture.read()
                base64_image = base64.b64encode(file_content).decode('utf-8')
                
                # Crear Data URI
                data_uri = f"data:{profile_picture.content_type};base64,{base64_image}"
                
                # Agregar a los datos de actualización
                update_data["profile_picture"] = data_uri
                
                print(f"✅ Nueva foto para {nombre}: {len(base64_image)} caracteres")
                
            except Exception as e:
                print(f"❌ Error procesando imagen: {str(e)}")
                messages.error(request, f"Error processing image: {str(e)}")
                return render(request, "patients_form.html", {
                    "action": "Edit",
                    "paciente": paciente,
                    "rol": request.session.get("rol"),
                    "username": request.session.get("user")
                })

        # Actualizar paciente
        pacientes.update_one({"_id": ObjectId(id)}, {"$set": update_data})
        print(f"✅ Paciente {nombre} actualizado")
        
        messages.success(request, f"{nombre}'s information updated successfully.")
        return redirect("list_pacientes")

    # GET request
    return render(request, "patients_form.html", {
        "action": "Edit",
        "paciente": paciente,
        "rol": request.session.get("rol"),
        "username": request.session.get("user")
    })


def delete_paciente(request, id):
    """Elimina un paciente."""
    if "user" not in request.session:
        messages.warning(request, "Please log in first.")
        return redirect("login")
    
    paciente = pacientes.find_one({"_id": ObjectId(id)})
    
    if not paciente:
        messages.error(request, "Pet not found.")
        return redirect("list_pacientes")
    
    # Opcional: Verificar si tiene citas pendientes
    # from .conexion import citas
    # citas_pendientes = citas.count_documents({
    #     "paciente_id": str(id),
    #     "estado": "Pendiente"
    # })
    # if citas_pendientes > 0:
    #     messages.error(request, f"Cannot delete {paciente['nombre']}. There are {citas_pendientes} pending appointments.")
    #     return redirect("list_pacientes")
    
    pacientes.delete_one({"_id": ObjectId(id)})
    print(f"🗑️ Paciente {paciente['nombre']} eliminado")
    
    messages.info(request, f"{paciente['nombre']} has been removed from your pets.")
    return redirect("list_pacientes")


# ------------------ CRUD de Veterinarios ------------------


def list_veterinarios(request):
    """Lista todos los veterinarios (usuarios con rol Veterinario)."""
    if "user" not in request.session:
        messages.warning(request, "Please log in first.")
        return redirect("login")

    rol = request.session.get("rol")
    if rol != "Administrador":
        messages.error(request, "Access denied. Administrator privileges required.")
        return redirect("index")

    # Obtener todos los usuarios con rol "Veterinario"
    data = list(users.find({"Rol": "Veterinario"}))
    for v in data:
        v["id"] = str(v["_id"])

    context = {
        "vets": data,
        "rol": rol,
        "username": request.session.get("user")
    }

    return render(request, "vets_list.html", context)


def add_veterinario(request):
    """Agrega un nuevo veterinario (usuario con rol Veterinario)."""
    if "user" not in request.session:
        messages.warning(request, "Please log in first.")
        return redirect("login")
    
    if request.session.get("rol") != "Administrador":
        messages.error(request, "Only administrators can add veterinarians.")
        return redirect("index")

    if request.method == "POST":
        # Datos de usuario
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "").strip()
        
        # Datos de veterinario
        nombre = request.POST.get("nombre", "").strip()
        especialidad = request.POST.get("especialidad", "").strip()
        phone = request.POST.get("phone", "").strip()
        license = request.POST.get("license", "").strip()

        # Validar campos requeridos
        if not username or not email or not password or not nombre or not especialidad:
            messages.error(request, "Username, email, password, name and specialty are required.")
            return redirect("add_veterinario")
        
        # Validar longitud de contraseña
        if len(password) < 6:
            messages.error(request, "Password must be at least 6 characters long.")
            return redirect("add_veterinario")

        # Validar username único
        if users.find_one({"User": username}):
            messages.error(request, "Username already exists.")
            return redirect("add_veterinario")
        
        # Validar email único
        if users.find_one({"Email": email}):
            messages.error(request, "Email already in use.")
            return redirect("add_veterinario")

        # Validar licencia única (si se proporciona)
        if license and users.find_one({"license": license}):
            messages.error(request, "A veterinarian with this license number already exists.")
            return redirect("add_veterinario")

        # Preparar datos del usuario veterinario
        vet_data = {
            "User": username,
            "Email": email,
            "Password": password,  # En producción deberías hashear esto
            "Rol": "Veterinario",
            "nombre": nombre,
            "especialidad": especialidad,
            "phone": phone,
            "license": license,
            "profile_picture": None
        }

        # ===================================================
        # MANEJO DE FOTO DE PERFIL - BASE64
        # ===================================================
        
        if 'profile_picture' in request.FILES:
            profile_picture = request.FILES['profile_picture']
            
            # Validar que tenga contenido
            if profile_picture.size == 0:
                messages.error(request, "The uploaded file is empty.")
                return redirect("add_veterinario")
            
            # Validar tipo de archivo
            allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
            if profile_picture.content_type not in allowed_types:
                messages.error(request, "Invalid file type. Only JPG, PNG, GIF, and WEBP are allowed.")
                return redirect("add_veterinario")
            
            # Validar tamaño (5MB máximo)
            if profile_picture.size > 5 * 1024 * 1024:
                messages.error(request, "File size must be less than 5MB.")
                return redirect("add_veterinario")
            
            try:
                # Leer archivo y convertir a Base64
                file_content = profile_picture.read()
                base64_image = base64.b64encode(file_content).decode('utf-8')
                
                # Crear Data URI
                data_uri = f"data:{profile_picture.content_type};base64,{base64_image}"
                
                # Agregar a los datos
                vet_data["profile_picture"] = data_uri
                
                print(f"✅ Foto guardada para Dr. {nombre}: {len(base64_image)} caracteres")
                
            except Exception as e:
                print(f"❌ Error procesando imagen: {str(e)}")
                messages.error(request, f"Error processing image: {str(e)}")
                return redirect("add_veterinario")

        # Insertar veterinario en users
        result = users.insert_one(vet_data)
        print(f"✅ Veterinario insertado con ID: {result.inserted_id}")
        
        messages.success(request, f"Dr. {nombre} added successfully with username: {username}")
        return redirect("list_veterinarios")

    # GET request
    context = {
        "action": "Add",
        "vet": {},
        "rol": request.session.get("rol"),
        "username": request.session.get("user")
    }
    return render(request, "vets_form.html", context)


def edit_veterinario(request, id):
    """Edita un veterinario (usuario con rol Veterinario)."""
    if "user" not in request.session:
        messages.warning(request, "Please log in first.")
        return redirect("login")
    
    if request.session.get("rol") != "Administrador":
        messages.error(request, "Only administrators can edit veterinarians.")
        return redirect("index")

    vet = users.find_one({"_id": ObjectId(id), "Rol": "Veterinario"})
    if not vet:
        messages.error(request, "Veterinarian not found.")
        return redirect("list_veterinarios")

    if request.method == "POST":
        # Datos de usuario
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password_nueva = request.POST.get("password", "").strip()
        
        # Datos de veterinario
        nombre = request.POST.get("nombre", "").strip()
        especialidad = request.POST.get("especialidad", "").strip()
        phone = request.POST.get("phone", "").strip()
        license = request.POST.get("license", "").strip()
        remove_profile_picture = request.POST.get("remove_profile_picture", "") == "true"

        # Validar campos requeridos
        if not username or not email or not nombre or not especialidad:
            messages.error(request, "Username, email, name and specialty are required.")
            context = {
                "action": "Edit",
                "vet": vet,
                "rol": request.session.get("rol"),
                "username": request.session.get("user")
            }
            return render(request, "vets_form.html", context)

        # Validar username único (excepto el actual)
        existing_user = users.find_one({
            "User": username,
            "_id": {"$ne": ObjectId(id)}
        })
        if existing_user:
            messages.error(request, "Username already exists.")
            context = {
                "action": "Edit",
                "vet": vet,
                "rol": request.session.get("rol"),
                "username": request.session.get("user")
            }
            return render(request, "vets_form.html", context)

        # Validar email único (excepto el actual)
        existing_email = users.find_one({
            "Email": email,
            "_id": {"$ne": ObjectId(id)}
        })
        if existing_email:
            messages.error(request, "Email already in use.")
            context = {
                "action": "Edit",
                "vet": vet,
                "rol": request.session.get("rol"),
                "username": request.session.get("user")
            }
            return render(request, "vets_form.html", context)

        # Validar licencia única (excepto la actual)
        if license:
            existing_license = users.find_one({
                "license": license,
                "_id": {"$ne": ObjectId(id)}
            })
            if existing_license:
                messages.error(request, "Another veterinarian already has this license number.")
                context = {
                    "action": "Edit",
                    "vet": vet,
                    "rol": request.session.get("rol"),
                    "username": request.session.get("user")
                }
                return render(request, "vets_form.html", context)

        # Preparar datos de actualización
        update_data = {
            "User": username,
            "Email": email,
            "nombre": nombre,
            "especialidad": especialidad,
            "phone": phone,
            "license": license
        }
        
        # Actualizar contraseña solo si se proporciona
        if password_nueva:
            if len(password_nueva) < 6:
                messages.error(request, "Password must be at least 6 characters long.")
                context = {
                    "action": "Edit",
                    "vet": vet,
                    "rol": request.session.get("rol"),
                    "username": request.session.get("user")
                }
                return render(request, "vets_form.html", context)
            update_data["Password"] = password_nueva

        # ===================================================
        # MANEJO DE FOTO DE PERFIL
        # ===================================================
        
        # Opción 1: Eliminar foto actual
        if remove_profile_picture:
            update_data["profile_picture"] = None
            print(f"🗑️ Eliminando foto de Dr. {nombre}")
        
        # Opción 2: Subir nueva foto
        if 'profile_picture' in request.FILES and not remove_profile_picture:
            profile_picture = request.FILES['profile_picture']
            
            # Validar que tenga contenido
            if profile_picture.size == 0:
                messages.error(request, "The uploaded file is empty.")
                context = {
                    "action": "Edit",
                    "vet": vet,
                    "rol": request.session.get("rol"),
                    "username": request.session.get("user")
                }
                return render(request, "vets_form.html", context)
            
            # Validar tipo de archivo
            allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
            if profile_picture.content_type not in allowed_types:
                messages.error(request, "Invalid file type. Only JPG, PNG, GIF, and WEBP are allowed.")
                context = {
                    "action": "Edit",
                    "vet": vet,
                    "rol": request.session.get("rol"),
                    "username": request.session.get("user")
                }
                return render(request, "vets_form.html", context)
            
            # Validar tamaño (5MB máximo)
            if profile_picture.size > 5 * 1024 * 1024:
                messages.error(request, "File size must be less than 5MB.")
                context = {
                    "action": "Edit",
                    "vet": vet,
                    "rol": request.session.get("rol"),
                    "username": request.session.get("user")
                }
                return render(request, "vets_form.html", context)
            
            try:
                # Leer archivo y convertir a Base64
                file_content = profile_picture.read()
                base64_image = base64.b64encode(file_content).decode('utf-8')
                
                # Crear Data URI
                data_uri = f"data:{profile_picture.content_type};base64,{base64_image}"
                
                # Agregar a los datos de actualización
                update_data["profile_picture"] = data_uri
                
                print(f"✅ Nueva foto para Dr. {nombre}: {len(base64_image)} caracteres")
                
            except Exception as e:
                print(f"❌ Error procesando imagen: {str(e)}")
                messages.error(request, f"Error processing image: {str(e)}")
                context = {
                    "action": "Edit",
                    "vet": vet,
                    "rol": request.session.get("rol"),
                    "username": request.session.get("user")
                }
                return render(request, "vets_form.html", context)

        # Actualizar veterinario
        users.update_one({"_id": ObjectId(id)}, {"$set": update_data})
        print(f"✅ Veterinario Dr. {nombre} actualizado")
        
        messages.success(request, f"Dr. {nombre} updated successfully.")
        return redirect("list_veterinarios")

    # GET request
    context = {
        "action": "Edit",
        "vet": vet,
        "rol": request.session.get("rol"),
        "username": request.session.get("user")
    }
    return render(request, "vets_form.html", context)


def delete_veterinario(request, id):
    """Elimina un veterinario (usuario con rol Veterinario)."""
    if "user" not in request.session:
        messages.warning(request, "Please log in first.")
        return redirect("login")
    
    if request.session.get("rol") != "Administrador":
        messages.error(request, "Only administrators can delete veterinarians.")
        return redirect("index")

    vet = users.find_one({"_id": ObjectId(id), "Rol": "Veterinario"})
    if not vet:
        messages.error(request, "Veterinarian not found.")
        return redirect("list_veterinarios")

    # Opcional: Verificar si tiene citas pendientes
    # from .conexion import citas
    # citas_pendientes = citas.count_documents({
    #     "veterinario_id": str(id),
    #     "estado": "Pendiente"
    # })
    # if citas_pendientes > 0:
    #     messages.error(request, f"Cannot delete Dr. {vet.get('nombre', vet.get('User'))}. There are {citas_pendientes} pending appointments.")
    #     return redirect("list_veterinarios")

    users.delete_one({"_id": ObjectId(id)})
    print(f"🗑️ Veterinario Dr. {vet.get('nombre', vet.get('User'))} eliminado")
    
    messages.info(request, f"Dr. {vet.get('nombre', vet.get('User'))} has been deleted from the system.")
    return redirect("list_veterinarios")





# -------------------- FUNCIÓN AUXILIAR: ACTUALIZAR ESTADOS AUTOMÁTICAMENTE --------------------
def actualizar_estados_citas_automaticamente():
    """
    Actualiza automáticamente el estado de las citas a 'Completada' 
    cuando ha pasado el tiempo suficiente desde su inicio.
    """
    try:
        ahora = datetime.now()
        citas_pendientes = citas.find({"estado": "Pendiente"})
        citas_actualizadas = 0
        
        for cita in citas_pendientes:
            try:
                fecha_inicio = datetime.strptime(cita.get("fecha", ""), "%Y-%m-%dT%H:%M")
                duracion = cita.get("duracion", 1)
                fecha_completado = fecha_inicio + timedelta(hours=duracion)
                
                if ahora >= fecha_completado:
                    citas.update_one(
                        {"_id": cita["_id"]},
                        {"$set": {"estado": "Completada"}}
                    )
                    citas_actualizadas += 1
            except Exception as e:
                print(f"Error procesando cita {cita.get('_id')}: {e}")
                continue
        
        if citas_actualizadas > 0:
            print(f"✅ {citas_actualizadas} citas actualizadas a 'Completada'")
    except Exception as e:
        print(f"❌ Error al actualizar estados: {e}")


# -------------------- LISTAR CITAS --------------------
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

    # Obtener current_user
    current_user = users.find_one({"User": username})
    if not current_user:
        messages.error(request, "User not found.")
        return redirect("index")
    
    current_user_id = str(current_user["_id"])

    # Obtener citas según rol
    if rol == "Administrador":
        data = list(citas.find())
    elif rol == "Veterinario":
        # ✅ Filtrar por veterinario (user_id)
        data = list(citas.find({"id_veterinario": current_user_id}))
    else:
        # Cliente: Solo citas de sus mascotas
        mascotas = list(pacientes.find({"id_user": current_user_id}))
        mascota_ids = [str(m["_id"]) for m in mascotas]
        data = list(citas.find({"id_paciente": {"$in": mascota_ids}}))

    # Ordenar por fecha descendente
    data.sort(key=lambda x: x.get("fecha", "1970-01-01T00:00"), reverse=True)

    # Calcular contadores
    total_citas = len(data)
    pendientes = len([c for c in data if c.get("estado") == "Pendiente"])
    completadas = len([c for c in data if c.get("estado") == "Completada"])
    canceladas = len([c for c in data if c.get("estado") == "Cancelada"])

    # Enriquecer datos
    for c in data:
        c["id"] = str(c.get("_id", ""))
        c["id_str"] = str(c.get("_id", ""))
        c["fecha_original"] = c.get("fecha", "")

        # Buscar datos de la mascota
        if "id_paciente" in c:
            mascota = pacientes.find_one({"_id": ObjectId(c["id_paciente"])})
            if mascota:
                c["mascota_nombre"] = mascota.get("nombre", "Unknown Pet")
                c["mascota_especie"] = mascota.get("especie", "Unknown")
                c["mascota_owner_id"] = mascota.get("id_user")

        # ✅ Buscar veterinario en USERS
        if "id_veterinario" in c:
            vet = users.find_one({
                "_id": ObjectId(c["id_veterinario"]),
                "Rol": "Veterinario"
            })
            if vet:
                c["veterinario_nombre"] = vet.get("nombre", "Unknown Vet")
            else:
                c["veterinario_nombre"] = "Unknown Vet"

        # Separar fecha y hora
        try:
            fecha_cita = datetime.strptime(c.get("fecha", ""), "%Y-%m-%dT%H:%M")
            c["fecha"] = fecha_cita.strftime("%Y-%m-%d")
            c["hora"] = fecha_cita.strftime("%H:%M")
        except:
            c["fecha"] = c.get("fecha", "")
            c["hora"] = ""

        # Sistema de permisos
        c["puede_editar"] = False
        c["puede_cancelar"] = False
        c["puede_agregar_observacion"] = False
        
        if rol == "Administrador":
            c["puede_editar"] = True
            c["puede_cancelar"] = True
        elif rol == "Cliente":
            if c.get("mascota_owner_id") == current_user_id and c.get("estado") == "Pendiente":
                c["puede_editar"] = True
                c["puede_cancelar"] = True
        elif rol == "Veterinario":
            if c.get("id_veterinario") == current_user_id:
                if c.get("estado") == "Pendiente":
                    c["puede_editar"] = True
                # ✅ El veterinario puede agregar observaciones en citas asignadas (Pendiente o Completada)
                if c.get("estado") in ["Pendiente", "Completada"]:
                    c["puede_agregar_observacion"] = True

        # Formatear fecha de observación si existe
        if c.get("fecha_observacion"):
            try:
                fecha_obs = datetime.strptime(c["fecha_observacion"], "%Y-%m-%dT%H:%M:%S")
                c["fecha_observacion"] = fecha_obs.strftime("%B %d, %Y at %I:%M %p")
            except:
                pass

    return render(request, "appointments_list.html", {
        "citas": data,
        "rol": rol,
        "username": username,
        "total_citas": total_citas,
        "pendientes": pendientes,
        "completadas": completadas,
        "canceladas": canceladas
    })


# -------------------- AÑADIR OBSERVACIÓN --------------------
def add_observation(request, id):
    """Permite a un veterinario añadir observaciones a una cita."""
    if "user" not in request.session:
        messages.warning(request, "Please log in first.")
        return redirect("login")
    
    rol = request.session.get("rol")
    username = request.session.get("user")
    
    # Solo veterinarios pueden añadir observaciones
    if rol != "Veterinario":
        messages.error(request, "Only veterinarians can add observations.")
        return redirect("list_citas")
    
    # Buscar la cita
    cita = citas.find_one({"_id": ObjectId(id)})
    if not cita:
        messages.error(request, "Appointment not found.")
        return redirect("list_citas")
    
    # Verificar que el veterinario esté asignado a esta cita
    current_user = users.find_one({"User": username})
    if not current_user:
        messages.error(request, "User not found.")
        return redirect("list_citas")
    
    current_user_id = str(current_user["_id"])
    
    if cita.get("id_veterinario") != current_user_id:
        messages.error(request, "You can only add observations to your own appointments.")
        return redirect("list_citas")
    
    # Solo se pueden agregar observaciones a citas Pendientes o Completadas
    if cita.get("estado") not in ["Pendiente", "Completada"]:
        messages.error(request, "Observations can only be added to pending or completed appointments.")
        return redirect("list_citas")
    
    if request.method == "POST":
        observacion = request.POST.get("observacion", "").strip()
        
        if not observacion:
            messages.error(request, "Observation cannot be empty.")
            return redirect("list_citas")
        
        # Actualizar la cita con la observación
        citas.update_one(
            {"_id": ObjectId(id)},
            {"$set": {
                "observacion": observacion,
                "fecha_observacion": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
                "veterinario_observacion": current_user_id
            }}
        )
        
        messages.success(request, "Observation added successfully.")
        return redirect("list_citas")
    
    # Si no es POST, redirigir a la lista
    return redirect("list_citas")


# -------------------- CANCELAR CITA --------------------
def cancel_cita(request, id):
    """Cancela una cita cambiando su estado a 'Cancelada'."""
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
    tiene_permiso = False
    
    if rol == "Administrador":
        tiene_permiso = True
    elif rol == "Cliente":
        mascota = pacientes.find_one({"_id": ObjectId(cita.get("id_paciente"))})
        if mascota and mascota.get("id_user") == current_user_id:
            tiene_permiso = True
    elif rol == "Veterinario":
        messages.error(request, "Veterinarians cannot cancel appointments. Please contact the pet owner or an administrator.")
        return redirect("list_citas")
    
    if not tiene_permiso:
        messages.error(request, "You don't have permission to cancel this appointment.")
        return redirect("list_citas")

    if cita.get("estado") != "Pendiente":
        messages.warning(request, f"Cannot cancel an appointment that is already {cita.get('estado')}.")
        return redirect("list_citas")

    citas.update_one(
        {"_id": ObjectId(id)},
        {"$set": {
            "estado": "Cancelada",
            "fecha_cancelacion": datetime.now().strftime("%Y-%m-%dT%H:%M")
        }}
    )
    
    messages.info(request, "Appointment cancelled successfully.")
    return redirect("list_citas")


# -------------------- AGENDAR CITA --------------------
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

    # Obtener mascotas
    mascotas = []
    if rol == "Cliente":
        for m in pacientes.find({"id_user": user_id}):
            m["id"] = str(m["_id"])
            m["display_name"] = f"{m.get('nombre', 'Unknown')} ({m.get('especie', 'Unknown')})"
            m["owner_name"] = "You"
            mascotas.append(m)
    else:
        for m in pacientes.find():
            m["id"] = str(m["_id"])
            owner = users.find_one({"_id": ObjectId(m.get("id_user"))}) if m.get("id_user") else None
            owner_name = owner.get("User", "Unknown Owner") if owner else "Unknown Owner"
            m["display_name"] = f"{m.get('nombre', 'Unknown')} ({m.get('especie', 'Unknown')}) - Owner: {owner_name}"
            m["owner_name"] = owner_name
            mascotas.append(m)

    # ✅ Obtener veterinarios de USERS
    vets = []
    for v in users.find({"Rol": "Veterinario"}):
        v["id"] = str(v["_id"])
        vets.append(v)
    
    if not vets:
        messages.error(request, "No veterinarians available. Please contact the administrator.")
        return redirect("list_citas")

    # Procesar formulario
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

        # ✅ FIX: Usar dt_time en lugar de time
        if hora < dt_time(8, 0) or hora >= dt_time(19, 0):
            messages.error(request, "Appointments must be between 8:00 a.m. and 7:00 p.m.")
            return render(request, "appointments_form.html", {
                "mascotas": mascotas,
                "vets": vets,
                "action": "Add",
                "rol": rol
            })

        if dt_time(12, 0) <= hora < dt_time(14, 0):
            messages.error(request, "Lunch time (12–2 p.m.) is unavailable.")
            return render(request, "appointments_form.html", {
                "mascotas": mascotas,
                "vets": vets,
                "action": "Add",
                "rol": rol
            })

        fecha_fin = fecha_cita + timedelta(hours=duracion)

        # Verificar disponibilidad del veterinario
        citas_veterinario = list(citas.find({
            "id_veterinario": id_veterinario,
            "estado": {"$ne": "Cancelada"}
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
            except:
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
            "fecha_creacion": datetime.now().strftime("%Y-%m-%dT%H:%M"),
            "observacion": "",  # ✅ Campo nuevo para observaciones
            "fecha_observacion": "",
            "veterinario_observacion": ""
        })
        messages.success(request, "Appointment successfully scheduled.")
        return redirect("list_citas")

    return render(request, "appointments_form.html", {
        "mascotas": mascotas,
        "vets": vets,
        "action": "Add",
        "rol": rol
    })


# -------------------- EDITAR CITA --------------------
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
        if mascota and mascota.get("id_user") == current_user_id and cita.get("estado") == "Pendiente":
            tiene_permiso = True
    elif rol == "Veterinario":
        if cita.get("id_veterinario") == current_user_id and cita.get("estado") == "Pendiente":
            tiene_permiso = True
    
    if not tiene_permiso:
        messages.error(request, "You don't have permission to edit this appointment.")
        return redirect("list_citas")
    
    # Obtener mascotas
    mascotas = []
    if rol == "Cliente":
        for m in pacientes.find({"id_user": current_user_id}):
            m["id"] = str(m["_id"])
            m["display_name"] = f"{m.get('nombre', 'Unknown')} ({m.get('especie', 'Unknown')})"
            m["owner_name"] = "You"
            mascotas.append(m)
        
        if not mascotas:
            messages.warning(request, "You don't have any registered pets. Please add a pet first.")
            return redirect("add_paciente")
    else:
        for m in pacientes.find():
            m["id"] = str(m["_id"])
            owner = users.find_one({"_id": ObjectId(m.get("id_user"))}) if m.get("id_user") else None
            owner_name = owner.get("User", "Unknown") if owner else "Unknown"
            m["display_name"] = f"{m.get('nombre', 'Unknown')} ({m.get('especie', 'Unknown')}) - Owner: {owner_name}"
            m["owner_name"] = owner_name
            mascotas.append(m)
    
    # ✅ Obtener veterinarios de USERS
    vets = []
    for v in users.find({"Rol": "Veterinario"}):
        v["id"] = str(v["_id"])
        vets.append(v)
    
    # Procesar formulario
    if request.method == "POST":
        id_paciente = request.POST.get("paciente")
        id_veterinario = request.POST.get("veterinario")
        fecha_str = request.POST.get("fecha")
        motivo = request.POST.get("motivo", "").strip()
        
        if not all([id_paciente, id_veterinario, fecha_str, motivo]):
            messages.error(request, "Please fill all required fields.")
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

    # Preparar datos de la cita para el formulario
    cita["id_str"] = str(cita["_id"])
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
    report_type = request.GET.get("type", "appointments")
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
            
            # ✅ CAMBIO: Veterinario desde USERS
            vet = users.find_one({
                "_id": ObjectId(c.get("id_veterinario")),
                "Rol": "Veterinario"
            }) if c.get("id_veterinario") else None
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
        # ✅ CAMBIO: Obtener veterinarios de USERS
        vets_data = list(users.find({"Rol": "Veterinario"}))
        
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
            # ✅ CAMBIO: Si es veterinario, contar sus citas
            elif u.get("Rol") == "Veterinario":
                u["total_mascotas"] = 0
                u["total_citas"] = citas.count_documents({"id_veterinario": str(u["_id"])})
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
    
    # ✅ CAMBIO: Obtener lista de veterinarios de USERS para el filtro
    all_vets = []
    for v in users.find({"Rol": "Veterinario"}):
        all_vets.append({
            "id": str(v["_id"]),
            "nombre": v.get("nombre", "Unknown"),
            "especialidad": v.get("especialidad", "N/A")
        })
    
    context["all_vets"] = all_vets
    
    return render(request, "reports.html", context)



# ============================================
# BACKEND ACTUALIZADO - edit_profile con Foto
# ============================================



def edit_profile(request):
    """Vista para editar el perfil del usuario con imagen en MongoDB."""
    
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
        remove_profile_picture = request.POST.get("remove_profile_picture", "") == "true"
        
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
        
        # ===================================================
        # MANEJO DE FOTO DE PERFIL - BASE64 EN MONGODB
        # ===================================================
        
        # Opción 1: Eliminar foto actual
        if remove_profile_picture:
            update_data["profile_picture"] = None
        
        # Opción 2: Subir nueva foto
        if 'profile_picture' in request.FILES and not remove_profile_picture:
            profile_picture = request.FILES['profile_picture']
            
            # Validar tipo de archivo
            allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
            if profile_picture.content_type not in allowed_types:
                messages.error(request, "Invalid file type. Only JPG, PNG, GIF, and WEBP are allowed.")
                return redirect("edit_profile")
            
            # Validar tamaño (5MB máximo)
            if profile_picture.size > 5 * 1024 * 1024:
                messages.error(request, "File size must be less than 5MB.")
                return redirect("edit_profile")
            
            try:
                # Leer el archivo y convertir a Base64
                file_content = profile_picture.read()
                base64_image = base64.b64encode(file_content).decode('utf-8')
                
                # Guardar como Data URI (se puede usar directamente en <img src="">)
                data_uri = f"data:{profile_picture.content_type};base64,{base64_image}"
                
                # Guardar en la base de datos
                update_data["profile_picture"] = data_uri
                
            except Exception as e:
                messages.error(request, f"Error processing image: {str(e)}")
                return redirect("edit_profile")
        
        # ===================================================
        # CAMBIO DE CONTRASEÑA
        # ===================================================
        
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
        
        # ===================================================
        # ACTUALIZAR USUARIO EN LA BASE DE DATOS
        # ===================================================
        
        users.update_one(
            {"_id": user["_id"]},
            {"$set": update_data}
        )
        
        # ===================================================
        # ACTUALIZAR SESIÓN CON LA FOTO
        # ===================================================
        
        if "profile_picture" in update_data:
            request.session["user_profile_picture"] = update_data["profile_picture"] or ""
            request.session.modified = True
        
        # ===================================================
        # ACTUALIZAR DATOS DE VETERINARIO (si aplica)
        # ===================================================
        
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
    
    # ===================================================
    # GET REQUEST - MOSTRAR FORMULARIO
    # ===================================================
    
    return render(request, "edit_profile.html", {
        "username": username,
        "rol": rol,
        "user": user,
        "vet_data": vet_data
    })



# -------------------- LISTAR HISTORIAS CLÍNICAS --------------------
def list_historias(request):
    """Lista historias clínicas según el rol del usuario."""
    if "user" not in request.session:
        messages.warning(request, "Please log in first.")
        return redirect("login")

    rol = request.session.get("rol")
    username = request.session.get("user")
    
    current_user = users.find_one({"User": username})
    if not current_user:
        messages.error(request, "User not found.")
        return redirect("index")
    
    current_user_id = str(current_user["_id"])
    historias = []

    if rol == "Administrador" or rol == "Veterinario":
        # Admin y Veterinarios ven todas las historias
        historias = list(historia_clinica.find())
    elif rol == "Cliente":
        # Clientes solo ven historias de sus mascotas
        mascotas_ids = [str(m["_id"]) for m in pacientes.find({"id_user": current_user_id})]
        historias = list(historia_clinica.find({"id_paciente": {"$in": mascotas_ids}}))

    # Enriquecer datos
    for h in historias:
        h["id_str"] = str(h["_id"])
        
        # Obtener datos de la mascota
        if h.get("id_paciente"):
            mascota = pacientes.find_one({"_id": ObjectId(h["id_paciente"])})
            if mascota:
                h["mascota_nombre"] = mascota.get("nombre", "Unknown")
                h["mascota_especie"] = mascota.get("especie", "Unknown")
                h["mascota_raza"] = mascota.get("raza", "Unknown")
                
                # Obtener dueño
                if mascota.get("id_user"):
                    owner = users.find_one({"_id": ObjectId(mascota["id_user"])})
                    h["propietario_nombre"] = owner.get("nombre", "Unknown") if owner else "Unknown"
                else:
                    h["propietario_nombre"] = "Unknown"

        # Formatear fecha
        if h.get("fecha"):
            try:
                fecha_obj = datetime.strptime(h["fecha"], "%Y-%m-%d")
                h["fecha_formatted"] = fecha_obj.strftime("%B %d, %Y")
            except:
                h["fecha_formatted"] = h["fecha"]

        # Permisos
        h["puede_editar"] = False
        h["puede_eliminar"] = False
        
        if rol == "Administrador":
            h["puede_editar"] = True
            h["puede_eliminar"] = True
        elif rol == "Veterinario":
            h["puede_editar"] = True

    # Ordenar por fecha descendente
    historias.sort(key=lambda x: x.get("fecha", "1970-01-01"), reverse=True)

    return render(request, "medical_history_list.html", {
        "historias": historias,
        "rol": rol,
        "username": username,
        "total": len(historias)
    })


# -------------------- VER DETALLE DE HISTORIA CLÍNICA --------------------
def view_historia(request, id):
    """Muestra el detalle completo de una historia clínica."""
    if "user" not in request.session:
        messages.warning(request, "Please log in first.")
        return redirect("login")

    rol = request.session.get("rol")
    username = request.session.get("user")
    
    historia = historia_clinica.find_one({"_id": ObjectId(id)})
    if not historia:
        messages.error(request, "Medical history not found.")
        return redirect("list_historias")

    # Verificar permisos
    current_user = users.find_one({"User": username})
    if not current_user:
        messages.error(request, "User not found.")
        return redirect("list_historias")
    
    current_user_id = str(current_user["_id"])

    # Si es cliente, verificar que sea el dueño de la mascota
    if rol == "Cliente":
        mascota = pacientes.find_one({"_id": ObjectId(historia.get("id_paciente"))})
        if not mascota or mascota.get("id_user") != current_user_id:
            messages.error(request, "You don't have permission to view this medical history.")
            return redirect("list_historias")

    # Enriquecer datos
    historia["id_str"] = str(historia["_id"])
    
    if historia.get("id_paciente"):
        mascota = pacientes.find_one({"_id": ObjectId(historia["id_paciente"])})
        if mascota:
            historia["mascota"] = mascota
            historia["mascota"]["id_str"] = str(mascota["_id"])
            
            if mascota.get("id_user"):
                owner = users.find_one({"_id": ObjectId(mascota["id_user"])})
                if owner:
                    historia["propietario"] = owner

    # Formatear fecha
    if historia.get("fecha"):
        try:
            fecha_obj = datetime.strptime(historia["fecha"], "%Y-%m-%d")
            historia["fecha_formatted"] = fecha_obj.strftime("%B %d, %Y")
        except:
            historia["fecha_formatted"] = historia["fecha"]

    # Permisos
    puede_editar = rol in ["Administrador", "Veterinario"]
    puede_eliminar = rol == "Administrador"

    return render(request, "medical_history_detail.html", {
        "historia": historia,
        "rol": rol,
        "username": username,
        "puede_editar": puede_editar,
        "puede_eliminar": puede_eliminar
    })

# -------------------- CREAR HISTORIA CLÍNICA (CORREGIDO) --------------------
def add_historia(request):
    """Crea una nueva historia clínica."""
    if "user" not in request.session:
        messages.warning(request, "Please log in first.")
        return redirect("login")

    rol = request.session.get("rol")
    username = request.session.get("user")
    
    # Solo Veterinarios y Administradores pueden crear historias
    if rol not in ["Veterinario", "Administrador"]:
        messages.error(request, "You don't have permission to create medical histories.")
        return redirect("list_historias")

    current_user = users.find_one({"User": username})
    if not current_user:
        messages.error(request, "User not found.")
        return redirect("list_historias")
    
    current_user_id = str(current_user["_id"])

    # ✅ CORRECCIÓN: Obtener todas las mascotas con el nombre correcto del dueño
    mascotas = []
    for m in pacientes.find():
        m["id_str"] = str(m["_id"])
        
        # Buscar el dueño correctamente
        if m.get("id_user"):
            owner = users.find_one({"_id": ObjectId(m["id_user"])})
            if owner:
                # ✅ Usar el campo 'nombre' en lugar de 'User'
                m["owner_name"] = owner.get("nombre", owner.get("User", "Unknown"))
            else:
                m["owner_name"] = "Unknown"
        else:
            m["owner_name"] = "Unknown"
        
        # Crear display_name con el nombre correcto del dueño
        m["display_name"] = f"{m.get('nombre', 'Unknown')} ({m.get('especie', 'Unknown')}) - Owner: {m['owner_name']}"
        mascotas.append(m)

    if request.method == "POST":
        # Datos básicos
        id_paciente = request.POST.get("id_paciente")
        hc_numero = request.POST.get("hc_numero")
        fecha = request.POST.get("fecha")
        hora = request.POST.get("hora")
        
        # Datos del propietario
        propietario_nombre = request.POST.get("propietario_nombre")
        propietario_documento_tipo = request.POST.get("propietario_documento_tipo")
        propietario_documento_numero = request.POST.get("propietario_documento_numero")
        propietario_direccion = request.POST.get("propietario_direccion")
        propietario_telefono_fijo = request.POST.get("propietario_telefono_fijo")
        propietario_telefono_celular = request.POST.get("propietario_telefono_celular")
        propietario_email = request.POST.get("propietario_email")
        propietario_responsable = request.POST.get("propietario_responsable") == "on"
        
        # Reseña del paciente
        paciente_nombre = request.POST.get("paciente_nombre")
        paciente_especie = request.POST.get("paciente_especie")
        paciente_raza = request.POST.get("paciente_raza")
        paciente_sexo = request.POST.get("paciente_sexo")
        paciente_fecha_nacimiento = request.POST.get("paciente_fecha_nacimiento")
        paciente_peso = request.POST.get("paciente_peso")
        paciente_color = request.POST.get("paciente_color")
        paciente_chip = request.POST.get("paciente_chip")
        paciente_otras_identificaciones = request.POST.get("paciente_otras_identificaciones")
        paciente_fin_zootecnico = request.POST.get("paciente_fin_zootecnico")
        paciente_origen = request.POST.get("paciente_origen")
        
        # Anamnesis
        anamnesis_dieta = request.POST.get("anamnesis_dieta")
        anamnesis_enfermedades_previas = request.POST.get("anamnesis_enfermedades_previas")
        anamnesis_esterilizado = request.POST.get("anamnesis_esterilizado")
        anamnesis_num_partos = request.POST.get("anamnesis_num_partos")
        anamnesis_cirugias_previas = request.POST.get("anamnesis_cirugias_previas")

        # Validaciones básicas
        if not all([id_paciente, fecha, paciente_nombre, paciente_especie]):
            messages.error(request, "Please fill all required fields.")
            return render(request, "medical_history_form.html", {
                "mascotas": mascotas,
                "action": "Add",
                "rol": rol
            })

        # Crear documento
        nueva_historia = {
            "id_paciente": id_paciente,
            "hc_numero": hc_numero,
            "fecha": fecha,
            "hora": hora or "",
            
            # Propietario
            "propietario_nombre": propietario_nombre,
            "propietario_responsable": propietario_responsable,
            "propietario_documento_tipo": propietario_documento_tipo or "",
            "propietario_documento_numero": propietario_documento_numero or "",
            "propietario_direccion": propietario_direccion or "",
            "propietario_telefono_fijo": propietario_telefono_fijo or "",
            "propietario_telefono_celular": propietario_telefono_celular or "",
            "propietario_email": propietario_email or "",
            
            # Paciente
            "paciente_nombre": paciente_nombre,
            "paciente_especie": paciente_especie,
            "paciente_raza": paciente_raza or "",
            "paciente_sexo": paciente_sexo or "",
            "paciente_fecha_nacimiento": paciente_fecha_nacimiento or "",
            "paciente_peso": paciente_peso or "",
            "paciente_color": paciente_color or "",
            "paciente_chip": paciente_chip or "",
            "paciente_otras_identificaciones": paciente_otras_identificaciones or "",
            "paciente_fin_zootecnico": paciente_fin_zootecnico or "",
            "paciente_origen": paciente_origen or "",
            
            # Anamnesis
            "anamnesis_dieta": anamnesis_dieta or "",
            "anamnesis_enfermedades_previas": anamnesis_enfermedades_previas or "",
            "anamnesis_esterilizado": anamnesis_esterilizado or "",
            "anamnesis_num_partos": anamnesis_num_partos or "",
            "anamnesis_cirugias_previas": anamnesis_cirugias_previas or "",
            
            # Metadata
            "creado_por": current_user_id,
            "fecha_creacion": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "ultima_actualizacion": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        }

        historia_clinica.insert_one(nueva_historia)
        messages.success(request, "Medical history created successfully.")
        return redirect("list_historias")

    return render(request, "medical_history_form.html", {
        "mascotas": mascotas,
        "action": "Add",
        "rol": rol
    })


# -------------------- EDITAR HISTORIA CLÍNICA (CORREGIDO) --------------------
def edit_historia(request, id):
    """Edita una historia clínica existente."""
    if "user" not in request.session:
        messages.warning(request, "Please log in first.")
        return redirect("login")

    rol = request.session.get("rol")
    username = request.session.get("user")
    
    # Solo Veterinarios y Administradores pueden editar
    if rol not in ["Veterinario", "Administrador"]:
        messages.error(request, "You don't have permission to edit medical histories.")
        return redirect("list_historias")

    historia = historia_clinica.find_one({"_id": ObjectId(id)})
    if not historia:
        messages.error(request, "Medical history not found.")
        return redirect("list_historias")

    current_user = users.find_one({"User": username})
    if not current_user:
        messages.error(request, "User not found.")
        return redirect("list_historias")
    
    current_user_id = str(current_user["_id"])

    # ✅ CORRECCIÓN: Obtener todas las mascotas con el nombre correcto del dueño
    mascotas = []
    for m in pacientes.find():
        m["id_str"] = str(m["_id"])
        
        # Buscar el dueño correctamente
        if m.get("id_user"):
            owner = users.find_one({"_id": ObjectId(m["id_user"])})
            if owner:
                # ✅ Usar el campo 'nombre' en lugar de 'User'
                m["owner_name"] = owner.get("nombre", owner.get("User", "Unknown"))
            else:
                m["owner_name"] = "Unknown"
        else:
            m["owner_name"] = "Unknown"
        
        # Crear display_name con el nombre correcto del dueño
        m["display_name"] = f"{m.get('nombre', 'Unknown')} ({m.get('especie', 'Unknown')}) - Owner: {m['owner_name']}"
        mascotas.append(m)

    if request.method == "POST":
        # Datos básicos
        id_paciente = request.POST.get("id_paciente")
        hc_numero = request.POST.get("hc_numero")
        fecha = request.POST.get("fecha")
        hora = request.POST.get("hora")
        
        # Propietario
        propietario_nombre = request.POST.get("propietario_nombre")
        propietario_documento_tipo = request.POST.get("propietario_documento_tipo")
        propietario_documento_numero = request.POST.get("propietario_documento_numero")
        propietario_direccion = request.POST.get("propietario_direccion")
        propietario_telefono_fijo = request.POST.get("propietario_telefono_fijo")
        propietario_telefono_celular = request.POST.get("propietario_telefono_celular")
        propietario_email = request.POST.get("propietario_email")
        propietario_responsable = request.POST.get("propietario_responsable") == "on"
        
        # Paciente
        paciente_nombre = request.POST.get("paciente_nombre")
        paciente_especie = request.POST.get("paciente_especie")
        paciente_raza = request.POST.get("paciente_raza")
        paciente_sexo = request.POST.get("paciente_sexo")
        paciente_fecha_nacimiento = request.POST.get("paciente_fecha_nacimiento")
        paciente_peso = request.POST.get("paciente_peso")
        paciente_color = request.POST.get("paciente_color")
        paciente_chip = request.POST.get("paciente_chip")
        paciente_otras_identificaciones = request.POST.get("paciente_otras_identificaciones")
        paciente_fin_zootecnico = request.POST.get("paciente_fin_zootecnico")
        paciente_origen = request.POST.get("paciente_origen")
        
        # Anamnesis
        anamnesis_dieta = request.POST.get("anamnesis_dieta")
        anamnesis_enfermedades_previas = request.POST.get("anamnesis_enfermedades_previas")
        anamnesis_esterilizado = request.POST.get("anamnesis_esterilizado")
        anamnesis_num_partos = request.POST.get("anamnesis_num_partos")
        anamnesis_cirugias_previas = request.POST.get("anamnesis_cirugias_previas")

        if not all([id_paciente, fecha, paciente_nombre, paciente_especie]):
            messages.error(request, "Please fill all required fields.")
            historia["id_str"] = str(historia["_id"])
            return render(request, "medical_history_form.html", {
                "historia": historia,
                "mascotas": mascotas,
                "action": "Edit",
                "rol": rol
            })

        # Actualizar
        historia_clinica.update_one(
            {"_id": ObjectId(id)},
            {"$set": {
                "id_paciente": id_paciente,
                "hc_numero": hc_numero,
                "fecha": fecha,
                "hora": hora or "",
                
                "propietario_nombre": propietario_nombre,
                "propietario_responsable": propietario_responsable,
                "propietario_documento_tipo": propietario_documento_tipo or "",
                "propietario_documento_numero": propietario_documento_numero or "",
                "propietario_direccion": propietario_direccion or "",
                "propietario_telefono_fijo": propietario_telefono_fijo or "",
                "propietario_telefono_celular": propietario_telefono_celular or "",
                "propietario_email": propietario_email or "",
                
                "paciente_nombre": paciente_nombre,
                "paciente_especie": paciente_especie,
                "paciente_raza": paciente_raza or "",
                "paciente_sexo": paciente_sexo or "",
                "paciente_fecha_nacimiento": paciente_fecha_nacimiento or "",
                "paciente_peso": paciente_peso or "",
                "paciente_color": paciente_color or "",
                "paciente_chip": paciente_chip or "",
                "paciente_otras_identificaciones": paciente_otras_identificaciones or "",
                "paciente_fin_zootecnico": paciente_fin_zootecnico or "",
                "paciente_origen": paciente_origen or "",
                
                "anamnesis_dieta": anamnesis_dieta or "",
                "anamnesis_enfermedades_previas": anamnesis_enfermedades_previas or "",
                "anamnesis_esterilizado": anamnesis_esterilizado or "",
                "anamnesis_num_partos": anamnesis_num_partos or "",
                "anamnesis_cirugias_previas": anamnesis_cirugias_previas or "",
                
                "ultima_actualizacion": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            }}
        )

        messages.success(request, "Medical history updated successfully.")
        return redirect("view_historia", id=id)

    # Preparar datos
    historia["id_str"] = str(historia["_id"])
    historia["id_paciente"] = str(historia.get("id_paciente", ""))

    return render(request, "medical_history_form.html", {
        "historia": historia,
        "mascotas": mascotas,
        "action": "Edit",
        "rol": rol
    })


# -------------------- TAMBIÉN CORREGIR list_historias --------------------
def list_historias(request):
    """Lista historias clínicas según el rol del usuario."""
    if "user" not in request.session:
        messages.warning(request, "Please log in first.")
        return redirect("login")

    rol = request.session.get("rol")
    username = request.session.get("user")
    
    current_user = users.find_one({"User": username})
    if not current_user:
        messages.error(request, "User not found.")
        return redirect("index")
    
    current_user_id = str(current_user["_id"])
    historias = []

    if rol == "Administrador" or rol == "Veterinario":
        # Admin y Veterinarios ven todas las historias
        historias = list(historia_clinica.find())
    elif rol == "Cliente":
        # Clientes solo ven historias de sus mascotas
        mascotas_ids = [str(m["_id"]) for m in pacientes.find({"id_user": current_user_id})]
        historias = list(historia_clinica.find({"id_paciente": {"$in": mascotas_ids}}))

    # Enriquecer datos
    for h in historias:
        h["id_str"] = str(h["_id"])
        
        # Obtener datos de la mascota
        if h.get("id_paciente"):
            mascota = pacientes.find_one({"_id": ObjectId(h["id_paciente"])})
            if mascota:
                h["mascota_nombre"] = mascota.get("nombre", "Unknown")
                h["mascota_especie"] = mascota.get("especie", "Unknown")
                h["mascota_raza"] = mascota.get("raza", "Unknown")
                
                # ✅ CORRECCIÓN: Obtener dueño con nombre correcto
                if mascota.get("id_user"):
                    owner = users.find_one({"_id": ObjectId(mascota["id_user"])})
                    if owner:
                        # Usar 'nombre' en lugar de 'User'
                        h["propietario_nombre"] = owner.get("nombre", owner.get("User", "Unknown"))
                    else:
                        h["propietario_nombre"] = "Unknown"
                else:
                    h["propietario_nombre"] = "Unknown"

        # Formatear fecha
        if h.get("fecha"):
            try:
                fecha_obj = datetime.strptime(h["fecha"], "%Y-%m-%d")
                h["fecha_formatted"] = fecha_obj.strftime("%B %d, %Y")
            except:
                h["fecha_formatted"] = h["fecha"]

        # Permisos
        h["puede_editar"] = False
        h["puede_eliminar"] = False
        
        if rol == "Administrador":
            h["puede_editar"] = True
            h["puede_eliminar"] = True
        elif rol == "Veterinario":
            h["puede_editar"] = True

    # Ordenar por fecha descendente
    historias.sort(key=lambda x: x.get("fecha", "1970-01-01"), reverse=True)

    return render(request, "medical_history_list.html", {
        "historias": historias,
        "rol": rol,
        "username": username,
        "total": len(historias)
    })










# -------------------- ELIMINAR HISTORIA CLÍNICA --------------------
def delete_historia(request, id):
    """Elimina una historia clínica (solo administradores)."""
    if "user" not in request.session:
        messages.warning(request, "Please log in first.")
        return redirect("login")

    rol = request.session.get("rol")
    
    if rol != "Administrador":
        messages.error(request, "Only administrators can delete medical histories.")
        return redirect("list_historias")

    historia = historia_clinica.find_one({"_id": ObjectId(id)})
    if not historia:
        messages.error(request, "Medical history not found.")
        return redirect("list_historias")

    historia_clinica.delete_one({"_id": ObjectId(id)})
    messages.success(request, "Medical history deleted successfully.")
    return redirect("list_historias")






