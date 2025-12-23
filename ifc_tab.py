import os
import threading
import tkinter as tk
from tkinter import messagebox, colorchooser

import ifcopenshell
import ifcopenshell.api as ifc_api
import ttkbootstrap as ttk


class IfcTab:
    """Логика и UI вкладки IFC (назначение цветов элементам)."""

    def __init__(self, app, tab_frame, messages: dict):
        self.app = app
        self.tab = tab_frame
        self.messages = messages
        self.selected_color = "#ff0000"
        self.ifc_elements = []

        # UI-элементы
        self.ifc_listbox = None
        self.ifc_file_label = None
        self.btn_ifc_reload = None
        self.btn_ifc_apply_color = None
        self.btn_ifc_color_pick = None
        self.ifc_color_label = None

    def build(self):
        """Создание интерфейса вкладки IFC."""
        frame = self.app._create_tab_header(self.tab, "Работа с IFC (цвет элементов)")
        frame.pack(fill=ttk.BOTH, expand=True, padx=5, pady=5)

        info_frame = ttk.Frame(frame)
        info_frame.pack(fill=ttk.X, padx=10, pady=(0, 10))
        ttk.Label(info_frame, text="Для работы используется первый выбранный IFC файл").pack(side=ttk.LEFT)
        self.ifc_file_label = ttk.Label(info_frame, text="", bootstyle="secondary")
        self.ifc_file_label.pack(side=ttk.LEFT, padx=(10, 0))

        list_frame = ttk.Frame(frame)
        list_frame.pack(fill=ttk.BOTH, expand=True, padx=10, pady=(0, 10))

        ttk.Label(list_frame, text="Элементы файла").pack(anchor=ttk.W, pady=(0, 5))

        listbox_frame = ttk.Frame(list_frame)
        listbox_frame.pack(fill=ttk.BOTH, expand=True)

        self.ifc_listbox = tk.Listbox(
            listbox_frame,
            selectmode=tk.EXTENDED,
            height=12,
            exportselection=False
        )
        self.ifc_listbox.pack(side=ttk.LEFT, fill=ttk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(listbox_frame, orient=tk.VERTICAL, command=self.ifc_listbox.yview)
        scrollbar.pack(side=ttk.RIGHT, fill=ttk.Y)
        self.ifc_listbox.configure(yscrollcommand=scrollbar.set)

        controls = ttk.Frame(frame)
        controls.pack(fill=ttk.X, padx=10, pady=5)

        self.ifc_color_label = ttk.Label(
            controls,
            text=f"Текущий цвет: {self.selected_color}",
            padding=5,
            relief="groove"
        )
        self.ifc_color_label.pack(side=ttk.LEFT, padx=(0, 10))

        self.btn_ifc_color_pick = self.app.btn_ifc_color_pick = ttk.Button(
            controls,
            text="Выбрать цвет",
            command=self.choose_ifc_color,
            bootstyle="info",
            style='my.TButton',
            state="disabled"
        )
        self.btn_ifc_color_pick.pack(side=ttk.LEFT, padx=5)

        self.btn_ifc_apply_color = self.app.btn_ifc_apply_color = ttk.Button(
            controls,
            text="Применить к выбранным",
            command=self.apply_color_to_selected,
            bootstyle="success",
            style='my.TButton',
            state="disabled"
        )
        self.btn_ifc_apply_color.pack(side=ttk.LEFT, padx=5)

        self.btn_ifc_reload = self.app.btn_ifc_reload = ttk.Button(
            controls,
            text="Обновить список",
            command=self.load_ifc_elements,
            bootstyle="secondary",
            style='my.TButton',
            state="disabled"
        )
        self.btn_ifc_reload.pack(side=ttk.LEFT, padx=5)

    def on_files_selected(self):
        """Обработчик после выбора IFC файлов."""
        self.load_ifc_elements()

    def on_files_cleared(self):
        """Сброс UI, если файлы не выбраны."""
        if self.ifc_listbox:
            self.ifc_listbox.delete(0, tk.END)
        if self.ifc_file_label:
            self.ifc_file_label.configure(text="")
        for btn in (self.btn_ifc_reload, self.btn_ifc_apply_color, self.btn_ifc_color_pick):
            if btn:
                btn.configure(state="disabled")

    def load_ifc_elements(self):
        """Загрузка элементов из первого выбранного IFC файла."""
        if not self.app.ifc_paths:
            messagebox.showwarning("Нет файлов", self.messages["select_files"])
            return

        first_file = self.app.ifc_paths[0]
        try:
            model = ifcopenshell.open(first_file)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть IFC: {e}")
            return

        products = [
            p for p in model.by_type("IfcProduct")
            if getattr(p, "Representation", None) and getattr(p, "GlobalId", None)
        ]
        self.ifc_elements = [{
            "guid": p.GlobalId,
            "text": f"{p.is_a()} | {p.Name or '(без имени)'}"
        } for p in products]

        self.ifc_listbox.delete(0, tk.END)
        for item in self.ifc_elements:
            self.ifc_listbox.insert(tk.END, item["text"])

        file_name = os.path.basename(first_file)
        self.ifc_file_label.configure(text=file_name)
        for btn in (self.btn_ifc_reload, self.btn_ifc_apply_color, self.btn_ifc_color_pick):
            btn.configure(state="normal")
        self.app.status_var.set(f"Загружено элементов: {len(self.ifc_elements)}")

    def choose_ifc_color(self):
        """Выбор цвета для элементов IFC."""
        color = colorchooser.askcolor(title="Выберите цвет", color=self.selected_color)
        if color and color[1]:
            self.selected_color = color[1]
            self.ifc_color_label.configure(text=f"Текущий цвет: {self.selected_color}")

    def apply_color_to_selected(self):
        """Применение цвета к выбранным элементам."""
        if not self.app.ifc_paths:
            messagebox.showwarning("Нет файлов", self.messages["select_files"])
            return
        selection = self.ifc_listbox.curselection()
        if not selection:
            messagebox.showinfo("Нет выбора", "Выберите один или несколько элементов.")
            return

        selected_guids = [self.ifc_elements[i]["guid"] for i in selection]
        self.app.status_var.set("Применение цвета к элементам...")
        self.app._set_buttons_state("disabled")
        threading.Thread(
            target=self._apply_color_worker,
            args=(selected_guids,),
            daemon=True
        ).start()

    def _apply_color_worker(self, guids):
        """Фоновое применение выбранного цвета к элементам."""
        target_file = self.app.ifc_paths[0]
        try:
            model = ifcopenshell.open(target_file)
            style = ifc_api.run("style.add_style", model, name=f"Color_{self.selected_color}")
            r, g, b = self._hex_to_rgb(self.selected_color)
            ifc_api.run(
                "style.add_surface_style",
                model,
                style=style,
                ifc_class="IfcSurfaceStyleShading",
                attributes={
                    "SurfaceColour": {
                        "Name": None,
                        "Red": r / 255,
                        "Green": g / 255,
                        "Blue": b / 255
                    },
                    "Transparency": 0.0
                }
            )

            updated = 0
            for guid in guids:
                element = model.by_guid(guid)
                if not element or not getattr(element, "Representation", None):
                    continue
                representations = getattr(element.Representation, "Representations", [])
                if not representations:
                    continue
                shape_rep = representations[0]
                ifc_api.run(
                    "style.assign_representation_styles",
                    model,
                    shape_representation=shape_rep,
                    styles=[style]
                )
                updated += 1

            output_path = self._build_colored_path(target_file)
            model.write(output_path)
            msg = f"Цвет применен ({updated} элементов). Сохранено: {os.path.basename(output_path)}"
            print(msg)
            self.app.status_var.set(msg)
            messagebox.showinfo("Готово", msg)
        except Exception as e:
            error_msg = f"Ошибка при применении цвета: {e}"
            print(error_msg)
            messagebox.showerror("Ошибка", error_msg)
        finally:
            self.app._set_buttons_state("normal")

    @staticmethod
    def _build_colored_path(file_path: str) -> str:
        """Формирует путь для сохранения измененного IFC."""
        base, ext = os.path.splitext(file_path)
        return f"{base}_colored{ext}"

    @staticmethod
    def _hex_to_rgb(hex_color: str):
        """Преобразование HEX в RGB."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

