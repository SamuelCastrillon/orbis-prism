# 💎 Orbis Prism

> "Deconstruct the engine, illuminate the API."

**Orbis Prism** es un conjunto de herramientas de ingeniería avanzada diseñado para el ecosistema de modding de Hytale. Su objetivo es descomponer el servidor oficial (`HytaleServer.jar`), aislar su núcleo lógico y proporcionar una interfaz de consulta inteligente (MCP) asistida por IA para desarrolladores.



---

## ✨ Características Principales

- **Auto-Detection:** Localiza automáticamente la instalación de Hytale en rutas estándar de Windows (`%LOCALAPPDATA%`).
- **Prism Pipeline:** Descompilación quirúrgica usando JADX, eliminando librerías de terceros y centrándose exclusivamente en `com.hypixel.hytale`.
- **Deep Indexing:** Genera una base de datos SQLite con búsqueda de texto completo (FTS5) sobre más de 200k firmas de métodos y clases.
- **AI-Ready (MCP):** Servidor integrado de Model Context Protocol para que agentes como Claude o Cursor naveguen por la API sin alucinaciones.

## 🚀 Inicio Rápido

### Requisitos
- **Python 3.11+**
- **Java 25** (Para compatibilidad con el servidor de Hytale)
- **JADX** (Incluido en `/bin` o disponible en el PATH)

### Instalación
1. Clona el repositorio:
   ```bash
   git clone https://github.com/SamuelCastrillon/orbis-prism-project.git
   cd orbis-prism
   
