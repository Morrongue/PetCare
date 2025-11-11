
from pymongo import MongoClient

client = MongoClient("mongodb+srv://Watf:morrongo@project1.551ddy2.mongodb.net/")

db = client["Clinica_Veterinaria"]
users = db["user"]
pacientes = db["paciente"]
veterinarios = db["veterinarios"]
citas = db["citas"]
auditoria = db["auditoria"]
historia_clinica =db["historia_clinica"]
payments = db["payments"]


