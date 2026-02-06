# Guía de contribución

Gracias por tu interés en contribuir a **Orbis Prism**. Esta guía resume cómo participar de forma ordenada.

---

## Antes de empezar

- **Requisitos:** Python 3.11+, instalación oficial de Hytale (para probar el pipeline). Ver [README](README.md#-inicio-rápido).
- **Contexto técnico:** Si vas a modificar código, lee [Agents.md](Agents.md) para entender la arquitectura (capas, flujos, comandos). Para cambios en el CLI, consulta también [Documentación del CLI](src/prism/entrypoints/cli/README.md).

**Documentación relacionada:** [README](README.md) (visión general e inicio rápido) · [Agents.md](Agents.md) (guía para agentes y arquitectura).

---

## Cómo contribuir

1. **Issues:** Abre un issue para reportar un bug o proponer una mejora. Describe pasos para reproducir y entorno (OS, Python).
2. **Ramas:** Crea una rama desde `main` (por ejemplo `fix/descripcion` o `feat/nueva-funcionalidad`).
3. **Pull requests:** Envía un PR contra `main`. Describe qué cambia y por qué. Si modificas comandos o mensajes al usuario, actualiza README y/o [CLI README](src/prism/entrypoints/cli/README.md) y las cadenas en `locales/es.json` y `locales/en.json`.

---

## Estándares del proyecto

- **Código:** Variables, funciones, clases y nombres de archivos en **inglés**.
- **Comentarios:** En **inglés** (en código y en documentación técnica), para mantener el proyecto accesible a contribuidores internacionales.
- **Commits:** Mensajes de commit en **inglés**.
- **Mensajes al usuario:** Traducciones en `src/prism/locales/es.json` y `en.json`; mantener ambas lenguas sincronizadas cuando añadas o cambies claves.
- **Traducción obligatoria (es + en):** Todo texto que vea el usuario (nuevos comandos, mensajes de ayuda, errores, descripciones en el CLI o en la salida de herramientas) debe contar con su correspondiente entrada en **español** e **inglés** en los archivos de locales. No se aceptan cadenas solo en un idioma: cada clave nueva debe existir en `es.json` y en `en.json`.
- **Comandos y ayuda:** Los comandos reales son `ctx`, `config_impl`, etc. La ayuda (`help.py`) y los mensajes de error deben mostrar exactamente lo que el usuario debe escribir (por ejemplo `config_impl set game_path`, no `config set game_path`).

---

## Probar tus cambios

1. Instala dependencias: `pip install -r requirements.txt`
2. Si tienes Hytale instalado: `python main.py ctx detect` y luego `python main.py ctx init` (o solo `ctx db` si ya tienes código descompilado).
3. Prueba los comandos que hayas tocado (por ejemplo `python main.py ctx list`, `python main.py query algo`, `python main.py --help`).
4. Si modificas la capa de aplicación o MCP, verifica que las herramientas MCP sigan respondiendo correctamente.

---

## Estructura rápida

| Ubicación        | Contenido |
|-----------------|-----------|
| `src/prism/domain/`      | Tipos y constantes (versiones, normalización). |
| `src/prism/ports/`      | Interfaces (ConfigProvider, IndexRepository). |
| `src/prism/application/`| Casos de uso (búsqueda, indexación, lectura de código). |
| `src/prism/infrastructure/` | Implementaciones (config, JADX, SQLite, prune, etc.). |
| `src/prism/entrypoints/cli/` | Comandos CLI (context/ctx, query, mcp, lang, config_impl). |
| `src/prism/locales/`    | Cadenas i18n (es/en). |

No dupliques lógica entre CLI y aplicación: el CLI debe delegar en los casos de uso y en `config_impl`/repositorios.

---

## Licencia

Al contribuir, aceptas que tus aportaciones se licencien bajo la [MIT License](LICENSE).

---

**Véase también:** [README](README.md) | [Agents.md](Agents.md)
