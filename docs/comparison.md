# Сравнение с Maven

Проверка выполнена 30 октября 2026 года. Использованы Apache Maven 3.9.9
и Maven Dependency Plugin 3.8.1. Команда `dependency:tree` запущена с
`-Dscope=runtime`, поэтому сравниваются области `compile` и `runtime`.

## Повторение проверки

Нужны установленный Maven и доступ к Maven Central.

```sh
sh scripts/compare_maven.sh
sh scripts/render_examples.sh
```

Проверочные POM находятся в `examples/comparison`.
Maven используется только в этом отдельном сценарии сравнения.
Основная программа сама читает POM и строит граф.

## Результаты

### commons-text

Вывод Maven:

```text
practice:comparison-commons-text:jar:1.0
\- org.apache.commons:commons-text:jar:1.12.0:compile
   \- org.apache.commons:commons-lang3:jar:3.14.0:compile
```

Программа нашла Commons Text 1.12.0 и его зависимость Commons Lang 3.14.0.
Набор пакетов и связь совпали с Maven.

### commons-io

Вывод Maven:

```text
practice:comparison-commons-io:jar:1.0
\- commons-io:commons-io:jar:2.16.1:compile
```

У выбранной версии нет зависимостей в сравниваемых областях.
Программа построила граф из одной вершины. Результат совпал с Maven.

### commons-codec

Вывод Maven:

```text
practice:comparison-commons-codec:jar:1.0
\- commons-codec:commons-codec:jar:1.17.1:compile
```

У выбранной версии нет зависимостей в сравниваемых областях.
Программа построила граф из одной вершины. Результат совпал с Maven.

## Различия представлений

В выводе Maven первая вершина `practice:comparison-...` принадлежит
проверочному проекту. Она нужна для запуска Maven и не входит в граф
анализируемого пакета. Maven показывает тип `jar` и область `compile`;
программа подписывает вершины координатами без этих полей.

В трёх проверенных примерах различий в зависимостях нет. Для других
пакетов результат может отличаться: программа сохраняет разные версии
одного артефакта отдельными вершинами, а Maven разрешает конфликты версий.
Автоматическая активация профилей в программе не реализована.
