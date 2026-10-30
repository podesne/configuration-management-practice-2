"""Проверки параметров и ошибок запуска."""

import contextlib
import io
from pathlib import Path
import tempfile
import unittest

from src.config import CENTRAL, parse_config
from src.main import main

PACKAGE = "org.apache.commons:commons-text:1.12.0"


class ConfigTests(unittest.TestCase):
    """Проверить значения по умолчанию и неправильные аргументы."""

    def test_defaults(self):
        """Без дополнительных опций доступны значения по умолчанию."""
        config = parse_config(["--package", PACKAGE])
        self.assertEqual(config.repo, CENTRAL)
        self.assertEqual(config.output, "output/graph.png")
        self.assertFalse(config.test)
        self.assertFalse(config.ascii)
        self.assertEqual(config.filter, "")

    def test_all_options(self):
        """Все шесть параметров доступны в тестовом режиме."""
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "repo.json"
            path.write_text('{"A": []}')
            config = parse_config([
                "--package", "A", "--repo", str(path), "--test",
                "--ascii", "--output", "a.png", "--filter", "B",
            ])
            self.assertTrue(config.test)
            self.assertTrue(config.ascii)
            self.assertEqual(config.filter, "B")

    def test_invalid_values(self):
        """Ошибки значений не принимаются как рабочая конфигурация."""
        cases = [
            ["--package", "bad"],
            ["--package", "g:a:[1,2)"],
            ["--package", PACKAGE, "--repo", "ftp://host/repo"],
            ["--package", PACKAGE, "--output", "a.jpg"],
            ["--package", PACKAGE, "--filter", "commons"],
            ["--package", "A", "--test", "--repo", "absent.json"],
        ]
        for arguments in cases:
            with self.subTest(arguments=arguments):
                with self.assertRaises(ValueError):
                    parse_config(arguments)

    def test_boolean_and_missing_options(self):
        """Пропуск обязательных значений и значения флагов дают ошибку."""
        cases = [[], ["--package"], ["--package", PACKAGE, "--ascii", "x"],
                 ["--package", PACKAGE, "--test", "false"],
                 ["--package", PACKAGE, "--output"],
                 ["--package", PACKAGE, "--filter"],
                 ["--package", PACKAGE, "--repo"]]
        for arguments in cases:
            with contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit):
                    parse_config(arguments)

    def test_main_error(self):
        """Ошибка значения возвращает ненулевой код без traceback."""
        with contextlib.redirect_stderr(io.StringIO()) as output:
            self.assertEqual(main(["--package", "bad"]), 1)
        self.assertIn("Ошибка", output.getvalue())
