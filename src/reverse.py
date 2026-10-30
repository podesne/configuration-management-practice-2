"""Обратные зависимости известного графа."""

from .graph import build_graph, filtered, test_loader


def reverse_graph(graph, substring=""):
    """Развернуть все связи, предварительно исключив пакеты по фильтру."""
    result = {name: [] for name in graph if not filtered(name, substring)}
    for name, dependencies in graph.items():
        if name not in result:
            continue
        for dependency in dependencies:
            if dependency in result and name not in result[dependency]:
                result[dependency].append(name)
    return result


def reverse_dependencies(graph, start, substring=""):
    """Найти прямые и косвенные обратные зависимости рекурсивным BFS."""
    reverse = reverse_graph(graph, substring)
    visited = build_graph(start, test_loader(reverse), substring)
    return [name for name in visited if name != start]
