# Guía para agentes: Orbis Prism

Consulta siempre este archivo cuando trabajes en este repositorio para tener contexto del proyecto. Para contribuir (estándares, PRs, pruebas), ver [CONTRIBUTING.md](CONTRIBUTING.md). Visión general del proyecto: [README.md](README.md).

---

## Qué es Orbis Prism

Herramienta de ingeniería para el modding de **Hytale**. Toma el servidor oficial (`HytaleServer.jar`), lo descompila con JADX, deja solo el núcleo `com.hypixel.hytale`, indexa clases y métodos en SQLite con FTS5 y expone esa API vía **CLI** y **servidor MCP** para que agentes (Cursor, Claude, etc.) consulten la API sin “alucinar”.

- **Carpeta del proyecto:** `orbis-prism/` (dentro del workspace `01 ServerContext`).
- **Entrada:** `python main.py` desde `orbis-prism/` o desde la raíz del workspace (el `main.py` de la raíz delega a orbis-prism).
- **Stack:** Python 3.11+, JADX, SQLite (FTS5), dependencia principal `mcp>=1.0.0`.

---

## Estructura del código (`orbis-prism/src/prism/`)

Arquitectura por capas (hexagonal):

| Capa | Ubicación | Rol |
|------|-----------|-----|
| **Domain** | `domain/` | Tipos y constantes: `ServerVersion`, `VALID_SERVER_VERSIONS`, `normalize_version()` en `constants.py`; `types.py` con tipos compartidos. |
| **Ports** | `ports/` | Interfaces (Protocol): `ConfigProvider` (raíz, DB path, decompiled dir, load/save config) e `IndexRepository` (search, get_class, get_method, list_classes, get_stats). |
| **Application** | `application/` | Casos de uso: `search_api` en `search.py`; `get_class`, `get_method`, `list_classes`, `get_index_stats`, `get_context_list` en `index_queries.py`; `read_source` en `read_source.py`. Reciben los ports por inyección. |
| **Infrastructure** | `infrastructure/` | Implementaciones: `config_impl` (paths, .prism.json, env), `db` (schema SQLite + FTS5), `file_config` (ConfigProvider), `sqlite_repository` (IndexRepository), `detection` (JAR/JADX), `decompile` (JADX; `run_decompile_only` sin prune), `prune`, `extractor` (regex sobre Java → DB), `workspace_cleanup` (clean_db, clean_build, reset_workspace). |
| **Entrypoints** | `entrypoints/` | Paquete `cli/` (comandos: `query`, `mcp`, `context`/`ctx` con **init** —comando inicial—, detect, clean, reset, decompile, prune, db, list, use; `lang`, `config`). No hay comando top-level `init`; el comando inicial es `ctx init`. `mcp_server.py`: herramientas MCP (`prism_search`, etc.). |

**Fuera de capas:** `i18n.py` (traducciones es/en desde `locales/*.json`).

---

## Flujos principales

1. **Comando inicial: ctx init.** El usuario ejecuta `python main.py ctx init` (o `context init`). Si el JAR no está configurado, antes debe ejecutar `ctx detect` para que `detection` encuentre `HytaleServer.jar` (env, config, %APPDATA%\Hytale), guarde `.prism.json` y cree `workspace/`, etc. No existe comando top-level `init`.
2. **Context init (pipeline completo):** `context init` ejecuta: decompile (solo JADX) → prune → db. JADX escribe en `workspace/decompiled_raw/<version>`; `prune` copia solo `com/hypixel/hytale` a `workspace/decompiled/<version>`; `extractor` indexa en `workspace/db/prism_api_<version>.db`.
3. **Pasos sueltos:** `context decompile` (solo JADX), `context prune`, `context db` (indexar). `context clean` (db | build | all) y `context reset` (dejar proyecto a cero).
4. **Query / MCP:** La aplicación usa `ConfigProvider` y `IndexRepository`; el CLI y el MCP instancian `FileConfigProvider` y `SqliteIndexRepository` y llaman a los casos de uso (`search_api`, `get_class`, etc.).

---

## Puntos que un agente debe tener en cuenta

- **Config:** Rutas y configuración en `infrastructure/config_impl.py`. Constantes: `CONFIG_KEY_JAR_PATH`, `CONFIG_KEY_ACTIVE_SERVER`, `ENV_WORKSPACE`, `CONFIG_FILENAME` (`.prism.json`), etc. El CLI usa `config_impl.get_project_root()`, `config_impl.load_config()`, etc.
- **Versiones:** Solo dos: `"release"` y `"prerelease"`. Usar `domain.constants.normalize_version()` y `VALID_SERVER_VERSIONS` para no duplicar lógica.
- **Búsqueda:** Caso de uso `application.search.search_api`; recibe `ConfigProvider`, `IndexRepository`, root, version, query, limit, etc.
- **Context list:** Listado de versiones indexadas y activa viene de `application.index_queries.get_context_list(config_provider, root)`; el CLI no debe duplicar esa lógica.
- **Raíz del proyecto:** Puede venir de `PRISM_WORKSPACE` o inferirse (buscando `main.py` hacia arriba). Los entrypoints y la infra dependen de esa raíz para `.prism.json` y `workspace/`.
- **Idioma:** Código, comentarios y mensajes de commit en **inglés**. Mensajes al usuario vía i18n en `locales/es.json` y `locales/en.json`. Para estándares de contribución, ver [CONTRIBUTING.md](CONTRIBUTING.md).

---

## Cómo ejecutar

- Desde **orbis-prism:** El comando inicial es **`python main.py ctx init`** (pipeline completo; si falta el JAR, ejecutar antes `python main.py ctx detect`). Luego: `python main.py ctx list`, `python main.py ctx clean db`, `python main.py query <término>`, `python main.py mcp`, etc.
- Desde **raíz del workspace:** `python main.py -h` (el `main.py` de la raíz delega a orbis-prism).

Si vas a tocar CLI, MCP o configuración, conviene leer en este orden: `entrypoints/cli/main.py`, `entrypoints/cli/context.py`, `entrypoints/mcp_server.py`, `infrastructure/config_impl.py`.
