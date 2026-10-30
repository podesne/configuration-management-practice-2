"""Mermaid, PNG и ASCII-дерево графа."""

from pathlib import Path
import shutil
import subprocess

RENDER_TIMEOUT = 120


def mermaid_text(graph):
    """Вернуть Mermaid с отдельными идентификаторами и безопасными метками."""
    names = {name: f"n{index}" for index, name in enumerate(graph)}
    lines = ["flowchart TD"]
    for name, identifier in names.items():
        label = name.replace('"', '#quot;').replace('<', '&lt;')
        label = label.replace('>', '&gt;')
        lines.append(f'    {identifier}["{label}"]')
    for name, dependencies in graph.items():
        for dependency in dependencies:
            lines.append(f"    {names[name]} --> {names[dependency]}")
    return "\n".join(lines) + "\n"


def save_image(graph, output):
    """Записать Mermaid и вызвать локальный mmdc для создания PNG."""
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    source = path.with_suffix(".mmd")
    source.write_text(mermaid_text(graph), encoding="utf-8")
    renderer = shutil.which("mmdc")
    if renderer is None:
        raise ValueError("Нужен Mermaid CLI: npm install -g "
                         "@mermaid-js/mermaid-cli")
    command = [renderer, "-i", str(source), "-o", str(path), "-b", "white"]
    try:
        result = subprocess.run(command, capture_output=True, text=True,
                                timeout=RENDER_TIMEOUT, check=False)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise ValueError(f"Ошибка запуска Mermaid CLI: {error}") from error
    if result.returncode:
        raise ValueError(f"Ошибка Mermaid CLI: {result.stderr.strip()}")
    if not path.is_file() or not path.read_bytes().startswith(b'\x89PNG\r\n'):
        raise ValueError("Mermaid CLI не создал PNG-файл")
    return source, path


def ascii_tree(graph, start):
    """Вернуть ASCII-дерево с отметками циклов и повторных вершин."""
    lines = [start]
    tree_lines(graph, start, "", {start}, {start}, lines)
    return "\n".join(lines)


def tree_lines(graph, name, prefix, path, seen, lines):
    """Добавить ветви дерева, не разворачивая циклы и повторы."""
    children = graph[name]
    for index, child in enumerate(children):
        last = index == len(children) - 1
        branch = "+-- "
        marker = ""
        if child in path:
            marker = " [цикл]"
        elif child in seen:
            marker = " [повтор]"
        lines.append(prefix + branch + child + marker)
        if not marker:
            seen.add(child)
            continuation = "    " if last else "|   "
            tree_lines(graph, child, prefix + continuation, path | {child},
                       seen, lines)
