# 🧩 Patrón de Diseño PROTOTYPE — API con FastAPI

Este proyecto implementa el patrón **Prototype** utilizando **FastAPI**, como parte del conjunto de patrones de diseño del taller de aprovisionamiento multi-cloud.

El patrón **Prototype** permite crear nuevos objetos clonando instancias preconfiguradas (plantillas) en lugar de construirlas desde cero.  
Es ideal para entornos donde la creación de objetos es costosa o repetitiva, como la provisión de recursos en la nube (VMs, redes, almacenamiento).

---

## 📘 Objetivo

Implementar un sistema de **prototipos (plantillas)** de recursos de infraestructura (VM, Network, Storage) que puedan clonarse rápidamente para generar nuevas instancias personalizadas, garantizando coherencia y simplicidad en la creación de configuraciones.

---

## 🧠 Conceptos Clave del Patrón Prototype

- **Define una interfaz `clone()`** en los objetos prototipo.
- Cada clase concreta (`VMPrototype`, `NetworkPrototype`, `StoragePrototype`) implementa esa interfaz para devolver copias independientes.
- Un **PrototypeRegistry** centraliza el registro y recuperación de plantillas por clave.
- Permite crear variaciones de un objeto sin depender de su clase concreta.

---

## ⚙️ Estructura del Proyecto
📁 prototype-api
┣ 📄 app.py # Código principal de la API
┣ 📄 README.md # Este archivo
┣ 📄 requirements.txt # Dependencias (FastAPI, Uvicorn)
┗ 📄 diagram.puml # Diagrama UML del patrón Prototype


---

## 🧩 Diagrama UML (PlantUML)

```plantuml
@startuml
interface Prototype {
  + clone(): Prototype
}

class VMPrototype {
  - id: string
  - provider: string
  - name: string
  - vcpus: int
  - memory_gb: int
  - disk_gb: int
  + clone(): VMPrototype
  + apply_overrides(map): void
}

class NetworkPrototype {
  - id: string
  - provider: string
  - region: string
  - public_ip: boolean
  - firewall_rules: List<String>
  + clone(): NetworkPrototype
  + apply_overrides(map): void
}

class StoragePrototype {
  - id: string
  - provider: string
  - size_gb: int
  - iops: int
  - encrypted: boolean
  + clone(): StoragePrototype
  + apply_overrides(map): void
}

class PrototypeRegistry {
  - vm_templates: Map<String, VMPrototype>
  - net_templates: Map<String, NetworkPrototype>
  - storage_templates: Map<String, StoragePrototype>
  + register_vm_template(key, VMPrototype)
  + get_vm_clone(key): VMPrototype
}

Prototype <|.. VMPrototype
Prototype <|.. NetworkPrototype
Prototype <|.. StoragePrototype
PrototypeRegistry "1" o-- "*" VMPrototype
PrototypeRegistry "1" o-- "*" NetworkPrototype
PrototypeRegistry "1" o-- "*" StoragePrototype
@enduml


1️⃣ Clonar el repositorio
git clone https://github.com/AnibalFuentes/patron-prototype.git
cd prototype-api

2️⃣ Instalar dependencias
pip install fastapi uvicorn pydantic

3️⃣ Ejecutar el servidor
uvicorn app:app --reload --port 8000

4️⃣ Abrir la documentación interactiva

👉 http://127.0.0.1:8000/docs

🔌 Endpoints disponibles
Método	Ruta	Descripción
POST	/provision	Clona una plantilla existente y crea una instancia personalizada.
GET	/provisioned	Lista todos los clones creados durante la ejecución.
🧾 Ejemplos de uso
✅ Crear una instancia AWS personalizada

Request:

curl -X POST "http://127.0.0.1:8000/provision" \
 -H "Content-Type: application/json" \
 -d '{
   "provider": "aws",
   "template_key": "aws-standard",
   "name": "web-server-01",
   "overrides": {"vcpus": 4, "memory_gb": 8},
   "network_overrides": {"region":"us-east-1", "public_ip": true},
   "storage_overrides": {"size_gb": 80}
 }'


Response:

{
  "status": "provisioned",
  "vm": {
    "id": "f9d8e4c2-1b4b-4b85-9335-01fd6a3f019d",
    "provider": "aws",
    "name": "web-server-01",
    "vcpus": 4,
    "memory_gb": 8,
    "disk_gb": 50
  },
  "network": { "region": "us-east-1", "public_ip": true },
  "storage": { "size_gb": 80, "encrypted": true }
}

✅ Crear una instancia GCP (sin overrides)
curl -X POST "http://127.0.0.1:8000/provision" \
 -H "Content-Type: application/json" \
 -d '{
   "provider": "gcp",
   "template_key": "gcp-memopt"
 }'

✅ Ver recursos clonados
curl -X GET "http://127.0.0.1:8000/provisioned"

🧱 Validaciones implementadas
Tipo de validación	Descripción	Respuesta
Estructura JSON	Se valida automáticamente con Pydantic.	422 Unprocessable Entity
Plantilla no registrada	Si la clave no existe en el registro.	404 Not Found
Proveedor incoherente	Si provider no coincide en VM, Network y Storage.	400 Bad Request
Campo override inexistente	El campo no se aplica, pero no lanza error.	Ignorado
Tipo de dato incorrecto	Ejemplo: provider: 123.	422 Validation Error
🧩 Integración con otros patrones
Patrón	Función	Relación con Prototype
Factory Method	Crea recursos concretos por proveedor.	Prototype puede clonar objetos antes de enviarlos a las fábricas.
Abstract Factory	Agrupa creaciones de familias de objetos (VM + Network + Storage).	Usa prototipos como plantillas base.
Builder	Permite construir configuraciones paso a paso.	Builder puede clonar prototipos y luego aplicar pasos adicionales.
💬 Ejemplo de flujo completo

El cliente solicita un clon de la plantilla "aws-standard".

La API obtiene los prototipos de VM, Network y Storage desde el PrototypeRegistry.

Se aplican overrides (personalizaciones).

Se valida la coherencia del proveedor.

Se devuelven los objetos clonados con nuevos IDs únicos.

📄 Dependencias

Python 3.9+

FastAPI – Framework para la API REST.

Uvicorn – Servidor ASGI.

Pydantic – Validación de modelos de datos.

UUID / copy – Generación de identificadores y clonación profunda.

📚 Autor

Aníbal Fuentes
Estudiante de Ingeniería de Sistemas
Proyecto: Patrones de Diseño — Taller WS4 (Prototype)
2025

🧠 Créditos y referencias

Gamma, Helm, Johnson, Vlissides. Design Patterns (GoF).

FastAPI Documentation

PlantUML Documentation