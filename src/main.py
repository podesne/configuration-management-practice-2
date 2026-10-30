"""Запуск четвёртого этапа."""

import sys

from .application import load_reverse_source
from .config import parse_config
from .reverse import reverse_dependencies


def main(arguments=None):
    """Вывести обратные зависимости и вернуть код завершения."""
    try:
        config = parse_config(arguments)
        graph = load_reverse_source(config)
        packages = reverse_dependencies(graph, config.package, config.filter)
        print("\n".join(packages) or "Обратных зависимостей нет")
        return 0
    except (ValueError, OSError, RecursionError) as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
