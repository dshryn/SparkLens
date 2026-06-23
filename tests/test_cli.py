from pathlib import Path

from cli.main import main


def test_cli_import():
    assert main is not None