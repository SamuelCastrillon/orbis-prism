# 💎 Orbis Prism

> "Deconstruct the engine, illuminate the API."

**Orbis Prism** es un conjunto de herramientas de ingeniería avanzada diseñado para el ecosistema de modding de Hytale. Su objetivo es descomponer el servidor oficial (`HytaleServer.jar`), aislar su núcleo lógico y proporcionar una interfaz de consulta inteligente (MCP) asistida por IA para desarrolladores.

> **⚠️ Aviso importante**
>
> - **Orbis Prism es una herramienta de desarrollo independiente y no está afiliada a Hypixel Studios.**
> - **Es necesario tener instalada previamente una versión oficial del juego (Hytale).** Esta herramienta **no incluye ningún código fuente ni binario del juego**: solo localiza tu instalación, descompila el servidor que ya tienes y genera índices para consulta. Sin una instalación válida de Hytale (por ejemplo vía el launcher oficial), Orbis Prism no puede funcionar.

---


## ✨ Características Principales

- **Auto-Detection:** Localiza la instalación oficial en Windows (`%APPDATA%\Hytale\install\...\Server`). Puedes sobrescribir la ruta con `python main.py config_impl set game_path <ruta>`.
- **Prism Pipeline:** Descompilación quirúrgica usando JADX, eliminando librerías de terceros y centrándose exclusivamente en `com.hypixel.hytale`.
- **Deep Indexing:** Genera una base de datos SQLite con búsqueda de texto completo (FTS5) sobre más de 200k firmas de métodos y clases.
- **AI-Ready (MCP):** Servidor integrado de Model Context Protocol para que agentes como Claude o Cursor naveguen por la API sin alucinaciones.
- **Multi-language:** El CLI y los mensajes al usuario están disponibles en **español** e **inglés**. Puedes cambiar el idioma en cualquier momento (ver más abajo).

## 🌐 Idioma / Language

Orbis Prism muestra mensajes, ayuda y errores en **español** o **inglés**. El idioma se guarda en la configuración del proyecto.

| Acción | Comando |
|--------|---------|
| Ver idiomas disponibles | `python main.py lang list` |
| Cambiar a inglés | `python main.py lang set en` |
| Cambiar a español | `python main.py lang set es` |

Tras ejecutar `lang set <código>`, los siguientes mensajes del CLI usarán ese idioma.

## 🚀 Inicio Rápido

### Requisitos
- **Instalación oficial de Hytale** (launcher y juego). Orbis Prism no distribuye código ni binarios del juego; trabaja sobre tu instalación.
- **Python 3.11+**
- **Java 25** (para compatibilidad con el servidor de Hytale)
- **JADX** (incluido en `/bin` o disponible en el PATH)

### Comando inicial (primera vez)

El comando que debes ejecutar al empezar es **`ctx init`** (o `context init`). Detecta el JAR de Hytale, descompila, poda e indexa la API en SQLite. Si el JAR no está detectado, ejecuta antes **`ctx detect`** para que Orbis Prism localice `HytaleServer.jar` y guarde la configuración en `.prism.json`.

### Dónde se detecta HytaleServer.jar
- **Windows:** Por defecto se usa la instalación oficial. Ejecuta `python main.py ctx detect` para detectarla.
- **Ruta manual:** Solo necesitas la **carpeta raíz del juego** (no el JAR). Ejecuta `python main.py config_impl set game_path <ruta>` con esa carpeta; Orbis Prism detectará automáticamente release y pre-release si existen.
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

3. Ejecuta el comando inicial (detecta JAR, descompila e indexa la API):

   ```bash
   python main.py ctx init
   ```

   **Si el JAR no se encuentra:**
   - Prueba primero `python main.py ctx detect` (por si la instalación está en una ruta que se detecta automáticamente).
   - **Para indicar la ruta manualmente:** usa la carpeta raíz del juego (no el JAR). En el **Launcher de Hytale** → **Settings** → **Open Directory** copia esa ruta y ejecuta:
     ```bash
     python main.py config_impl set game_path "C:\ruta\a\tu\carpeta\Hytale"
     ```
     Luego vuelve a ejecutar `python main.py ctx init`.

## 🛠 Comandos CLI

El comando **inicial** recomendado es **`python main.py ctx init`** (o `context init`): detecta el JAR si hace falta, descompila, poda e indexa. Puedes usar `ctx` como abreviatura de `context`.

| Comando | Descripción |
|--------|-------------|
| `python main.py ctx init [release\|prerelease\|--all]` | **Comando inicial.** Pipeline completo: detecta JAR si falta, descompila (JADX), poda e indexa en SQLite. |
| `python main.py ctx detect` | Detecta HytaleServer.jar (y release/prerelease si existen) y guarda la configuración en `.prism.json`. |
| `python main.py ctx clean <db\|build\|all>` | Limpia: `db` (solo bases de datos), `build` (decompilado), `all` (todo). |
| `python main.py ctx reset` | Deja el proyecto a cero (borra DB, build y `.prism.json`). |
| `python main.py ctx decompile [release\|prerelease\|--all]` | Solo JADX → `workspace/decompiled_raw/<version>`. |
| `python main.py ctx prune [release\|prerelease\|--all]` | Poda: copia solo `com.hypixel.hytale` de raw a decompiled. |
| `python main.py ctx db [release\|prerelease\|--all]` | Indexa el código en SQLite (FTS5). |
| `python main.py ctx list` | Lista los contextos indexados (release/prerelease) y cuál está activo (*). |
| `python main.py ctx use <release\|prerelease>` | Establece el contexto activo. |
| `python main.py query <término> [release\|prerelease]` | Busca en la DB indexada (FTS5). |
| `python main.py mcp [--http] [--port N] [--host DIR]` | Inicia el servidor MCP. Por defecto stdio; con `--http` expone HTTP en el puerto (default 8000). |
| `python main.py lang list` | Lista idiomas disponibles. |
| `python main.py lang set <código>` | Cambia el idioma (ej. `lang set en`). |
| `python main.py config_impl set game_path <ruta>` | Establece la ruta del juego (carpeta raíz o JAR). Launcher → Settings → Open Directory. |

Para una **documentación más detallada del CLI** (argumentos, flujos, estructura del código y descripción de cada subcomando), ver [Documentación del CLI](src/prism/entrypoints/cli/README.md).

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

> **Nota:** Este modo está en fase de construcción; la interfaz y el comportamiento pueden cambiar.

Para exponer el servidor por red (por ejemplo en un contenedor):

- **CLI:** `python main.py mcp --http [--port 8000] [--host 0.0.0.0]`. Por defecto escucha en `0.0.0.0:8000` (todas las interfaces).
- **Variables de entorno (opcionales):** `MCP_TRANSPORT=http` (o `streamable-http`), `MCP_PORT`, `MCP_HOST`. La línea de comandos tiene prioridad sobre el entorno.

El endpoint MCP en modo HTTP es `http://<host>:<port>/mcp`. Los clientes MCP compatibles con Streamable HTTP pueden conectarse a esa URL.

**Ejemplo mínimo con Docker:** construye una imagen que instale dependencias y ejecute `python main.py mcp --http`, expón el puerto 8000 y conecta tu cliente a `http://<ip-contenedor>:8000/mcp`.

## 🤝 Contribuir

Si quieres contribuir al proyecto, consulta la [Guía de contribución](CONTRIBUTING.md). Para contexto técnico y arquitectura (agentes, desarrollo), ver también [Agents.md](Agents.md).

## 📜 License

This project is licensed under the MIT License. See the `LICENSE` file for more details.
