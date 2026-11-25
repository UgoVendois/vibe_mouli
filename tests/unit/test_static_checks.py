from vibe_mouli import static_checks


def test_parse_checker_report_format_prompt():
    text = "main.c:12: MAJOR:C-3 ligne trop longue\nfoo.h:1: INFO:C-9\nbruit sans format\n"
    items = static_checks.parse_checker_report(text)
    assert [(i.file, i.line, i.severity, i.code) for i in items] == [
        ("main.c", 12, "MAJOR", "C-3"),
        ("foo.h", 1, "INFO", "C-9"),
    ]


def test_local_style_check_flags_long_trailing_tab(tmp_path):
    (tmp_path / "a.c").write_text("x" * 81 + "\n" + "ok \n" + "\tint y;\n", encoding="utf-8")
    codes = sorted(i.code for i in static_checks.local_style_check(tmp_path))
    assert codes == ["LOCAL-LINE80", "LOCAL-TAB", "LOCAL-TRAILING"]


def test_local_style_check_ignores_non_c_files(tmp_path):
    (tmp_path / "Makefile").write_text("x" * 200 + "\n", encoding="utf-8")
    assert static_checks.local_style_check(tmp_path) == []


def test_forbidden_files(tmp_path):
    for name in ["a.o", "vgcore.123", "main.c~", "#main.c#", "ok.c"]:
        (tmp_path / name).write_text("", encoding="utf-8")
    assert static_checks.forbidden_files(tmp_path) == ["#main.c#", "a.o", "main.c~", "vgcore.123"]
