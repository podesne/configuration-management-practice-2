"""Параметры командной строки."""

import argparse
from pathlib import Path
import re
from urllib.parse import urlparse

CENTRAL = "https://repo.maven.apache.org/maven2"
PARTS_COUNT = 3
COORDINATE = r"[A-Za-z0-9_][A-Za-z0-9_.-]*"


def check_package(package):
    """Проверить точные координаты и вернуть их части."""
    parts = package.split(":")
    if len(parts) != PARTS_COUNT:
        raise ValueError("Пакет задаётся как groupId:artifactId:version")
    if not all(re.fullmatch(COORDINATE, part) for part in parts):
        raise ValueError("Нужны точные координаты без диапазонов версий")
    if any(part in (".", "..") for part in parts):
        raise ValueError("Недопустимые координаты пакета")
    return parts


def parse_config(arguments=None):
    """Получить параметры из списка или из командной строки процесса."""
    parser = argparse.ArgumentParser(description="Граф зависимостей Maven")
    parser.add_argument("--package", required=True, help="координаты пакета")
    parser.add_argument("--repo", default=CENTRAL, help="репозиторий или JSON")
    parser.add_argument("--test", action="store_true", help="читать JSON")
    parser.add_argument("--output", default="output/graph.png", help="PNG")
    parser.add_argument("--ascii", action="store_true", help="ASCII-дерево")
    parser.add_argument("--filter", default="", help="исключаемая подстрока")
    config = parser.parse_args(arguments)
    validate_config(config)
    return config


def validate_config(config):
    """Проверить совместимость и значения всех шести параметров."""
    if config.test:
        validate_test(config)
    else:
        check_package(config.package)
        validate_url(config.repo)
    output = Path(config.output)
    if output.suffix.lower() != ".png" or output.is_dir():
        raise ValueError("Выходной файл должен иметь расширение .png")
    name = config.package if config.test else config.package.split(":")[1]
    if config.filter and config.filter in name:
        raise ValueError("Фильтр исключает начальный пакет")


def print_config(config):
    """Напечатать все параметры в формате ключ-значение."""
    for key, value in vars(config).items():
        print(f"{key}: {value}")


def validate_test(config):
    """Проверить имя пакета и наличие файла в тестовом режиме."""
    if not re.fullmatch(r"[A-Z]+", config.package):
        raise ValueError("В тестовом режиме нужны большие буквы A-Z")
    if not Path(config.repo).is_file():
        raise ValueError("Файл тестового репозитория не найден")


def validate_url(address):
    """Проверить базовый HTTP-адрес без авторизации и параметров."""
    url = urlparse(address)
    if url.scheme not in ("http", "https") or not url.hostname:
        raise ValueError("Адрес репозитория должен быть HTTP или HTTPS")
    if url.query or url.fragment or url.username or url.password:
        raise ValueError("Нужен базовый URL без параметров и авторизации")
