# RH_new_guids.py

import os
import uuid
import ifcopenshell
import ifcopenshell.util.element as uel
from ifcopenshell.api import layer
import ifcopenshell.api
import re
import traceback

def assign_guids(ifc_path: str) -> str: 
    """
    Записывает во все элементы GUID там, где их не было,
    сохраняет результат в новый файл с суффиксом _guids.ifc.
    Возвращает строку с результатом операции.
    """
    try:
        if not os.path.exists(ifc_path):
            error_msg = f"❌ Файл не найден: {ifc_path}"
            print(error_msg + "\n")
            return error_msg

        model = ifcopenshell.open(ifc_path)
        print(f"IFC открыт: {ifc_path}")

        elements = [el for el in model if hasattr(el, 'GlobalId')]
        print(f"🔍 Найдено {len(elements)} элементов с атрибутом GlobalId")

        updated = 0
        notupdated = 0
        for el in elements:
            # Если GlobalId пустой или None
            if not el.GlobalId:
                new_guid = ifcopenshell.guid.new()
                el.GlobalId = new_guid
                updated += 1
                # print(f"🔧 Назначен новый GlobalId для {el.is_a()}: {new_guid}")
            else:
                # print(f"✔️ Уже есть GUID: {el.GlobalId} ({el.is_a()})")
                notupdated += 1
                pass

        print(f"--------------------------------")
        print(f"GUID присутствовал у {notupdated} элементов")
        print(f"🔄 Назначено GUID на {updated} элементов")

        output_path = ifc_path.replace(".ifc", "_guids.ifc")
        model.write(output_path)
        success_msg = f"💾 Сохранено в: {output_path}"
        print(success_msg)
        print(f"--------------------------------" + "\n")
        return success_msg
        
    except Exception as e:
        error_msg = f"❌ Ошибка при обработке файла: {str(e)}"
        print(error_msg + "\n")
        return error_msg 