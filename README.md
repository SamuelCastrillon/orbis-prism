# 💎 Orbis Prism

> "Deconstruct the engine, illuminate the API."

**Orbis Prism** es un conjunto de herramientas de ingeniería avanzada diseñado para el ecosistema de modding de Hytale. Su objetivo es descomponer el servidor oficial (`HytaleServer.jar`), aislar su núcleo lógico y proporcionar una interfaz de consulta inteligente (MCP) asistida por IA para desarrolladores.



---

## ✨ Características Principales

- **Auto-Detection:** Localiza la instalación oficial en Windows (`%APPDATA%\Hytale\install\...\Server`). Puedes sobrescribir la ruta con `prism config set game_path <ruta>`.
- **Prism Pipeline:** Descompilación quirúrgica usando JADX, eliminando librerías de terceros y centrándose exclusivamente en `com.hypixel.hytale`.
- **Deep Indexing:** Genera una base de datos SQLite con búsqueda de texto completo (FTS5) sobre más de 200k firmas de métodos y clases.
- **AI-Ready (MCP):** Servidor integrado de Model Context Protocol para que agentes como Claude o Cursor naveguen por la API sin alucinaciones.

## 🚀 Inicio Rápido

### Requisitos
- **Python 3.11+**
- **Java 25** (Para compatibilidad con el servidor de Hytale)
- **JADX** (Incluido en `/bin` o disponible en el PATH)

### Dónde se detecta HytaleServer.jar
- **Windows:** Por defecto se usa la instalación oficial. Ejecuta `prism init` para detectarla.
- **Ruta manual:** Solo necesitas la **carpeta raíz del juego** (no el JAR). Ejecuta `prism config set game_path <ruta>` con esa carpeta; Orbis Prism detectará automáticamente release y pre-release si existen.
  - **Cómo obtener la ruta:** Abre el **Launcher de Hytale** → **Settings** → **Open Directory** → copia la ruta (ej. `C:\Users\...\AppData\Roaming\Hytale`).

### Instalación
1. Clona el repositorio:

   ```bash
   git clone https://github.com/SamuelCastrillon/orbis-prism.git
   cd orbis-prism
   ```

2. Instala dependencias:

   ```bash
   pip install -r requirements.txt
   ```

3. Ejecuta el asistente de configuración:

   ```bash
   python main.py init
   ```

## 🛠 Comandos CLI

| Comando | Descripción |
|--------|-------------|
| `prism init` | Detecta HytaleServer.jar (y release/prerelease si existen) y guarda la configuración en `.prism.json`. |
| `prism build [release\|prerelease]` | **Flujo completo:** descompila e indexa (sobrescribe código y DB). Sin argumento: todas las versiones configuradas; con argumento: solo esa. |
| `prism decompile [release\|prerelease]` | Descompila con JADX y poda a `workspace/decompiled/<version>`. Sin argumento: todas las versiones configuradas. |
| `prism index [release\|prerelease]` | Indexa el código descompilado en la base SQLite (FTS5). Sin argumento, indexa el contexto activo. |
| `prism mcp [--http] [--port N] [--host DIR]` | Inicia el servidor MCP. Por defecto usa stdio; con `--http` expone transporte Streamable HTTP en el puerto (default 8000). Útil para Docker. |
| `prism context list` | Lista los contextos indexados (release/prerelease) y cuál está activo (*). |
| `prism context use <release\|prerelease>` | Establece el contexto activo (con qué versión de la API trabajas). |
| `prism lang list` | Lista idiomas disponibles. |
| `prism lang set <código>` | Cambia el idioma (ej. `prism lang set en`). |
| `prism config set game_path <ruta>` | Establece la ruta del juego (carpeta raíz o JAR). Launcher → Settings → Open Directory. |

## 📁 Estructura del proyecto

- **`/src`**: Código fuente del orquestador (Python).
- **`/workspace/decompiled/<version>`**: Código limpio del núcleo Hytale por versión (`release`, `prerelease`).
- **`/workspace/decompiled_raw/<version>`**: Salida cruda de JADX antes de la poda.
- **`/workspace/db`**: Bases SQLite por contexto (`prism_api_release.db`, `prism_api_prerelease.db`).
- **`/bin`**: Binarios de apoyo (JADX, etc.).

## 🔌 Configurar el servidor MCP

Por defecto el servidor usa **transporte stdio** (no abre ningún puerto). Tu cliente (Cursor, Claude Desktop, etc.) ejecuta el proceso y se comunica por stdin/stdout. Opcionalmente puedes usar **transporte HTTP** para despliegue remoto o en Docker.

### Modo stdio (por defecto)

1. **Ejecuta una vez** `python main.py mcp` en la carpeta del proyecto: si la salida es una terminal, se mostrarán comando, argumentos y directorio de trabajo.
2. **En Cursor** edita la configuración MCP (p. ej. `~/.cursor/mcp.json`) y añade un bloque como este (ajusta las rutas):

   ```json
   "orbis-prism": {
     "type": "stdio",
     "command": "python",
     "args": ["C:\\ruta\\absoluta\\a\\orbis-prism\\main.py", "mcp"],
     "cwd": "C:\\ruta\\absoluta\\a\\orbis-prism",
     "env": {
       "PRISM_WORKSPACE": "C:\\ruta\\absoluta\\a\\orbis-prism"
     }
   }
   ```

   - **cwd** es necesario para que el servidor encuentre `.prism.json` y `workspace/db`.
   - **env.PRISM_WORKSPACE** (opcional): si está definido, el servidor usa esta ruta como raíz del proyecto aunque el proceso se lance desde otro directorio.
3. Recarga la ventana de Cursor (Ctrl+Shift+P → "Developer: Reload Window") para que detecte el tool `prism_search`.

### Modo HTTP / Docker

Para exponer el servidor por red (por ejemplo en un contenedor):

- **CLI:** `prism mcp --http [--port 8000] [--host 0.0.0.0]`. Por defecto escucha en `0.0.0.0:8000` (todas las interfaces).
- **Variables de entorno (opcionales):** `MCP_TRANSPORT=http` (o `streamable-http`), `MCP_PORT`, `MCP_HOST`. La línea de comandos tiene prioridad sobre el entorno.

El endpoint MCP en modo HTTP es `http://<host>:<port>/mcp`. Los clientes MCP compatibles con Streamable HTTP pueden conectarse a esa URL.

**Ejemplo mínimo con Docker:** construye una imagen que instale dependencias y ejecute `python main.py mcp --http`, expón el puerto 8000 y conecta tu cliente a `http://<ip-contenedor>:8000/mcp`.

## 📜 License
This project is licensed under the MIT License. See the `LICENSE` file for more details.

Disclaimer: Orbis Prism is an independent development tool and is not affiliated with Hypixel Studios.
