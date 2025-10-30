from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    
    # 🔹 NUEVOS: Dashboard y Reportes
    
    path("reports/", views.reports, name="reports"),
    
    path("register/", views.register, name="register"),
    path("login/", views.login, name="login"),
    path("logout/", views.logout, name="logout"),
    path('edit/', views.edit_profile, name='edit_profile'),

    # Pacientes CRUD
    path("patients/", views.list_pacientes, name="list_pacientes"),
    path("patients/add/", views.add_paciente, name="add_paciente"),
    path("patients/edit/<str:id>/", views.edit_paciente, name="edit_paciente"),
    path("patients/delete/<str:id>/", views.delete_paciente, name="delete_paciente"),

    # --- CRUD de Veterinarios ---
    path("vets/", views.list_veterinarios, name="list_veterinarios"),
    path("vets/add/", views.add_veterinario, name="add_veterinario"),
    path("vets/edit/<str:id>/", views.edit_veterinario, name="edit_veterinario"),
    path("vets/delete/<str:id>/", views.delete_veterinario, name="delete_veterinario"),

    # ---- CRUD de Citas ----
    path('appointments/', views.list_citas, name='list_citas'),
    path('appointments/add/', views.add_cita, name='add_cita'),
    path('appointments/edit/<str:id>/', views.edit_cita, name='edit_cita'),
    path('citas/cancel/<str:id>/', views.cancel_cita, name='cancel_cita'), 

    # Panel de administrador
    path("panel/users/", views.admin_users_list, name="admin_users_list"),
    path("panel/users/add/", views.admin_users_add, name="admin_users_add"),
    path("panel/users/edit/<str:id>/", views.admin_users_edit, name="admin_users_edit"),
    path("panel/users/delete/<str:id>/", views.admin_users_delete, name="admin_users_delete"),
    path("panel/users/reset/<str:id>/", views.admin_users_reset_password, name="admin_users_reset_password"),
]