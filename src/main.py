"""Запуск второго этапа."""

import sys

from .config import parse_config
from .maven import MavenRepository


def main(arguments=None):
    """Показать прямые зависимости и вернуть код завершения."""
    try:
        config = parse_config(arguments)
        if config.test:
            raise ValueError("Тестовый JSON доступен с третьего этапа")
        repository = MavenRepository(config.repo)
        for package, _ in repository.dependencies(config.package, root=True):
            print(package)
        return 0
    except (ValueError, OSError) as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
