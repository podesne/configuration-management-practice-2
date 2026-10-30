"""Загрузка POM без менеджеров пакетов и сторонних библиотек."""

from urllib.error import HTTPError, URLError
from urllib.request import urlopen

from .config import check_package
from .pom_xml import (expand, merge_dependencies, parse_xml,
                      read_dependencies, text)

TIMEOUT = 20
SCOPES = ("compile", "runtime")


class MavenRepository:
    """Хранить адрес репозитория и уже разобранные документы."""

    def __init__(self, url, download=None):
        """Задать базовый URL и необязательную функцию скачивания для тестов."""
        self.url = url.rstrip("/")
        self.download = download or download_pom
        self.cache = {}
        self.loading = set()

    def load(self, package):
        """Получить модель POM, обнаруживая циклы родителей и BOM."""
        if package in self.cache:
            return self.cache[package]
        if package in self.loading:
            raise ValueError(f"Цикл родителей или BOM: {package}")
        self.loading.add(package)
        try:
            root = parse_xml(self.download(pom_url(self.url, package)))
            model = self.make_model(root, package)
            self.cache[package] = model
            return model
        finally:
            self.loading.remove(package)

    def make_model(self, root, package):
        """Собрать свойства, управляемые версии и зависимости с родителем."""
        own = {node.tag: (node.text or "").strip()
               for node in root.findall("properties/*")}
        parent = self.parent_model(root, own)
        properties = dict(parent.get("properties", {}))
        properties.update(own)
        properties.update(project_properties(root, package))
        managed = dict(parent.get("managed", {}))
        entries = read_dependencies(root, "dependencyManagement/dependencies/"
                                    "dependency")
        self.import_boms(entries, properties, managed)
        for item in entries:
            if expand(item["scope"], properties) != "import":
                managed[managed_key(item, properties)] = item
        dependencies = merge_dependencies(
            parent.get("dependencies", []),
            read_dependencies(root, "dependencies/dependency"), properties)
        return {"properties": properties, "managed": managed,
                "dependencies": dependencies}

    def parent_model(self, root, properties):
        """Загрузить родительский POM, если он указан."""
        parent = root.find("parent")
        if parent is None:
            return {}
        package = ":".join(expand(text(parent, key), properties)
                           for key in ("groupId", "artifactId", "version"))
        return self.load(package)

    def import_boms(self, entries, properties, managed):
        """Добавить управляемые версии из BOM с сохранением их свойств."""
        imported = {}
        for item in entries:
            if expand(item["scope"], properties) != "import":
                continue
            package = coordinates(item, properties)
            bom = self.load(package)
            for key, entry in bom["managed"].items():
                resolved = resolve_entry(entry, bom["properties"])
                imported.setdefault(key, resolved)
        managed.update(imported)

    def dependencies(self, package, root=False):
        """Вернуть рабочие зависимости с точными версиями и exclusions."""
        model = self.load(package)
        result = []
        for item in model["dependencies"]:
            entry = effective_dependency(item, model)
            if entry["scope"] not in SCOPES:
                continue
            if entry["optional"] == "true" and not root:
                continue
            result.append((coordinates(entry, {}), entry["exclusions"]))
        return result


def pom_url(base, package):
    """Построить адрес POM по трём частям координат."""
    group, artifact, version = check_package(package)
    path = f"{group.replace('.', '/')}/{artifact}/{version}"
    return f"{base}/{path}/{artifact}-{version}.pom"


def download_pom(url):
    """Скачать POM с ограниченным временем ожидания."""
    try:
        with urlopen(url, timeout=TIMEOUT) as response:
            return response.read()
    except HTTPError as error:
        raise ValueError(f"HTTP {error.code}: {url}") from error
    except (URLError, TimeoutError, OSError) as error:
        raise ValueError(f"Не удалось загрузить {url}: {error}") from error


def project_properties(root, package):
    """Собрать встроенные имена project, pom и parent."""
    result = {}
    for key, value in zip(("groupId", "artifactId", "version"),
                          check_package(package)):
        for prefix in ("project", "pom"):
            result[f"{prefix}.{key}"] = value
        result[key] = value
        parent = text(root, f"parent/{key}")
        if parent:
            result[f"project.parent.{key}"] = parent
            result[f"parent.{key}"] = parent
    return result


def managed_key(item, properties):
    """Получить ключ управляемой версии зависимости."""
    return tuple(expand(item.get(key, ""), properties) or default
                 for key, default in (("groupId", ""), ("artifactId", ""),
                                      ("type", "jar"), ("classifier", "")))


def resolve_entry(item, properties):
    """Раскрыть поля записи и пары исключений."""
    result = {key: expand(value, properties) for key, value in item.items()
              if key != "exclusions"}
    result["exclusions"] = [
        tuple(expand(value, properties) for value in pair)
        for pair in item.get("exclusions", [])
    ]
    return result


def effective_dependency(item, model):
    """Применить управляемые значения и раскрыть свойства зависимости."""
    properties = model["properties"]
    key = managed_key(item, properties)
    inherited = model["managed"].get(key, {})
    merged = dict(inherited)
    merged.update({key: value for key, value in item.items() if value})
    merged["exclusions"] = list(inherited.get("exclusions", []))
    merged["exclusions"] += item.get("exclusions", [])
    merged.setdefault("optional", "false")
    merged.setdefault("scope", "compile")
    merged["scope"] = merged["scope"] or "compile"
    return resolve_entry(merged, properties)


def coordinates(item, properties):
    """Получить точные координаты, отвергая отсутствующую версию."""
    values = [expand(item.get(key, ""), properties)
              for key in ("groupId", "artifactId", "version")]
    package = ":".join(values)
    check_package(package)
    return package
