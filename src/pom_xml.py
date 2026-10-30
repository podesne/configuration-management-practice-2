"""Чтение XML и подстановка свойств POM."""

import re
import xml.etree.ElementTree as ET

PROPERTY = re.compile(r"\$\{([^}]+)\}")


def parse_xml(data):
    """Разобрать байты POM и удалить пространства имён из тегов."""
    if b"<!DOCTYPE" in data.upper() or b"<!ENTITY" in data.upper():
        raise ValueError("Объявления DTD и сущностей в POM не поддерживаются")
    try:
        root = ET.fromstring(data)
    except ET.ParseError as error:
        raise ValueError(f"Повреждённый XML: {error}") from error
    for node in root.iter():
        node.tag = node.tag.split("}")[-1]
    if root.tag != "project":
        raise ValueError("Корневой элемент POM должен быть project")
    return root


def text(node, path, default=""):
    """Вернуть текст дочернего элемента или значение по умолчанию."""
    child = node.find(path)
    return default if child is None else (child.text or "").strip()


def expand(value, properties):
    """Подставить свойства; циклы и неизвестные имена считать ошибкой."""
    seen = set()
    while PROPERTY.search(value):
        if value in seen:
            raise ValueError(f"Цикл свойств POM: {value}")
        seen.add(value)
        value = PROPERTY.sub(lambda match: property_value(match, properties),
                             value)
    return value


def property_value(match, properties):
    """Получить свойство по найденному имени или сообщить об ошибке."""
    name = match.group(1)
    if name not in properties:
        raise ValueError(f"Неизвестное свойство POM: {name}")
    return properties[name]


def read_dependencies(root, path):
    """Прочитать записи зависимостей вместе с областями и исключениями."""
    result = []
    for node in root.findall(path):
        item = {}
        for key in ("groupId", "artifactId", "version", "scope", "type",
                    "classifier", "optional"):
            item[key] = text(node, key)
        item["exclusions"] = [
            (text(ex, "groupId"), text(ex, "artifactId"))
            for ex in node.findall("exclusions/exclusion")
        ]
        result.append(item)
    return result


def dependency_key(item, properties):
    """Вернуть ключ зависимости, учитывая тип и classifier."""
    return tuple(expand(item.get(key, "") or ("jar" if key == "type" else ""),
                        properties) for key in
                 ("groupId", "artifactId", "type", "classifier"))


def merge_dependencies(inherited, own, properties):
    """Объединить зависимости; собственная запись заменяет родительскую."""
    result = {}
    for item in inherited + own:
        result[dependency_key(item, properties)] = item
    return list(result.values())
