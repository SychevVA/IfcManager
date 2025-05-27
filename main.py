# cursor.py
# тест
import os
import sys
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import filedialog, messagebox, scrolledtext
from RH_new_guids import assign_guids
from TK_convertIFCclass import convert_ifc_proxies
from io import StringIO
import threading
from ifchelper import Ifc_help
from htmlparser import Parser_html


# Для компиляции вставь в терминал: pyinstaller --onefile --windowed --name IFC_TEKLA_RHINO main.py

# TEST
# Установка рабочей директории
os.chdir(os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else os.path.abspath(sys.argv[0])))

print(f"Рабочая директория установлена: {os.getcwd()}")

class CursorApp(ttk.Window):
    def __init__(self):
        super().__init__(themename="cosmo")
        self.title("Обработка IFC-файлов")
        self.resizable(False, False)
        self.geometry("800x900")  # Увеличиваем высоту окна с 600px до 700px
        self.ifc_paths = []  # Список путей к файлам
        self.padding = 20
        
        # Перехватываем стандартный вывод
        self.stdout_redirector = StringIO()
        self.old_stdout = sys.stdout
        sys.stdout = self.stdout_redirector
        
        style = ttk.Style()
        style.configure('my.TButton', font=('Helvetica', 10))
        style.configure('section.TLabelframe.Label', font=('Helvetica', 11, 'bold'))
        style.configure('section.TLabelframe', padding=10)
        
        self._build_ui()
        
        # Запускаем периодическое обновление вывода
        self.update_output()
        
    def __del__(self):
        # Восстанавливаем стандартный вывод при закрытии приложения
        sys.stdout = self.old_stdout

    def _build_ui(self):
        # Создаем основной контейнер с отступами
        main_frame = ttk.Frame(self, padding=(self.padding))
        main_frame.pack(fill=ttk.BOTH, expand=True)

        # Заголовок
        header = ttk.Label(
            main_frame, 
            text="Обработка IFC4 файлов",
            font=('Helvetica', 16, 'bold'),
            bootstyle="primary"
        )
        header.pack(pady=(0, 20))

        # Поле выбора файла с улучшенным оформлением
        file_frame = ttk.LabelFrame(
            main_frame,
            text="Выбор файлов",
            style='section.TLabelframe'
        )
        file_frame.pack(fill=ttk.X, pady=(0, 20), padx=5)

        self.entry_path = ttk.Entry(file_frame, width=50)
        self.entry_path.pack(side=ttk.LEFT, padx=(10, 10), pady=10, fill=ttk.X, expand=True)
        
        btn_browse = ttk.Button(
            file_frame,
            text="Выбрать IFС файлы",
            command=self.choose_file,
            bootstyle="info",
            style='my.TButton'
        )
        btn_browse.pack(side=ttk.RIGHT, padx=(0, 10), pady=10)

        # Создаем frame для двух колонок кнопок
        buttons_container = ttk.Frame(main_frame)
        buttons_container.pack(fill=ttk.X, pady=10)

        # Левая колонка (Tekla)
        left_frame = ttk.LabelFrame(
            buttons_container,
            text="IFC-файлы Tekla Structures",
            style='section.TLabelframe'
        )
        left_frame.pack(side=ttk.LEFT, fill=ttk.BOTH, expand=True, padx=5)

        # Кнопки для Tekla
        self.btn_tekla1 = ttk.Button(
            left_frame,
            text="Замена IFCBuildingElementProxy:Userdefined",
            command=lambda: self.run_operation(convert_ifc_proxies),
            bootstyle="primary",
            style='my.TButton',
            state="disabled"
        )
        self.btn_tekla1.pack(pady=10, padx=10, fill=ttk.X)

        self.btn_tekla2 = ttk.Button(
            left_frame,
            text="Пустая кнопка",
            command=lambda: self.run_operation(None, "Пустая кнопка", show_info=True),
            bootstyle="primary",
            style='my.TButton',
            state="disabled"
        )
        self.btn_tekla2.pack(pady=10, padx=10, fill=ttk.X)

        # Правая колонка (Rhino)
        right_frame = ttk.LabelFrame(
            buttons_container,
            text="IFC-файлы Rhinoceros",
            style='section.TLabelframe'
        )
        right_frame.pack(side=ttk.RIGHT, fill=ttk.BOTH, expand=True, padx=5)

        # Кнопки для Rhino
        self.btn_guid = ttk.Button(
            right_frame,
            text="Назначить GUID на элементы",
            command=lambda: self.run_operation(assign_guids),
            bootstyle="success",
            style='my.TButton',
            state="disabled"
        )
        self.btn_guid.pack(pady=10, padx=10, fill=ttk.X)

        self.btn_other = ttk.Button(
            right_frame,
            text="Пустая кнопка",
            command=lambda: self.run_operation(None, "Пустая кнопка", show_info=True),
            bootstyle="success",
            style='my.TButton',
            state="disabled"
        )
        self.btn_other.pack(pady=10, padx=10, fill=ttk.X)

        # --- IDS: Новая секция для проверки IDS ---
        ids_frame = ttk.LabelFrame(
            main_frame,
            text="Проверка IDS",
            style='section.TLabelframe'
        )
        ids_frame.pack(fill=ttk.X, pady=10, padx=5)

        # Фрейм для выбора IDS файлов
        ids_files_frame = ttk.Frame(ids_frame)
        ids_files_frame.pack(fill=ttk.X, pady=5, padx=10)

        # IDS: Список выбранных IDS-файлов (теперь выбираются именно файлы, а не папка)
        self.ids_files = []  # Список путей к выбранным IDS-файлам
        self.ids_files_var = ttk.StringVar()  # Для отображения количества выбранных IDS-файлов
        ttk.Label(ids_files_frame, text="IDS файлы:").pack(side=ttk.LEFT, padx=(0, 5))
        self.ids_files_entry = ttk.Entry(ids_files_frame, textvariable=self.ids_files_var, width=60)
        self.ids_files_entry.pack(side=ttk.LEFT, padx=5)
        ttk.Button(
            ids_files_frame,
            text="Выбрать",
            command=self.choose_ids_files,  # IDS: Выбор нескольких IDS-файлов
            bootstyle="info-outline",
            style='my.TButton'
        ).pack(side=ttk.LEFT, padx=5)

        # IDS: Кнопка запуска проверки IDS (активируется только если выбраны и IFC, и IDS)
        self.btn_ids_check = ttk.Button(
            ids_frame,
            text="Запустить проверку IDS",
            command=self.run_ids_check,  # IDS: Запуск проверки
            bootstyle="warning",
            style='my.TButton',
            state="disabled"
        )
        self.btn_ids_check.pack(pady=10, padx=10, fill=ttk.X)

        # IDS: Кнопка для открытия сводного отчета (по умолчанию неактивна)
        self.btn_open_report = ttk.Button(
            ids_frame,
            text="Открыть сводный отчет",
            command=self.open_consolidated_report,
            bootstyle="secondary",
            style='my.TButton',
            state="disabled"
        )
        self.btn_open_report.pack(pady=5, padx=10, fill=ttk.X)

        # Создаем frame для статус бара
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(side=ttk.BOTTOM, fill=ttk.X, pady=(10, 0))

        # Добавляем надпись "Статус:"
        status_label = ttk.Label(
            status_frame,
            text="Статус:",
            bootstyle="secondary",
            padding=(0, 5)
        )
        status_label.pack(side=ttk.LEFT, padx=(0, 10))

        # Добавляем статус бар
        self.status_var = ttk.StringVar(value="Выберите IFC файл(ы)")
        status_bar = ttk.Label(
            status_frame,
            textvariable=self.status_var,
            bootstyle="secondary",
            relief="sunken",
            padding=5
        )
        status_bar.pack(side=ttk.LEFT, fill=ttk.X, expand=True)

        # Добавляем область для вывода print в отдельном frame
        output_frame = ttk.LabelFrame(
            main_frame,
            text="Журнал операций",
            style='section.TLabelframe'
        )
        output_frame.pack(side=ttk.BOTTOM, fill=ttk.BOTH, expand=True, pady=(10, 0))

        # Настраиваем стиль для кнопки копирования
        style = ttk.Style()
        style.configure('copy.TButton', 
            font=('Helvetica', 9),
            foreground='white'
        )

        # Создаем фрейм для кнопок
        button_frame = ttk.Frame(output_frame)
        button_frame.pack(side=ttk.BOTTOM, fill=ttk.X, padx=5, pady=(0, 5))

        # Добавляем кнопку очистки
        clear_button = ttk.Button(
            button_frame,
            text="🗑 очистить журнал",
            command=self.clear_log,
            bootstyle="secondary-link",
            style='copy.TButton'
        )
        clear_button.pack(side=ttk.RIGHT, padx=5)

        # Добавляем кнопку копирования
        copy_button = ttk.Button(
            button_frame,
            text="📋 копировать журнал",
            command=self.copy_log,
            bootstyle="secondary-link",
            style='copy.TButton'
        )
        copy_button.pack(side=ttk.RIGHT, padx=5)

        self.output_area = scrolledtext.ScrolledText(
            output_frame,
            height=25,  # Увеличиваем высоту с 12 до 25 строк
            wrap=ttk.NONE,  # Отключаем перенос строк для горизонтальной прокрутки
            font=('Consolas', 9),
            state='normal',
            xscrollcommand=lambda *args: self.h_scrollbar.set(*args)  # Привязываем горизонтальный скроллбар
        )
        self.output_area.pack(side=ttk.TOP, fill=ttk.BOTH, expand=True, padx=5, pady=5)

        # Добавляем горизонтальный скроллбар
        self.h_scrollbar = ttk.Scrollbar(
            output_frame,
            orient='horizontal',
            command=self.output_area.xview
        )
        self.h_scrollbar.pack(side=ttk.BOTTOM, fill=ttk.X, padx=5)

    def update_output(self):
        # Получаем новый вывод
        output = self.stdout_redirector.getvalue()
        current_text = self.output_area.get('1.0', ttk.END).strip()
        
        if output != current_text:
            # Сохраняем текущую позицию прокрутки
            current_position = self.output_area.yview()[0]
            
            # Обновляем текст
            self.output_area.delete('1.0', ttk.END)
            self.output_area.insert(ttk.END, output)
            
            # Восстанавливаем позицию прокрутки, если пользователь не в самом низу
            if current_position < 1.0:  # Если не в самом низу
                self.output_area.yview_moveto(current_position)
            
        # Планируем следующее обновление
        self.after(100, self.update_output)

    def choose_file(self):
        paths = filedialog.askopenfilenames(
            title="Выберите IFC-файлы",
            filetypes=[("IFC files", "*.ifc")],
        )
        if paths:
            self.ifc_paths = paths
            self.entry_path.delete(0, ttk.END)
            self.entry_path.insert(0, f"Выбрано файлов: {len(paths)}")
            self._set_buttons_state("normal")
            self._update_ids_check_button_state()
            self.status_var.set("Файлы выбраны")
        else:
            self.ifc_paths = []
            self.entry_path.delete(0, ttk.END)
            self.status_var.set("Выберите IFC файл(ы)")
            # Деактивируем все кнопки
            self.btn_guid.configure(state="disabled")
            self.btn_other.configure(state="disabled")
            self.btn_tekla1.configure(state="disabled")
            self.btn_tekla2.configure(state="disabled")

    def run_operation(self, operation_func=None, success_message="Операция выполнена", show_info=False):
        if operation_func:
            print("Процесс запущен...")  # Логируем начало процесса
            self.update()  # Обновляем интерфейс сразу после логирования
            # Отключаем кнопки
            self._set_buttons_state("disabled")
            # Запускаем обработку файлов в отдельном потоке
            threading.Thread(target=self._process_files, args=(operation_func,)).start()
        elif show_info:
            print("Процесс запущен...")  # Логируем начало процесса
            self.update()  # Обновляем интерфейс сразу после логирования
            messagebox.showinfo("Info", "Здесь вы можете вызвать другую функцию")
            self.status_var.set(success_message)

    def _process_files(self, operation_func):
        total_files = len(self.ifc_paths)
        for index, file_path in enumerate(self.ifc_paths, 1):
            print(f"[{index}/{total_files}] Обработка файла: {os.path.basename(file_path)}")
            result = operation_func(file_path)
            self.status_var.set(f"[{index}/{total_files}] {result}")
            self.update()
        # Включаем кнопки после завершения
        self._set_buttons_state("normal")

    def _set_buttons_state(self, state):
        """Устанавливает состояние всех кнопок"""
        self.btn_guid.configure(state=state)
        self.btn_tekla1.configure(state=state)
        self.btn_tekla2.configure(state=state)
        self.btn_other.configure(state=state)

    def copy_log(self):
        """Копирует содержимое журнала в буфер обмена"""
        log_content = self.output_area.get('1.0', ttk.END).strip()
        self.clipboard_clear()
        self.clipboard_append(log_content)
        self.status_var.set("Журнал скопирован в буфер обмена")

    def clear_log(self):
        """Очищает содержимое журнала"""
        self.output_area.delete('1.0', ttk.END)
        self.stdout_redirector = StringIO()
        sys.stdout = self.stdout_redirector
        self.status_var.set("Журнал очищен")

    def choose_ids_files(self):
        """
        IDS: Открывает диалог выбора IDS-файлов (можно выбрать несколько .ids)
        После выбора обновляет список и отображение количества файлов
        """
        files = filedialog.askopenfilenames(
            title="Выберите IDS-файлы",
            filetypes=[("IDS files", "*.ids")],
        )
        if files:
            self.ids_files = list(files)
            self.ids_files_var.set(f"Выбрано файлов: {len(files)}")
        else:
            self.ids_files = []
            self.ids_files_var.set("")
        self._update_ids_check_button_state()  # IDS: Проверка, можно ли активировать кнопку

    def _update_ids_check_button_state(self):
        """
        IDS: Активирует кнопку запуска IDS, если выбраны и IFC-файлы, и IDS-файлы
        """
        if self.ifc_paths and self.ids_files:
            self.btn_ids_check.configure(state="normal")
        else:
            self.btn_ids_check.configure(state="disabled")

    def run_ids_check(self):
        """
        IDS: Запускает проверку IDS для выбранных IFC-файлов и IDS-файлов
        - Для каждого IFC-файла отчеты сохраняются в ту же папку, где лежит IFC
        - Сводный отчет формируется в папке первого IFC-файла
        - Все действия выполняются в отдельном потоке, чтобы не блокировать интерфейс
        """
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
                        # IDS: Папка для отчета = папка IFC файла
                        report_folder = os.path.dirname(ifc_path)
                        Ifc_help.check_ifc_file(ifc_path, self.ids_files, report_folder)
                        print(f"✓ {os.path.basename(ifc_path)} - проверка завершена")
                    except Exception as e:
                        print(f"! Ошибка при проверке {os.path.basename(ifc_path)}: {e}")
                # IDS: Сводный отчет по всем IFC в папке первого IFC
                try:
                    consolidated_path = os.path.join(os.path.dirname(self.ifc_paths[0]), 'Сводный отчет.html')
                    Parser_html.get_consolidated_html(os.path.dirname(self.ifc_paths[0]), 'Сводный отчет')
                    print("✓ Сводный отчет создан")
                    # Активируем кнопку открытия отчета, если файл создан
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
        """
        Открывает сводный отчет в браузере по умолчанию, если файл существует
        """
        if not self.ifc_paths:
            messagebox.showwarning("Нет файлов", "Сначала выполните проверку IDS.")
            return
        consolidated_path = os.path.join(os.path.dirname(self.ifc_paths[0]), 'Сводный отчет.html')
        if os.path.exists(consolidated_path):
            import webbrowser
            webbrowser.open(f'file://{os.path.abspath(consolidated_path)}')
        else:
            messagebox.showerror("Файл не найден", "Сводный отчет не найден. Сначала выполните проверку IDS.")

if __name__ == "__main__":
    app = CursorApp()
    app.mainloop()
