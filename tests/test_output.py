"""Tests for moosecontainers.output."""

from moosecontainers import output


def test_in_github_action(monkeypatch):
    """Detect being in a GitHub action."""
    assert not output.in_github_action()
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    assert output.in_github_action()


def test_print_section(capsys):
    """Print a section outside of a GitHub action."""
    output.print_section("Title", "contents")
    output.print_section("List", ["a", "b"])
    assert capsys.readouterr().out == (
        "-- Title\n\ncontents\n\n-- List\n\na\nb\n\n"
    )


def test_print_section_github(github_action, capsys):
    """Print a section in a GitHub action."""
    output.print_section("Title", "contents")
    assert capsys.readouterr().out == (
        "::group::Title\ncontents\n::endgroup::\n"
    )


def test_build_summary_table(capsys):
    """Build a summary table outside of a GitHub action."""
    result = output.build_summary_table("T", [("a", "b")], ["x", "y"], "none")
    assert result == "## T\n\n| x   | y   |\n|-----|-----|\n| a   | b   |"
    assert "-- T summary" in capsys.readouterr().out


def test_build_summary_table_empty():
    """Build a summary table without rows."""
    result = output.build_summary_table("T", [], ["x"], "none")
    assert result == "## T\n\nnone"


def test_build_summary_table_github(github_action):
    """Build a summary table in a GitHub action, appending to the summary."""
    _, summary = github_action
    summary.write_text("before\n")
    result = output.build_summary_table("T", [], ["x"], "none")
    assert result == "## T\n\nnone\n\n"
    assert summary.read_text() == "before\n## T\n\nnone\n\n"


def test_write_outputs(capsys):
    """Write outputs outside of a GitHub action."""
    output.write_outputs({"a": "1", "b": "2"})
    assert capsys.readouterr().out == "-- Output\n\na=1\nb=2\n\n"


def test_write_outputs_github(github_action):
    """Write outputs in a GitHub action, appending to the output file."""
    outputs, _ = github_action
    outputs.write_text("before=0\n")
    output.write_outputs({"a": "1"})
    assert outputs.read_text() == "before=0\na=1\n"
