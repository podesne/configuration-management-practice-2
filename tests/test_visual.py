"""Проверки текстовых представлений и запуска Mermaid CLI."""

from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from src.visual import ascii_tree, mermaid_text, save_image


class VisualTests(unittest.TestCase):
    """Проверить структуру графа и ошибки средства отрисовки."""

    def test_mermaid_includes_edges_and_isolated_nodes(self):
        """Текст содержит каждую вершину и оба ребра цикла."""
        result = mermaid_text({'A': ['B'], 'B': ['A'], 'C': []})
        self.assertIn('n2["C"]', result)
        self.assertIn('n0 --> n1', result)
        self.assertIn('n1 --> n0', result)

    def test_tree_marks_cycles_and_shared_nodes(self):
        """Дерево останавливается на цикле и повторной зависимости."""
        graph = {'A': ['B', 'C'], 'B': ['D'], 'C': ['D'], 'D': ['A']}
        result = ascii_tree(graph, 'A')
        self.assertIn('A [цикл]', result)
        self.assertIn('D [повтор]', result)
        self.assertIn('|', result)

    def test_missing_renderer_preserves_source(self):
        """Без mmdc остаётся файл Mermaid и понятная ошибка."""
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'new' / 'a.png'
            with patch('src.visual.shutil.which', return_value=None):
                with self.assertRaisesRegex(ValueError, 'npm install'):
                    save_image({'A': []}, path)
            self.assertTrue(path.with_suffix('.mmd').exists())

    def test_render_failure_and_timeout(self):
        """Ошибка процесса и тайм-аут не объявляются успешным рендером."""
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'a.png'
            result = subprocess.CompletedProcess([], 1, '', 'bad')
            with patch('src.visual.shutil.which', return_value='mmdc'):
                with patch('src.visual.subprocess.run', return_value=result):
                    with self.assertRaisesRegex(ValueError, 'bad'):
                        save_image({'A': []}, path)
                error = subprocess.TimeoutExpired('mmdc', 120)
                with patch('src.visual.subprocess.run', side_effect=error):
                    with self.assertRaises(ValueError):
                        save_image({'A': []}, path)
