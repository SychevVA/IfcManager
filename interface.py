import tkinter as tk
from tkinter import filedialog
import os


class Interface():
    """
    Интерфейс программы
    """
    def __init__(self, func):
        self.func = func
        self.files = []
        self.folder_path_1 = ''
        self.folder_path_2 = ''
        self.file_path = ''

    def select_folder_1(self):
        self.folder_path_1 = filedialog.askdirectory(title="Выберите папку с ifc")
        self.folder_label_1.config(text=self.folder_path_1)
        self.files = os.listdir(self.folder_path_1)  # Получение списка файлов

    def select_folder_2(self):
        self.folder_path_2 = filedialog.askdirectory(title="Выберите папку для отчетов")
        self.folder_label_2.config(text=self.folder_path_2)

    def select_file(self):
        self.file_path = filedialog.askopenfilenames(title="Выберите файлы")
        self.file_label.config(text=", ".join(self.file_path))

    def set_button_function(self):
        self.func(self.files, self.folder_path_1, self.file_path, self.folder_path_2, self.file_list_box)

    def inicialize(self):
        self.root = tk.Tk()
        self.root.title("Проверка IFC")

        # Кнопка выбора папки с файлами ifc
        self.folder_button_1 = tk.Button(self.root, text="Выбрать папку ifc", command=self.select_folder_1)
        self.folder_button_1.pack(side=tk.TOP, anchor=tk.W, padx=10, pady=5)  # Размещение объекта в сетке

        # Текст для передачи пути к папке ifc
        self.folder_label_1 = tk.Label(self.root, text="", width=80)
        self.folder_label_1.pack(side=tk.TOP, fill=tk.X, padx=10)

        # Кнопка выбора файла ids
        self.file_button = tk.Button(self.root, text="Выбрать файлы ids", command=self.select_file)
        self.file_button.pack(side=tk.LEFT, padx=10, pady=10) 

        # Текст для передачи пути к файлу
        self.file_label = tk.Label(self.root, text="", width=80)
        self.file_label.pack(side=tk.TOP, fill=tk.X, padx=10)

        # Кнопка выбора папки для отчетов
        self.folder_button_2 = tk.Button(self.root, text="Выбрать папку отчетов", command=self.select_folder_2)
        self.folder_button_2.pack(side=tk.TOP, anchor=tk.W, padx=10, pady=10)

        # Текст для передачи пути к папке ids
        self.folder_label_2 = tk.Label(self.root, text="", width=80)
        self.folder_label_2.pack(side=tk.TOP, fill=tk.X, padx=10)

        # Кнопка для запуска функции
        self.function_button = tk.Button(self.root, text="Запустить проверку", command=self.set_button_function)
        self.function_button.pack(side=tk.TOP, anchor=tk.W, padx=10, pady=10)

        # Текстовое поле
        self.file_list_box = tk.Listbox(self.root, height=5, width=100)
        self.file_list_box.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.root.mainloop()
