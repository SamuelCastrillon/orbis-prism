# 💎 Orbis Prism

**[Leer en español](README.es.md)**

> "Deconstruct the engine, illuminate the API."

**Orbis Prism** is a set of advanced engineering tools designed for the Hytale modding ecosystem. It decomposes the official server (`HytaleServer.jar`), isolates its core logic, and provides an AI-assisted intelligent query interface (MCP) for developers.

> **⚠️ Important notice**
>
> - **Orbis Prism is an independent development tool and is not affiliated with Hypixel Studios.**
> - **You must have an official version of the game (Hytale) installed.** This tool **does not include any game source code or binaries**: it only locates your installation, decompiles the server you already have, and generates indexes for querying. Without a valid Hytale installation (e.g. via the official launcher), Orbis Prism cannot work.

---

## ✨ Main features

- **Auto-detection:** Locates the official installation on Windows (`%APPDATA%\Hytale\install\...\Server`). You can override the path with `python main.py config_impl set game_path <path>`.
- **Prism pipeline:** Surgical decompilation using JADX, removing third-party libraries and focusing exclusively on `com.hypixel.hytale`.
- **Deep indexing:** Generates an SQLite database with full-text search (FTS5) over 200k+ method and class signatures.
- **AI-ready (MCP):** Integrated Model Context Protocol server so agents like Claude or Cursor can navigate the API without hallucinations.
- **Multi-language:** The CLI and user messages are available in **Spanish** and **English**. You can change the language at any time (see below).

## 🌐 Language / Idioma

Orbis Prism shows messages, help, and errors in **Spanish** or **English**. The language is stored in the project configuration.

| Action | Command |
|--------|---------|
| List available languages | `python main.py lang list` |
| Switch to English | `python main.py lang set en` |
| Switch to Spanish | `python main.py lang set es` |

After running `lang set <code>`, subsequent CLI messages will use that language.

## 🚀 Quick start

### Requirements

- **Official Hytale installation** (launcher and game). Orbis Prism does not distribute any game code or binaries; it works on top of your installation.
- **Python 3.11+**
- **Java 25** (for compatibility with the Hytale server)
- **JADX** (included in `/bin` or available on PATH)

### Initial command (first time)

The command to run when getting started is **`ctx init`** (or `context init`). It detects the Hytale JAR, decompiles, prunes, and indexes the API into SQLite. If the JAR is not detected, run **`ctx detect`** first so Orbis Prism can locate `HytaleServer.jar` and save the configuration to `.prism.json`.

### Where HytaleServer.jar is detected

- **Windows:** The official installation is used by default. Run `python main.py ctx detect` to detect it.
- **Manual path:** You only need the **game root folder** (not the JAR). Run `python main.py config_impl set game_path <path>` with that folder; Orbis Prism will automatically detect release and pre-release if they exist.
  - **How to get the path:** Open the **Hytale Launcher** → **Settings** → **Open Directory** → copy the path (e.g. `C:\Users\...\AppData\Roaming\Hytale`).

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/SamuelCastrillon/orbis-prism.git
   cd orbis-prism
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Run the initial command (detects JAR, decompiles, and indexes the API):

   ```bash
   python main.py ctx init
   ```

   **If the JAR is not found:**
   - Try `python main.py ctx detect` first (in case the installation is in an auto-detected path).
   - **To set the path manually:** use the game root folder (not the JAR). In the **Hytale Launcher** → **Settings** → **Open Directory**, copy that path and run:
     ```bash
     python main.py config_impl set game_path "C:\path\to\your\Hytale\folder"
     ```
     Then run `python main.py ctx init` again.

## 🛠 CLI commands

The recommended **initial** command is **`python main.py ctx init`** (or `context init`): it detects the JAR if needed, decompiles, prunes, and indexes. You can use `ctx` as a shorthand for `context`.

