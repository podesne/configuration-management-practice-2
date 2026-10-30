"""Запуск пятого этапа."""

import sys

from .application import load_graph
from .config import parse_config
from .visual import ascii_tree, save_image


def main(arguments=None):
    """Сохранить граф, при необходимости вывести дерево, вернуть код выхода."""
    try:
        config = parse_config(arguments)
        graph = load_graph(config)
        if config.ascii:
            print(ascii_tree(graph, config.package))
        source, image = save_image(graph, config.output)
        print(f"Mermaid: {source}\nPNG: {image}")
        return 0
    except (ValueError, OSError, RecursionError) as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
