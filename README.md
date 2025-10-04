<h1>Проект: Виртуальная файловая система и эмулятор терминала</h1>

<p><b>Общее описание:</b>  
Данный проект реализует полностью <b>виртуальную файловую систему (MemoryVFS)</b>, работающую в оперативной памяти, 
и <b>эмулятор терминала (VFSShell)</b>, обеспечивающий взаимодействие с этой файловой системой с помощью команд, 
похожих на команды Unix/Linux.  
Проект демонстрирует работу с древовидными структурами, обработку команд, управление путями, 
а также реализацию интерактивного CLI-интерфейса.</p>

<p>Система состоит из трёх основных компонентов:</p>
<ul>
<li><b>MemoryVFS</b> — управляет структурой виртуальных файлов и каталогов;</li>
<li><b>VFSShell</b> — интерпретирует команды пользователя и вызывает соответствующие операции VFS;</li>
<li><b>TerminalEmulator</b> — контролирует запуск терминала, выполнение скриптов и переход в интерактивный режим.</li>
</ul>

<hr>

<h2>Пример использования</h2>

<pre><code class="language-python">
from vfs import MemoryVFS, VFSShell, TerminalEmulator, create_default_vfs

# Создаём тестовую виртуальную файловую систему
vfs = create_default_vfs()

# Инициализируем оболочку
shell = VFSShell(vfs_name="alex", vfs=vfs)

# Пример работы с командами
print(shell.get_prompt())         # alex:/$
shell.cmd_ls([])                  # Отображает содержимое текущего каталога
shell.cmd_cd(["/home"])           # Переходим в каталог /home
shell.cmd_touch(["notes.txt"])    # Создаём пустой файл
shell.cmd_ls([])                  # Проверяем содержимое /home
shell.cmd_rev(["Привет, мир!"])   # → !рим ,тевирП
shell.cmd_mv(["notes.txt", "memo.txt"])  # Переименовываем файл

# Альтернативно — запуск терминала с исполняемым скриптом
terminal = TerminalEmulator(vfs_name="alex", start_script="init_script.txt")
terminal.start(interactive=True)
</code></pre>

<hr>

<h2>Пример стартового скрипта <code>init_script.txt</code></h2>

<pre><code class="language-bash">
# Создание директорий и файлов
touch /docs/readme.txt
touch /tmp/log.txt

# Навигация
cd /docs
ls
rev Hello Virtual File System!
</code></pre>

<hr>

<h2>Пример структуры виртуальной файловой системы</h2>

<pre><code>
/
├── home/
│   ├── user/
│   │   ├── notes.txt
│   │   └── memo.txt
├── docs/
│   └── readme.txt
└── tmp/
    └── log.txt
</code></pre>

<hr>

<h2>Класс MemoryVFS</h2>

<p><b>Назначение:</b> Виртуальная файловая система, работающая полностью в оперативной памяти. 
Позволяет имитировать структуру каталогов и файлов, выполнять базовые операции (создание, перемещение, чтение, листинг).</p>

<h3>Методы:</h3>
<ol>
<li>__init__</li>
<li>add_entry</li>
<li>get_node</li>
<li>list_dir</li>
<li>make_file</li>
<li>move_entry</li>
</ol>

<hr>

<h3>__init__(self)</h3>
<p>Инициализирует пустую виртуальную файловую систему с корневой директорией <code>/</code>.</p>

<h3>add_entry(self, path, entry_type, content=None)</h3>
<p>Добавляет запись (файл или директорию) в виртуальную файловую систему.</p>
<p><b>Параметры:</b></p>
<ul>
<li><b>path</b> — путь к создаваемой записи (например, <code>/home/user/file.txt</code>)</li>
<li><b>entry_type</b> — тип записи: "dir" или "file"</li>
<li><b>content</b> — содержимое файла в формате base64 (опционально)</li>
</ul>
<p><b>Исключения:</b></p>
<ul>
<li>FileExistsError — если запись уже существует</li>
<li>FileNotFoundError — если родительская директория не найдена</li>
</ul>

<h3>get_node(self, path)</h3>
<p>Возвращает узел (директорию или файл) по указанному пути.</p>
<p><b>Исключения:</b></p>
<ul>
<li>FileNotFoundError — если путь не существует</li>
</ul>

<h3>list_dir(self, path)</h3>
<p>Возвращает список содержимого указанной директории.</p>
<p><b>Исключения:</b></p>
<ul>
<li>NotADirectoryError — если путь указывает на файл, а не на директорию</li>
</ul>

<h3>make_file(self, path)</h3>
<p>Создает пустой файл по заданному пути.</p>
<p><b>Исключения:</b></p>
<ul>
<li>FileNotFoundError — если родительская директория отсутствует</li>
</ul>

