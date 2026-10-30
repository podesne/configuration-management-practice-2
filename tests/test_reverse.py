"""Проверки обратных зависимостей."""

import unittest

from src.reverse import reverse_dependencies


class ReverseTests(unittest.TestCase):
    """Проверить прямые, косвенные связи, циклы и фильтр."""

    def test_reverse_bfs(self):
        """Обход возвращает потребителей по уровням без повторов."""
        graph = {'A': [], 'B': ['A'], 'C': ['A'],
                 'D': ['B', 'C'], 'E': ['D']}
        self.assertEqual(reverse_dependencies(graph, 'A'),
                         ['B', 'C', 'D', 'E'])

    def test_cycles_and_self(self):
        """Исходная вершина не входит в ответ даже при цикле."""
        self.assertEqual(reverse_dependencies({'A': ['A']}, 'A'), [])
        graph = {'A': ['B'], 'B': ['A'], 'C': ['B']}
        self.assertEqual(reverse_dependencies(graph, 'A'), ['B', 'C'])

    def test_filter(self):
        """Фильтр исключает потребителей и недоступные через них вершины."""
        graph = {'A': [], 'B': ['A'], 'C': ['B']}
        self.assertEqual(reverse_dependencies(graph, 'A', 'B'), [])

    def test_no_reverse(self):
        """Отсутствие потребителей даёт пустой список."""
        self.assertEqual(reverse_dependencies({'A': []}, 'A'), [])
