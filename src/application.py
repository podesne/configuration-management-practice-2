"""Выбор реального или тестового источника графа."""

from .graph import build_graph, read_test_repository, test_loader
from .maven import MavenRepository


def load_graph(config):
    """Получить граф из JSON или Maven по параметрам запуска."""
    if config.test:
        source = read_test_repository(config.repo)
        loader = test_loader(source)
    else:
        loader = MavenRepository(config.repo).dependencies
    return build_graph(config.package, loader, config.filter)
