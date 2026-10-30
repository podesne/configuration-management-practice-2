"""Запуск третьего этапа."""

import sys

from .application import load_graph
from .config import parse_config
from .graph import print_graph


def main(arguments=None):
    """Построить граф, вывести связи и вернуть код завершения."""
    try:
        config = parse_config(arguments)
        print_graph(load_graph(config))
        return 0
    except (ValueError, OSError, RecursionError) as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
