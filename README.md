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
   git clone https://github.com/SamuelCastrillon/orbis-prism.git
   cd orbis-prism
   
3. Install dependencies:
   
   ```bash
   pip install -r requirements.txt

5. Run the setup assistant:
   
   ```bash
   python main.py init

   
## 🛠 CLI Commands
- `prism decompile`: Starts the extraction and pruning of the source code.

- `prism index`: Analyzes .java files and populates the search index.

- `prism serve`: Launches the MCP bridge to connect your favorite AI.

## 📁 Project Structure
`/src`: Python orchestrator source code.

`/workspace/decompiled`: The clean Hytale "Core" (Java 25).

`/workspace/db`: `prism_api.db` SQLite index.

`/bin`: Support binaries and external tools.

## 📜 License
This project is licensed under the MIT License. See the `LICENSE` file for more details.

Disclaimer: Orbis Prism is an independent development tool and is not affiliated with Hypixel Studios.
