"""Запуск первого этапа."""

import sys

from .config import parse_config, print_config


def main(arguments=None):
    """Проверить параметры, показать значения и вернуть код завершения."""
    try:
        config = parse_config(arguments)
        print_config(config)
        return 0
    except (ValueError, OSError) as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
