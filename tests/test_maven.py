"""Проверки POM без подключения к сети."""

from urllib.error import HTTPError, URLError
import unittest
from unittest.mock import patch

from src.maven import MavenRepository, download_pom, pom_url
from src.pom_xml import expand, parse_xml


def pom(body):
    """Добавить XML-корень к содержимому тестового POM."""
    return ('<project xmlns="http://maven.apache.org/POM/4.0.0">'
            + body + '</project>').encode()


def dependency(name, version="1", extra=""):
    """Составить XML-зависимость с заданными полями."""
    value = f'<version>{version}</version>' if version else ''
    return (f'<dependency><groupId>g</groupId><artifactId>{name}'
            f'</artifactId>{value}{extra}</dependency>')


def repository(files):
    """Создать репозиторий с подставной загрузкой документов."""
    def download(url):
        """Вернуть POM из словаря по полному адресу."""
        return files[url]
    return MavenRepository("https://test", download)


class MavenTests(unittest.TestCase):
    """Проверить наследование, области и ошибки документов."""

    def test_direct_scopes_optional_and_cache(self):
        """Начальный пакет включает optional, транзитивный его пропускает."""
        body = '<dependencies>' + dependency('a')
        body += dependency('test', extra='<scope>test</scope>')
        body += dependency('opt', extra='<optional>true</optional>')
        body += '</dependencies>'
        repo = repository({pom_url('https://test', 'g:root:1'): pom(body)})
        self.assertEqual([p for p, _ in repo.dependencies('g:root:1', True)],
                         ['g:a:1', 'g:opt:1'])
        self.assertEqual(repo.dependencies('g:root:1'), [('g:a:1', [])])
        self.assertEqual(len(repo.cache), 1)

    def test_parent_properties_and_managed_version(self):
        """Родитель даёт свойства, зависимости и управляемую версию."""
        parent = '<properties><v>2</v></properties><dependencyManagement>'
        parent += '<dependencies>' + dependency('a', '${v}')
        parent += '</dependencies></dependencyManagement><dependencies>'
        parent += dependency('base') + '</dependencies>'
        child = ('<parent><groupId>g</groupId><artifactId>parent</artifactId>'
                 '<version>1</version></parent><properties><v>3</v>'
                 '</properties><dependencies>')
        child += dependency('a', '') + '</dependencies>'
        files = {pom_url('https://test', 'g:parent:1'): pom(parent),
                 pom_url('https://test', 'g:child:1'): pom(child)}
        self.assertEqual(repository(files).dependencies('g:child:1'),
                         [('g:base:1', []), ('g:a:3', [])])

    def test_bom_properties_are_resolved_in_bom(self):
        """Свойство импортируемой версии раскрывается в контексте BOM."""
        bom = '<properties><v>7</v></properties><dependencyManagement>'
        bom += '<dependencies>' + dependency('a', '${v}')
        bom += '</dependencies></dependencyManagement>'
        root = '<dependencyManagement><dependencies>'
        root += dependency('bom', extra='<scope>import</scope><type>pom</type>')
        root += '</dependencies></dependencyManagement><dependencies>'
        root += dependency('a', '') + '</dependencies>'
        files = {pom_url('https://test', 'g:bom:1'): pom(bom),
                 pom_url('https://test', 'g:root:1'): pom(root)}
        self.assertEqual(repository(files).dependencies('g:root:1'),
                         [('g:a:7', [])])

    def test_invalid_versions_properties_and_xml(self):
        """Отсутствующие и неточные версии не превращаются в вершины."""
        for version in ('', '[1,2)', '${missing}'):
            body = '<dependencies>' + dependency('a', version)
            body += '</dependencies>'
            repo = repository({pom_url('https://test', 'g:r:1'): pom(body)})
            with self.assertRaises(ValueError):
                repo.dependencies('g:r:1')
        for xml in (b'<bad>', b'<other/>', b'<!DOCTYPE x><project/>'):
            with self.assertRaises(ValueError):
                parse_xml(xml)
        with self.assertRaises(ValueError):
            expand('${a}', {'a': '${b}', 'b': '${a}'})

    def test_parent_cycle(self):
        """Цикл родителей останавливается до переполнения стека."""
        body = ('<parent><groupId>g</groupId><artifactId>r</artifactId>'
                '<version>1</version></parent>')
        repo = repository({pom_url('https://test', 'g:r:1'): pom(body)})
        with self.assertRaisesRegex(ValueError, 'Цикл'):
            repo.load('g:r:1')

    def test_network_errors(self):
        """HTTP, недоступность сервера и тайм-аут дают понятную ошибку."""
        errors = [HTTPError('url', 404, 'missing', {}, None),
                  URLError('offline'), TimeoutError('timeout')]
        for error in errors:
            with patch('src.maven.urlopen', side_effect=error):
                with self.assertRaises(ValueError):
                    download_pom('https://test/a.pom')
