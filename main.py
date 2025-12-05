"""
Основной модуль приложения для обработки IFC файлов.
Предоставляет графический интерфейс для работы с IFC файлами,
включая операции для Tekla Structures, Rhinoceros и проверку IDS.
"""

# Стандартные библиотеки
import os
import sys
import threading
import webbrowser
from io import StringIO
from typing import List, Optional, Callable

# Сторонние библиотеки
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import filedialog, messagebox, scrolledtext

# Локальные модули
from RH_new_guids import assign_guids
from TK_convertIFCclass import convert_ifc_proxies
from ifchelper import Ifc_help
from htmlparser import Parser_html

# Константы приложения
WINDOW_TITLE = "IFC Manager - Обработка IFC файлов"
WINDOW_SIZE = "800x900"
WINDOW_THEME = "cosmo"
WINDOW_PADDING = 20

# Настройки файлов
FILE_TYPES = {
    "ifc": [("IFC files", "*.ifc")],
    "ids": [("IDS files", "*.ids")]
}

# Сообщения
MESSAGES = {
    "select_files": "Выберите IFC файл(ы)",
    "files_selected": "Файлы выбраны",
    "operation_completed": "Операция выполнена",
    "operation_started": "Процесс запущен...",
    "log_copied": "Журнал скопирован в буфер обмена",
    "log_cleared": "Журнал очищен"
}

