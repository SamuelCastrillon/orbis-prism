# Ayuda del CLI.

from ... import i18n


def print_help() -> None:
    w = 38
    fmt = "  {:<" + str(w) + "}"
    print(i18n.t("cli.help.title"))
    print()
    print(i18n.t("cli.help.usage"))
    print()
    print(i18n.t("cli.help.commands"))
    print(fmt.format("context | ctx init [release|prerelease|--all|-a]") + i18n.t("cli.help.context_init_desc"))
    print(fmt.format("context | ctx detect") + i18n.t("cli.help.context_detect_desc"))
    print(fmt.format("context | ctx clean <db|build|all>") + i18n.t("cli.help.context_clean_desc"))
    print(fmt.format("context | ctx reset") + i18n.t("cli.help.context_reset_desc"))
    print(fmt.format("context | ctx decompile [release|prerelease|--all|-a]") + i18n.t("cli.help.context_decompile_desc"))
    print(fmt.format("context | ctx prune [release|prerelease|--all|-a]") + i18n.t("cli.help.context_prune_desc"))
    print(fmt.format("context | ctx db [release|prerelease|--all|-a]") + i18n.t("cli.help.context_db_desc"))
    print(fmt.format("context | ctx list") + i18n.t("cli.help.context_list_desc"))
    print(fmt.format("context | ctx use <release|prerelease>") + i18n.t("cli.help.context_use_desc"))
    print()
    print(fmt.format("query [--json|-j] [--limit N] <término> [release|prerelease]") + i18n.t("cli.help.query_desc"))
    print(fmt.format("mcp") + i18n.t("cli.help.mcp_desc"))
    print()
    print(fmt.format("lang list") + i18n.t("cli.help.lang_list_desc"))
    print(fmt.format("lang set <código>") + i18n.t("cli.help.lang_set_desc"))
    print()
    print(fmt.format("config_impl set game_path <ruta>") + i18n.t("cli.help.config_set_jar_desc"))
    print(fmt.format("") + i18n.t("cli.help.config_set_jar_hint"))
    print()
    print(i18n.t("cli.help.example"))