<h3>move_entry(self, src, dst)</h3>
<p>Перемещает или переименовывает файл/директорию.</p>
<p><b>Параметры:</b></p>
<ul>
<li><b>src</b> — исходный путь</li>
<li><b>dst</b> — путь назначения</li>
</ul>
<p><b>Исключения:</b></p>
<ul>
<li>FileNotFoundError — если исходный путь не существует</li>
<li>FileExistsError — если запись в месте назначения уже существует</li>
</ul>

<hr>

<h2>Класс VFSShell</h2>

<p><b>Назначение:</b> Эмулятор командной оболочки для взаимодействия с виртуальной файловой системой. 
Позволяет выполнять команды, управлять текущей директорией и работать с путями.</p>

<h3>Методы:</h3>
<ol>
<li>__init__</li>
<li>get_prompt</li>
<li>parse_command</li>
<li>resolve_path</li>
<li>run_command</li>
<li>cmd_ls</li>
<li>cmd_cd</li>
<li>cmd_rev</li>
<li>cmd_uptime</li>
<li>cmd_touch</li>
<li>cmd_mv</li>
<li>cmd_exit</li>
</ol>

<hr>

<h3>__init__(self, vfs_name="sasha", vfs=None)</h3>
<p>Инициализирует оболочку с именем пользователя и объектом VFS. 
Если <code>vfs</code> не передана — создается новая файловая система.</p>

<h3>get_prompt(self)</h3>
<p>Возвращает строку приглашения в формате <code>имя:текущая_директория$</code>.</p>

<h3>parse_command(self, input_string)</h3>
<p>Разбирает введённую пользователем строку на команду и аргументы. Возвращает кортеж <code>(command, args)</code>.</p>

<h3>resolve_path(self, dest)</h3>
<p>Преобразует относительный путь в абсолютный, с учётом текущей директории.</p>

<h3>Команды оболочки:</h3>
<ul>
<li><b>cmd_ls(args)</b> — выводит список файлов и папок в текущей или указанной директории</li>
<li><b>cmd_cd(args)</b> — изменяет текущую директорию</li>
<li><b>cmd_rev(args)</b> — переворачивает слова задом наперёд</li>
<li><b>cmd_uptime(args)</b> — показывает время работы сессии</li>
<li><b>cmd_touch(args)</b> — создаёт пустые файлы</li>
<li><b>cmd_mv(args)</b> — перемещает или переименовывает файлы и каталоги</li>
<li><b>cmd_exit(args)</b> — завершает работу оболочки</li>
</ul>

<h3>run_command(self, command, args)</h3>
<p>Находит и выполняет метод, соответствующий введённой команде. 
Если команда не найдена — выводит сообщение об ошибке.</p>

<hr>

<h2>Класс TerminalEmulator</h2>

<p><b>Назначение:</b> Главный класс, управляющий VFS и оболочкой. 
Отвечает за запуск, выполнение скриптов и переход в интерактивный режим.</p>

<h3>Методы:</h3>
<ol>
<li>__init__</li>
<li>_execute_line</li>
<li>start</li>
</ol>

<hr>

<h3>__init__(self, vfs_name="sasha", vfs_path=None, start_script=None)</h3>
<p>Создает экземпляр терминала, инициализируя VFS (новую или загруженную из файла). 
При наличии скрипта — сохраняет путь для автоматического выполнения при старте.</p>

<h3>_execute_line(self, line)</h3>
<p>Выполняет одну строку команды из скрипта.</p>
<p><b>Возвращает:</b> <code>True</code>, если команда была <code>exit</code>, иначе <code>False</code>.</p>

<h3>start(self, interactive=True)</h3>
<p>Запускает эмулятор терминала:</p>
<ol>
<li>Если указан стартовый скрипт — выполняет его построчно.</li>
<li>Если <code>interactive=True</code> — переходит в интерактивный режим работы.</li>
</ol>

<hr>

<h2>Вспомогательные функции</h2>

<h3>load_vfs_from_csv(csv_path)</h3>
<p>Загружает структуру VFS из CSV-файла.</p>
<p><b>Формат CSV:</b></p>
<table border="1" cellspacing="0" cellpadding="3">
<tr><th>path</th><th>type</th><th>content</th></tr>
<tr><td>/home</td><td>dir</td><td></td></tr>
<tr><td>/home/file.txt</td><td>file</td><td>SGVsbG8=</td></tr>
</table>

<h3>create_default_vfs()</h3>
<p>Создаёт тестовую структуру виртуальной файловой системы (папки, файлы, примеры).</p>

<h3>main()</h3>
<p>Точка входа программы. 
Обрабатывает аргументы командной строки, создаёт экземпляр <code>TerminalEmulator</code> и запускает его.</p>