class CursorApp(ttk.Window):
    """
    Основной класс приложения для обработки IFC файлов.
    Управляет графическим интерфейсом и координацией всех операций.
    """
    
    def __init__(self):
        """Инициализация приложения"""
        super().__init__(themename=WINDOW_THEME)
        self._init_window()
        self._init_variables()
        self._setup_output_redirect()
        self._setup_styles()
        self._build_ui()
        self.update_output()

    def _init_window(self):
        """Инициализация окна приложения"""
        self.title(WINDOW_TITLE)
        self.resizable(False, False)
        self.geometry(WINDOW_SIZE)
        
        # Установка рабочей директории
        os.chdir(os.path.dirname(sys.executable if getattr(sys, 'frozen', False) 
                else os.path.abspath(sys.argv[0])))
        print(f"Рабочая директория установлена: {os.getcwd()}")
        
        # Установка иконки окна
        icon_path = os.path.join(os.getcwd(), "IfcManager.ico")
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception as e:
                print(f"Не удалось загрузить иконку: {e}")

    def _init_variables(self):
        """Инициализация переменных приложения"""
        self.ifc_paths: List[str] = []  # Список путей к IFC файлам
        self.ids_files: List[str] = []  # Список путей к IDS файлам
        self.padding = WINDOW_PADDING
        self.last_ifc_dir: str = ""  # Последняя директория для IFC файлов
        self.last_ids_dir: str = ""  # Последняя директория для IDS файлов

    def _setup_output_redirect(self):
        """Настройка перенаправления вывода"""
        self.stdout_redirector = StringIO()
        self.old_stdout = sys.stdout
        sys.stdout = self.stdout_redirector

    def _setup_styles(self):
        """Настройка стилей приложения"""
        style = ttk.Style()
        
        # Основные стили
        style.configure('my.TButton', font=('Helvetica', 10))
        style.configure('section.TLabelframe.Label', font=('Helvetica', 11, 'bold'))
        style.configure('section.TLabelframe', padding=10)
        style.configure('copy.TButton', font=('Helvetica', 9), foreground='white')
        style.configure('header.TLabel', font=('Helvetica', 16, 'bold'))

        # Стиль для вкладок
        style.configure('TNotebook', background='white')
        style.configure('TNotebook.Tab', 
            padding=[10, 5],
            font=('Helvetica', 10),
            background='white'
        )
        style.map('TNotebook.Tab',
            background=[('selected', '#f2f7ff')],
            foreground=[('selected', '#000000')],
            expand=[('selected', [1, 1, 1, 0])]
        )

    def _build_ui(self):
        """Создание пользовательского интерфейса"""
        main_frame = ttk.Frame(self, padding=self.padding)
        main_frame.pack(fill=ttk.BOTH, expand=True)

        self._create_header(main_frame)
        self._create_file_selector(main_frame)
        self._create_tabs(main_frame)
        self._create_status_bar(main_frame)
        self._create_output_area(main_frame)

    def _create_header(self, parent):
        """Создание заголовка приложения"""
        header = ttk.Label(
            parent, 
            text=WINDOW_TITLE,
            style='header.TLabel',
            bootstyle="primary"
        )
        header.pack(pady=(0, 20))

    def _create_file_selector(self, parent):
        """Создание селектора IFC файлов"""
        file_frame = ttk.LabelFrame(
            parent,
            text="Выбор IFC файлов",
            style='section.TLabelframe'
        )
        file_frame.pack(fill=ttk.X, pady=(0, 20), padx=5)

        self.entry_path = ttk.Entry(file_frame, width=50)
        self.entry_path.pack(side=ttk.LEFT, padx=(10, 10), pady=10, fill=ttk.X, expand=True)
        
        btn_browse = ttk.Button(
            file_frame,
            text="Выбрать IFC файлы",
            command=self.choose_file,
            bootstyle="info",
            style='my.TButton'
        )
        btn_browse.pack(side=ttk.RIGHT, padx=(0, 10), pady=10)

    def _create_tabs(self, parent):
        """Создание вкладок с операциями"""
        self.tab_control = ttk.Notebook(parent)
        self.tab_control.pack(fill=ttk.BOTH, expand=True, pady=(0, 10))

        # Создание вкладок
        self.ids_tab = ttk.Frame(self.tab_control)
        self.tekla_tab = ttk.Frame(self.tab_control)
        self.rhino_tab = ttk.Frame(self.tab_control)
        self.robur_tab = ttk.Frame(self.tab_control)

        # Добавление вкладок
        self.tab_control.add(self.ids_tab, text="Проверка IDS")
        self.tab_control.add(self.tekla_tab, text="Tekla Structures")
        self.tab_control.add(self.rhino_tab, text="Rhinoceros")
        self.tab_control.add(self.robur_tab, text="Robur")

        # Заполнение вкладок
        self._create_ids_tab()
        self._create_tekla_tab()
        self._create_rhino_tab()
        self._create_robur_tab()

    def _create_tab_header(self, parent, text):
        """Создание заголовка для вкладки"""
        header = ttk.Label(
            parent,
            text=text,
            style='header.TLabel',
            bootstyle="primary"
        )
        header.pack(pady=(10, 20))
        return ttk.Frame(parent)

    def _create_tekla_tab(self):
        """Создание вкладки Tekla"""
        frame = self._create_tab_header(self.tekla_tab, "Операции с IFC файлами Tekla")
        frame.pack(fill=ttk.BOTH, expand=True, padx=5, pady=5)

        self.btn_tekla1 = ttk.Button(
            frame,
            text="💊 Замена IFCBuildingElementProxy:Userdefined",
            command=lambda: self.run_operation(convert_ifc_proxies),
            bootstyle="primary",
            style='my.TButton',
            state="disabled"
        )
        self.btn_tekla1.pack(pady=10, padx=10, fill=ttk.X)

        self.btn_tekla2 = ttk.Button(
            frame,
            text="Пустая кнопка",
            command=lambda: self.run_operation(None, "Пустая кнопка", show_info=True),
            bootstyle="primary",
            style='my.TButton',
            state="disabled"
        )
        self.btn_tekla2.pack(pady=10, padx=10, fill=ttk.X)

    def _create_rhino_tab(self):
        """Создание вкладки Rhino"""
        frame = self._create_tab_header(self.rhino_tab, "Операции с IFC файлами Rhinoceros")
        frame.pack(fill=ttk.BOTH, expand=True, padx=5, pady=5)

        self.btn_guid = ttk.Button(
            frame,
            text="Назначить GUID на элементы",
            command=lambda: self.run_operation(assign_guids),
            bootstyle="success",
            style='my.TButton',
            state="disabled"
        )
        self.btn_guid.pack(pady=10, padx=10, fill=ttk.X)

        self.btn_other = ttk.Button(
            frame,
            text="Пустая кнопка",
            command=lambda: self.run_operation(None, "Пустая кнопка", show_info=True),
            bootstyle="success",
            style='my.TButton',
            state="disabled"
        )
        self.btn_other.pack(pady=10, padx=10, fill=ttk.X)

    def _create_robur_tab(self):
        """Создание вкладки Robur"""
        frame = self._create_tab_header(self.robur_tab, "Операции с IFC файлами Robur")
        frame.pack(fill=ttk.BOTH, expand=True, padx=5, pady=5)

        self.btn_robur1 = ttk.Button(
            frame,
            text="Изменить структуру",
            command=lambda: self.run_operation(None, "Изменить структуру", show_info=True),
            bootstyle="info",
            style='my.TButton',
            state="disabled"
        )
        self.btn_robur1.pack(pady=10, padx=10, fill=ttk.X)

        self.btn_robur2 = ttk.Button(
            frame,
            text="Переопределить классы",
            command=lambda: self.run_operation(None, "Переопределить классы", show_info=True),
            bootstyle="info",
            style='my.TButton',
            state="disabled"
        )
        self.btn_robur2.pack(pady=10, padx=10, fill=ttk.X)

    def _create_ids_tab(self):
        """Создание вкладки проверки IDS"""
        frame = self._create_tab_header(self.ids_tab, "Проверка IDS")
        frame.pack(fill=ttk.BOTH, expand=True, padx=5, pady=5)

        # Фрейм для выбора IDS файлов
        ids_files_frame = ttk.Frame(frame)
        ids_files_frame.pack(fill=ttk.X, pady=5, padx=10)

        self.ids_files_var = ttk.StringVar()
        ttk.Label(ids_files_frame, text="IDS файлы:").pack(side=ttk.LEFT, padx=(0, 5))
        self.ids_files_entry = ttk.Entry(ids_files_frame, textvariable=self.ids_files_var, width=60)
        self.ids_files_entry.pack(side=ttk.LEFT, padx=5)
        ttk.Button(
            ids_files_frame,
            text="Выбрать IDS файлы",
            command=self.choose_ids_files,
            bootstyle="info-outline",
            style='my.TButton'
        ).pack(side=ttk.LEFT, padx=5)

        self.btn_ids_check = ttk.Button(
            frame,
            text="🔎 Запустить проверку IDS",
            command=self.run_ids_check,
            bootstyle="warning",
            style='my.TButton',
            state="disabled"
        )
        self.btn_ids_check.pack(pady=10, padx=10, fill=ttk.X)

        self.btn_open_report = ttk.Button(
            frame,
            text="📄 Открыть сводный отчет",
            command=self.open_consolidated_report,
            bootstyle="secondary",
            style='my.TButton',
            state="disabled"
        )
        self.btn_open_report.pack(pady=5, padx=10, fill=ttk.X)
        
        self.btn_open_folder = ttk.Button(
            frame,
            text="📁 Открыть папку с отчетом",
            command=self.open_report_folder,
            bootstyle="info-outline",
            style='my.TButton',
            state="disabled"
        )
        self.btn_open_folder.pack(pady=5, padx=10, fill=ttk.X)
        
        self.btn_delete_reports = ttk.Button(
            frame,
            text="🗑️ Удалить отчеты",
            command=self.delete_reports,
            bootstyle="danger-outline",
            style='my.TButton',
            state="disabled"
        )
        self.btn_delete_reports.pack(pady=5, padx=10, fill=ttk.X)

    def _create_status_bar(self, parent):
        """Создание статус бара"""
        status_frame = ttk.Frame(parent)
        status_frame.pack(side=ttk.BOTTOM, fill=ttk.X, pady=(10, 0))

        status_label = ttk.Label(
            status_frame,
            text="Статус:",
            bootstyle="secondary",
            padding=(0, 5)
        )
        status_label.pack(side=ttk.LEFT, padx=(0, 10))

        self.status_var = ttk.StringVar(value=MESSAGES["select_files"])
        status_bar = ttk.Label(
            status_frame,
            textvariable=self.status_var,
            bootstyle="secondary",
            relief="sunken",
            padding=5
        )
        status_bar.pack(side=ttk.LEFT, fill=ttk.X, expand=True)

    def _create_output_area(self, parent):
        """Создание области вывода"""
        output_frame = ttk.LabelFrame(
            parent,
            text="Журнал операций",
            style='section.TLabelframe'
        )
        output_frame.pack(side=ttk.BOTTOM, fill=ttk.BOTH, expand=True, pady=(10, 0))

        # Кнопки управления журналом
        button_frame = ttk.Frame(output_frame)
        button_frame.pack(side=ttk.BOTTOM, fill=ttk.X, padx=5, pady=(0, 5))

        clear_button = ttk.Button(
            button_frame,
            text="🗑 очистить журнал",
            command=self.clear_log,
            bootstyle="secondary-link",
            style='copy.TButton'
        )
        clear_button.pack(side=ttk.RIGHT, padx=5)

        copy_button = ttk.Button(
            button_frame,
            text="📋 копировать журнал",
            command=self.copy_log,
            bootstyle="secondary-link",
            style='copy.TButton'
        )
        copy_button.pack(side=ttk.RIGHT, padx=5)

        # Область вывода
        self.output_area = scrolledtext.ScrolledText(
            output_frame,
            height=15,
            wrap=ttk.NONE,
            font=('Consolas', 9),
            state='normal',
            xscrollcommand=lambda *args: self.h_scrollbar.set(*args)
        )
        self.output_area.pack(side=ttk.TOP, fill=ttk.BOTH, expand=True, padx=5, pady=5)

        # Горизонтальный скроллбар
        self.h_scrollbar = ttk.Scrollbar(
            output_frame,
            orient='horizontal',
            command=self.output_area.xview
        )
        self.h_scrollbar.pack(side=ttk.BOTTOM, fill=ttk.X, padx=5)

    def update_output(self):
        """Обновление области вывода"""
        output = self.stdout_redirector.getvalue()
        current_text = self.output_area.get('1.0', ttk.END).strip()
        
        if output != current_text:
            current_position = self.output_area.yview()[0]
            self.output_area.delete('1.0', ttk.END)
            self.output_area.insert(ttk.END, output)
            
            if current_position < 1.0:
                self.output_area.yview_moveto(current_position)
        
        self.after(100, self.update_output)

    def choose_file(self):
        """Выбор IFC файлов"""
        paths = filedialog.askopenfilenames(
            title=MESSAGES["select_files"],
            filetypes=FILE_TYPES["ifc"],
            initialdir=self.last_ifc_dir if self.last_ifc_dir else None
        )
        if paths:
            self.ifc_paths = paths
            # Сохраняем директорию последнего выбранного IFC файла
            self.last_ifc_dir = os.path.dirname(paths[0])
            self.entry_path.delete(0, ttk.END)
            self.entry_path.insert(0, f"Выбрано файлов: {len(paths)}")
            self._set_buttons_state("normal")
            self._update_ids_check_button_state()
            self.status_var.set(MESSAGES["files_selected"])
        else:
            self.ifc_paths = []
            self.entry_path.delete(0, ttk.END)
            self.status_var.set(MESSAGES["select_files"])
            self._set_buttons_state("disabled")

    def choose_ids_files(self):
        """Выбор IDS файлов"""
        files = filedialog.askopenfilenames(
            title="Выберите IDS файлы",
            filetypes=FILE_TYPES["ids"],
            initialdir=self.last_ids_dir if self.last_ids_dir else None
        )
        if files:
            self.ids_files = list(files)
            # Сохраняем директорию последнего выбранного IDS файла
            self.last_ids_dir = os.path.dirname(files[0])
            self.ids_files_var.set(f"Выбрано файлов: {len(files)}")
        else:
            self.ids_files = []
            self.ids_files_var.set("")
        self._update_ids_check_button_state()

    def run_operation(self, operation_func: Optional[Callable] = None, 
                     success_message: str = MESSAGES["operation_completed"], 
                     show_info: bool = False):
        """Запуск операции с файлами"""
        if not self.ifc_paths:
            messagebox.showwarning("Предупреждение", MESSAGES["select_files"])
            return
            
        if operation_func:
            print(MESSAGES["operation_started"])
            self.update()
            self._set_buttons_state("disabled")
            threading.Thread(target=self._process_files, args=(operation_func,)).start()
        elif show_info:
            print(MESSAGES["operation_started"])
            self.update()
            messagebox.showinfo("Info", "Здесь вы можете вызвать другую функцию")
            self.status_var.set(success_message)

    def _process_files(self, operation_func: Callable):
        """Обработка файлов в отдельном потоке"""
        try:
            total_files = len(self.ifc_paths)
            for index, file_path in enumerate(self.ifc_paths, 1):
                print(f"[{index}/{total_files}] Обработка файла: {os.path.basename(file_path)}")
                result = operation_func(file_path)
                self.status_var.set(f"[{index}/{total_files}] {result}")
                self.update()
        except Exception as e:
            error_msg = f"Ошибка при обработке файлов: {str(e)}"
            print(error_msg)
            messagebox.showerror("Ошибка", error_msg)
        finally:
            self._set_buttons_state("normal")
            self.status_var.set(MESSAGES["operation_completed"])

    def run_ids_check(self):
        """Запуск проверки IDS"""
        if not self.ifc_paths:
            messagebox.showwarning("Предупреждение", "Выберите IFC файлы для проверки")
            return
        if not self.ids_files:
            messagebox.showwarning("Предупреждение", "Выберите IDS файлы для проверки")
            return

        def check_ids():
            try:
                self._set_buttons_state("disabled")
                self.status_var.set("Выполняется проверка IDS...")
                
                for ifc_path in self.ifc_paths:
                    try:
                        print(f"Проверка файла: {os.path.basename(ifc_path)}")
                        report_folder = os.path.dirname(ifc_path)
                        Ifc_help.check_ifc_file(ifc_path, self.ids_files, report_folder)
                        print(f"✓ {os.path.basename(ifc_path)} - проверка завершена")
                    except Exception as e:
                        print(f"! Ошибка при проверке {os.path.basename(ifc_path)}: {e}")

                try:
                    consolidated_path = os.path.join(os.path.dirname(self.ifc_paths[0]), 'Сводный отчет.html')
                    Parser_html.get_consolidated_html(os.path.dirname(self.ifc_paths[0]), 'Сводный отчет')
                    print("✓ Сводный отчет создан")
                    if os.path.exists(consolidated_path):
                        self.btn_open_report.configure(state="normal")
                except Exception as e:
                    print(f"! Ошибка при создании сводного отчета: {e}")

                self.status_var.set("Проверка IDS завершена")
                messagebox.showinfo("Готово", "Проверка IDS завершена. Отчеты сохранены рядом с IFC файлами.")
            except Exception as e:
                self.status_var.set("Ошибка при проверке IDS")
                messagebox.showerror("Ошибка", f"Произошла ошибка при проверке IDS: {e}")
            finally:
                self._set_buttons_state("normal")

        threading.Thread(target=check_ids, daemon=True).start()

    def open_consolidated_report(self):
        """Открытие сводного отчета"""
        if not self.ifc_paths:
            messagebox.showwarning("Нет файлов", "Сначала выполните проверку IDS.")
            return
        consolidated_path = os.path.join(os.path.dirname(self.ifc_paths[0]), 'Сводный отчет.html')
        if os.path.exists(consolidated_path):
            webbrowser.open(f'file://{os.path.abspath(consolidated_path)}')
        else:
            messagebox.showerror("Файл не найден", "Сводный отчет не найден. Сначала выполните проверку IDS.")

    def open_report_folder(self):
        """Открытие папки с отчетами"""
        if not self.ifc_paths:
            messagebox.showwarning("Нет файлов", "Выберите IFC файлы.")
            return
        report_folder = os.path.dirname(self.ifc_paths[0])
        if os.path.exists(report_folder):
            # Открываем папку в проводнике Windows
            os.startfile(report_folder)
        else:
            messagebox.showerror("Папка не найдена", "Папка с отчетами не найдена.")

    def delete_reports(self):
        """Удаление HTML отчетов"""
        if not self.ifc_paths:
            messagebox.showwarning("Нет файлов", "Выберите IFC файлы.")
            return
        
        report_folder = os.path.dirname(self.ifc_paths[0])
        if not os.path.exists(report_folder):
            messagebox.showerror("Папка не найдена", "Папка с отчетами не найдена.")
            return
        
        # Подсчитываем HTML файлы в папке
        html_files = [f for f in os.listdir(report_folder) if f.endswith('.html')]
        if not html_files:
            messagebox.showinfo("Нет отчетов", "В папке нет HTML отчетов для удаления.")
            return
        
        # Запрашиваем подтверждение
        confirm = messagebox.askyesno(
            "Подтверждение удаления",
            f"Вы уверены, что хотите удалить все HTML отчеты?\n\n"
            f"Будет удалено файлов: {len(html_files)}\n"
            f"Папка: {report_folder}"
        )
        
        if confirm:
            try:
                deleted_count = 0
                for filename in html_files:
                    file_path = os.path.join(report_folder, filename)
                    os.remove(file_path)
                    deleted_count += 1
                    print(f"Удален файл: {filename}")
                
                # Отключаем кнопку открытия отчета, если она была активна
                self.btn_open_report.configure(state="disabled")
                
                print(f"✓ Удалено отчетов: {deleted_count}")
                messagebox.showinfo("Готово", f"Успешно удалено {deleted_count} отчетов.")
                self.status_var.set(f"Удалено отчетов: {deleted_count}")
            except Exception as e:
                error_msg = f"Ошибка при удалении отчетов: {str(e)}"
                print(error_msg)
                messagebox.showerror("Ошибка", error_msg)

    def _set_buttons_state(self, state: str):
        """Установка состояния всех кнопок"""
        for button in [getattr(self, attr) for attr in dir(self) 
                      if attr.startswith('btn_') and isinstance(getattr(self, attr), ttk.Button)]:
            button.configure(state=state)

    def _update_ids_check_button_state(self):
        """Обновление состояния кнопки проверки IDS"""
        if self.ifc_paths and self.ids_files:
            self.btn_ids_check.configure(state="normal")
        else:
            self.btn_ids_check.configure(state="disabled")

    def copy_log(self):
        """Копирование содержимого журнала"""
        log_content = self.output_area.get('1.0', ttk.END).strip()
        self.clipboard_clear()
        self.clipboard_append(log_content)
        self.status_var.set(MESSAGES["log_copied"])
        print(MESSAGES["log_copied"])

    def clear_log(self):
        """Очистка содержимого журнала"""
        self.output_area.delete('1.0', ttk.END)
        self.stdout_redirector = StringIO()
        sys.stdout = self.stdout_redirector
        self.status_var.set(MESSAGES["log_cleared"])
        print(MESSAGES["log_cleared"])

    def __del__(self):
        """Восстановление стандартного вывода при закрытии"""
        sys.stdout = self.old_stdout

if __name__ == "__main__":
    app = CursorApp()
    app.mainloop()