| Command | Description |
|--------|-------------|
| `python main.py ctx init [release\|prerelease\|--all]` | **Initial command.** Full pipeline: detects JAR if missing, decompiles (JADX), prunes, and indexes to SQLite. |
| `python main.py ctx detect` | Detects HytaleServer.jar (and release/prerelease if present) and saves configuration to `.prism.json`. |
| `python main.py ctx clean <db\|build\|all>` | Clean: `db` (databases only), `build` (decompiled output), `all` (everything). |
| `python main.py ctx reset` | Resets the project to zero (removes DB, build, and `.prism.json`). |
| `python main.py ctx decompile [release\|prerelease\|--all]` | JADX only → `workspace/decompiled_raw/<version>`. |
| `python main.py ctx prune [release\|prerelease\|--all]` | Prune: copies only `com.hypixel.hytale` from raw to decompiled. |
| `python main.py ctx db [release\|prerelease\|--all]` | Indexes the code into SQLite (FTS5). |
| `python main.py ctx list` | Lists indexed contexts (release/prerelease) and which is active (*). |
| `python main.py ctx use <release\|prerelease>` | Sets the active context. |
| `python main.py query <term> [release\|prerelease]` | Searches the indexed DB (FTS5). |
| `python main.py mcp [--http] [--port N] [--host DIR]` | Starts the MCP server. stdio by default; with `--http` exposes HTTP on the port (default 8000). |
| `python main.py lang list` | Lists available languages. |
| `python main.py lang set <code>` | Changes the language (e.g. `lang set en`). |
| `python main.py config_impl set game_path <path>` | Sets the game path (root folder or JAR). Launcher → Settings → Open Directory. |

For **detailed CLI documentation** (arguments, flows, code structure, and description of each subcommand), see [CLI documentation](src/prism/entrypoints/cli/README.md).

## 📁 Project structure

- **`/src`**: Source code of the orchestrator (Python).
- **`/workspace/decompiled/<version>`**: Clean Hytale core code per version (`release`, `prerelease`).
- **`/workspace/decompiled_raw/<version>`**: Raw JADX output before pruning.
- **`/workspace/db`**: SQLite databases per context (`prism_api_release.db`, `prism_api_prerelease.db`).
- **`/bin`**: Support binaries (JADX, etc.).

## 🔌 Configuring the MCP server

By default the server uses **stdio transport** (no port is opened). Your client (Cursor, Claude Desktop, etc.) runs the process and communicates via stdin/stdout. Optionally you can use **HTTP transport** for remote or Docker deployment.

### stdio mode (default)

1. **Run once** `python main.py mcp` in the project folder: if the output is a terminal, the command, arguments, and working directory will be shown.
2. **In Cursor** edit the MCP configuration (e.g. `~/.cursor/mcp.json`) and add a block like this (adjust paths):

   ```json
   "orbis-prism": {
     "type": "stdio",
     "command": "python",
     "args": ["C:\\absolute\\path\\to\\orbis-prism\\main.py", "mcp"],
     "cwd": "C:\\absolute\\path\\to\\orbis-prism",
     "env": {
       "PRISM_WORKSPACE": "C:\\absolute\\path\\to\\orbis-prism"
     }
   }
   ```

   - **cwd** is required so the server finds `.prism.json` and `workspace/db`.
   - **env.PRISM_WORKSPACE** (optional): if set, the server uses this path as the project root even when the process is started from another directory.
3. Reload the Cursor window (Ctrl+Shift+P → "Developer: Reload Window") so it picks up the `prism_search` tool.

### HTTP / Docker mode

> **Note:** This mode is under construction; the interface and behaviour may change.

To expose the server over the network (e.g. in a container):

- **CLI:** `python main.py mcp --http [--port 8000] [--host 0.0.0.0]`. By default it listens on `0.0.0.0:8000` (all interfaces).
- **Environment variables (optional):** `MCP_TRANSPORT=http` (or `streamable-http`), `MCP_PORT`, `MCP_HOST`. Command line takes precedence over the environment.

The MCP endpoint in HTTP mode is `http://<host>:<port>/mcp`. MCP clients that support Streamable HTTP can connect to that URL.

**Minimal Docker example:** build an image that installs dependencies and runs `python main.py mcp --http`, expose port 8000, and connect your client to `http://<container-ip>:8000/mcp`.

## 🤝 Contributing

If you want to contribute, see the [Contributing guide](CONTRIBUTING.md). For technical context and architecture (agents, development), see also [AGENTS.md](AGENTS.md).

## 📜 License

This project is licensed under the MIT License. See the `LICENSE` file for details.
