"""Рекурсивный обход графа в ширину и тестовый источник."""

import json
from pathlib import Path
import re


def read_test_repository(path):
    """Прочитать JSON со списками связей и проверить все вершины."""
    try:
        graph = json.loads(Path(path).read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeError) as error:
        raise ValueError(f"Повреждённый тестовый JSON: {error}") from error
    if not isinstance(graph, dict) or not graph:
        raise ValueError("Тестовый репозиторий должен быть непустым объектом")
    for package, dependencies in graph.items():
        if not re.fullmatch(r"[A-Z]+", package):
            raise ValueError("Имена тестовых пакетов должны содержать A-Z")
        if not isinstance(dependencies, list):
            raise ValueError(f"Зависимости {package} должны быть списком")
        for name in dependencies:
            if not isinstance(name, str) or name not in graph:
                raise ValueError(f"Неизвестная зависимость пакета {package}")
    return graph


def filtered(package, substring):
    """Проверить подстроку в имени пакета с учётом регистра."""
    name = package.split(":")[1] if ":" in package else package
    return bool(substring and substring in name)


def excluded(package, exclusions):
    """Проверить координаты по парам groupId и artifactId, включая *."""
    parts = package.split(":")
    if len(parts) == 1:
        return False
    return any(group in ("*", parts[0]) and name in ("*", parts[1])
               for group, name in exclusions)


def build_graph(start, loader, substring=""):
    """Построить достижимый граф рекурсивным BFS по уровням."""
    if filtered(start, substring):
        raise ValueError("Фильтр исключает начальный пакет")
    graph = {}
    visited = set()
    visit_level([(start, frozenset())], loader, substring, graph, visited,
                start)
    return graph


def visit_level(level, loader, substring, graph, visited, start):
    """Обработать один уровень и рекурсивно перейти к следующему."""
    if not level:
        return
    following = []
    for package, exclusions in level:
        state = (package, exclusions)
        if state in visited:
            continue
        visited.add(state)
        graph.setdefault(package, [])
        for name, own_exclusions in loader(package, package == start):
            if filtered(name, substring) or excluded(name, exclusions):
                continue
            if name not in graph[package]:
                graph[package].append(name)
            blocked = exclusions | frozenset(own_exclusions)
            following.append((name, blocked))
    visit_level(following, loader, substring, graph, visited, start)


def test_loader(graph):
    """Сделать загрузчик JSON с тем же интерфейсом, что у Maven."""
    def load(package, root=False):
        """Вернуть зависимости пакета, сохранив порядок JSON."""
        if package not in graph:
            raise ValueError(f"Пакет {package} отсутствует в репозитории")
        return [(name, []) for name in graph[package]]
    return load


def print_graph(graph):
    """Вывести каждую вершину и список прямых зависимостей."""
    for package, dependencies in graph.items():
        print(f"{package}: {', '.join(dependencies) or '(нет)'}")
