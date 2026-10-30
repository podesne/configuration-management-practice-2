"""Проверки рекурсивного BFS, фильтра и циклов."""

import json
from pathlib import Path
import tempfile
import unittest

from src.graph import build_graph, read_test_repository, test_loader


class GraphTests(unittest.TestCase):
    """Проверить графы разных форм и неправильные источники."""

    def test_level_order_and_shared_dependency(self):
        """Порядок вершин соответствует BFS, общая вершина одна."""
        source = {'A': ['B', 'C'], 'B': ['D'], 'C': ['D'], 'D': []}
        graph = build_graph('A', test_loader(source))
        self.assertEqual(list(graph), ['A', 'B', 'C', 'D'])
        self.assertEqual(graph, source)

    def test_cycles_self_reference_and_single_vertex(self):
        """Циклы сохраняются без бесконечного обхода."""
        for source in ({'A': []}, {'A': ['A']},
                       {'A': ['B'], 'B': ['A']}):
            self.assertEqual(build_graph('A', test_loader(source)), source)

    def test_filter_skips_branch_but_keeps_shared_node(self):
        """Отфильтрованная ветвь не мешает другому пути к вершине."""
        source = {'A': ['B', 'C'], 'B': ['D'], 'C': ['D'], 'D': []}
        graph = build_graph('A', test_loader(source), 'B')
        self.assertEqual(graph, {'A': ['C'], 'C': ['D'], 'D': []})
        with self.assertRaises(ValueError):
            build_graph('A', test_loader(source), 'A')

    def test_exclusions_are_path_specific(self):
        """Общая вершина обходится снова при других исключениях."""
        source = {
            'g:A:1': [('g:B:1', [('g', 'D')]), ('g:C:1', [])],
            'g:B:1': [('g:X:1', [])], 'g:C:1': [('g:X:1', [])],
            'g:X:1': [('g:D:1', [])], 'g:D:1': [],
        }
        graph = build_graph('g:A:1', lambda name, root: source[name])
        self.assertEqual(graph['g:X:1'], ['g:D:1'])

    def test_filtered_package_is_never_loaded(self):
        """Загрузчик не получает отфильтрованный пакет."""
        def load(name, root):
            """Считать ошибкой любой запрос исключённого пакета."""
            self.assertEqual(name, 'A')
            return [('B', [])]
        self.assertEqual(build_graph('A', load, 'B'), {'A': []})

    def test_invalid_json(self):
        """Неверные типы, имена и ссылки отклоняются."""
        cases = [[], {}, {'a': []}, {'A': 'B'}, {'A': ['B']},
                 {'A': [42]}, {'A': [{}]}]
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'graph.json'
            for data in cases:
                path.write_text(json.dumps(data))
                with self.assertRaises(ValueError):
                    read_test_repository(path)
            path.write_text('{')
            with self.assertRaises(ValueError):
                read_test_repository(path)

    def test_missing_start(self):
        """Начальный пакет должен присутствовать в JSON."""
        with self.assertRaises(ValueError):
            build_graph('B', test_loader({'A': []}))
