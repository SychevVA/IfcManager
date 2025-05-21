# TK_convertIFCclass.py

import os
import ifcopenshell
import ifcopenshell.util.element as uel
import traceback
from typing import Dict, List, Optional, Tuple

def convert_ifc_proxies(ifc_path: str) -> str:
    """
    Конвертирует все IfcBuildingElementProxy в соответствующие IFC сущности,
    основываясь на proxy.ObjectType в формате "EntityName:PREDEFINED".
    Сохраняет результат в новый файл с суффиксом _converted.ifc.
    Возвращает строку с результатом операции.
    """
    try:
        # 1) проверка существования файла
        if not os.path.exists(ifc_path):
            error_msg = f"❌ Файл не найден: {ifc_path}"
            print(error_msg + "\n")
            return error_msg

        model = ifcopenshell.open(ifc_path)
        proxies = model.by_type("IfcBuildingElementProxy")
        print(f"IFC открыт: {ifc_path}")
        print(f"🔍 Найдено {len(proxies)} BuildingElementProxy‑элементов")

        if not proxies:
            print("ℹ️ Proxy-элементы не найдены")
            return f"ℹ️ В файле {ifc_path} не найдено proxy-элементов"

        # Статистика
        stats = {
            "converted": 0,
            "skipped_no_colon": 0,
            "entity_type_errors": 0,
            "other_errors": 0
        }

        def parse_object_type(obj_type: str) -> Optional[Tuple[str, str]]:
            """Разбор ObjectType в формате 'EntityName:PREDEFINED'"""
            if ":" not in obj_type:
                stats["skipped_no_colon"] += 1
                print(f"\tПропускаем элемент: отсутствует ':' в ObjectType")
                return None

            try:
                entity_name, predefined = [s.strip() for s in obj_type.split(":", 1)]
                predefined = predefined.upper()
                print(f"\tРазбор USERDEFINED: EntityName={entity_name}, PredefinedType={predefined}")
                return entity_name, predefined
            except ValueError:
                print(f"\t⚠️ Некорректный формат ObjectType: {obj_type}")
                stats["skipped_no_colon"] += 1
                return None

        def create_test_entity(entity_name: str, predefined: str, proxy) -> Tuple[bool, Optional[dict]]:
            """Создание тестового элемента для проверки типа сущности"""
            try:
                test_attrs = {
                    "GlobalId": ifcopenshell.guid.new(),
                    "OwnerHistory": proxy.OwnerHistory,
                    "ObjectPlacement": proxy.ObjectPlacement,
                    "Representation": proxy.Representation
                }

                try:
                    test_elem = model.create_entity(
                        entity_name,
                        **test_attrs,
                        PredefinedType=predefined
                    )
                    has_predefined_type = True
                    print(f"\t✅ Тип {entity_name} поддерживает PredefinedType")
                except:
                    test_elem = model.create_entity(entity_name, **test_attrs)
                    has_predefined_type = False
                    print(f"\tℹ️ Тип {entity_name} не поддерживает PredefinedType")

                valid_attributes = [attr for attr in test_elem.get_info().keys() 
                                 if attr not in ["type", "id"]]
                model.remove(test_elem)
                return has_predefined_type, valid_attributes

            except Exception as e:
                stats["entity_type_errors"] += 1
                print(f"\t❌ Ошибка при проверке типа сущности {entity_name}: {str(e)}")
                return False, None

        def copy_relationships(proxy, new_elem) -> Dict[str, bool]:
            """Копирование всех связей элемента"""
            relationship_status = {
                "material": False,
                "property_sets": [],
                "decomposition": False,
                "spatial": False,
                "type": False,
                "group": False,
                "reference": False
            }

            for ref in model.get_inverse(proxy) or []:
                try:
                    if ref.is_a("IfcRelAggregates"):
                        # Добавляем новый элемент в существующую связь
                        related_objects = list(ref.RelatedObjects)
                        related_objects.append(new_elem)
                        ref.RelatedObjects = related_objects
                        relationship_status["decomposition"] = True
                        print(f"\t✅ Обновлена связь декомпозиции с {len(ref.RelatedObjects)} вложенными элементами:")
                        for obj in ref.RelatedObjects:
                            print(f"\t   - {obj.is_a()} (GUID: {obj.GlobalId})")

                    elif ref.is_a("IfcRelAssociatesMaterial"):
                        # Добавляем новый элемент в существующую связь
                        related_objects = list(ref.RelatedObjects)
                        related_objects.append(new_elem)
                        ref.RelatedObjects = related_objects
                        relationship_status["material"] = True
                        print(f"\t✅ Обновлена связь с материалом: {ref.RelatingMaterial.is_a()}")

                    elif ref.is_a("IfcRelContainedInSpatialStructure"):
                        # Добавляем новый элемент в существующую связь
                        related_elements = list(ref.RelatedElements)
                        related_elements.append(new_elem)
                        ref.RelatedElements = related_elements
                        relationship_status["spatial"] = True
                        print(f"\t✅ Обновлена связь с пространственной структурой: {ref.RelatingStructure.is_a()}")

                    elif ref.is_a("IfcRelDefinesByType"):
                        # Добавляем новый элемент в существующую связь
                        related_objects = list(ref.RelatedObjects)
                        related_objects.append(new_elem)
                        ref.RelatedObjects = related_objects
                        relationship_status["type"] = True
                        print(f"\t✅ Обновлена связь с типом: {ref.RelatingType.is_a()}")

                    elif ref.is_a("IfcRelAssignsToGroup"):
                        # Добавляем новый элемент в существующую связь
                        related_objects = list(ref.RelatedObjects)
                        related_objects.append(new_elem)
                        ref.RelatedObjects = related_objects
                        relationship_status["group"] = True
                        print(f"\t✅ Обновлена связь с группой: {ref.RelatingGroup.is_a()}")

                    elif ref.is_a("IfcRelReferencedInSpatialStructure"):
                        # Добавляем новый элемент в существующую связь
                        related_elements = list(ref.RelatedElements)
                        related_elements.append(new_elem)
                        ref.RelatedElements = related_elements
                        relationship_status["reference"] = True
                        print(f"\t✅ Обновлена ссылочная связь с пространственной структурой: {ref.RelatingStructure.is_a()}")

                    elif ref.is_a() in ["IfcRelDefinesByProperties", "IfcRelDefinesByTemplate"]:
                        try:
                            if ref.is_a("IfcRelDefinesByProperties"):
                                # Добавляем новый элемент в существующую связь
                                related_objects = list(ref.RelatedObjects)
                                related_objects.append(new_elem)
                                ref.RelatedObjects = related_objects
                                pset_name = ref.RelatingPropertyDefinition.Name
                                print(f"\t✅ Обновлен набор свойств: {pset_name}")
                            else:
                                # Для IfcRelDefinesByTemplate также обновляем существующую связь
                                related_objects = list(ref.RelatedObjects)
                                related_objects.append(new_elem)
                                ref.RelatedObjects = related_objects
                                pset_name = ref.RelatingTemplate.Name
                                print(f"\t✅ Обновлен шаблон свойств: {pset_name}")
                            
                            relationship_status["property_sets"].append(pset_name)
                        except Exception as e:
                            print(f"\t⚠️ Ошибка при обновлении набора свойств: {str(e)}")

                    else:
                        for a_name, a_val in ref.get_info(include_identifier=False).items():
                            if a_val is proxy:
                                setattr(ref, a_name, new_elem)
                            elif isinstance(a_val, list):
                                setattr(ref, a_name, [new_elem if x is proxy else x for x in a_val])
                        print(f"\tℹ️ Перенаправлена связь типа: {ref.is_a()}")

                except Exception as e:
                    print(f"\t⚠️ Ошибка при обработке связи {ref.is_a()}: {str(e)}")

            return relationship_status

        def print_relationship_summary(status: Dict[str, bool]) -> None:
            """Вывод итоговой информации о связях"""
            print("\n\t📊 Итоговая информация о связях:")
            if not status["material"]:
                print(f"\t   ℹ️ Материал не найден")
            if not status["property_sets"]:
                print(f"\t   ℹ️ Наборы свойств не найдены")
            else:
                print(f"\t   ✅ Скопировано наборов свойств: {len(status['property_sets'])}")
            if not status["decomposition"]:
                print(f"\t   ℹ️ Вложенные элементы не найдены")
            if not status["spatial"]:
                print(f"\t   ℹ️ Связь с пространственной структурой не найдена")
            if not status["type"]:
                print(f"\t   ℹ️ Связь с типом не найдена")
            if not status["group"]:
                print(f"\t   ℹ️ Связь с группой не найдена")
            if not status["reference"]:
                print(f"\t   ℹ️ Ссылочная связь не найдена")

        # Основной цикл обработки элементов
        for proxy in proxies:
            try:
                print(f"\n🔍 Обработка элемента с GUID: {proxy.GlobalId}")
                
                # Разбор ObjectType
                result = parse_object_type(proxy.ObjectType or "")
                if not result:
                    continue
                entity_name, predefined = result

                # Проверка типа сущности
                has_predefined_type, valid_attributes = create_test_entity(entity_name, predefined, proxy)
                if not valid_attributes:
                    continue

                # Сбор атрибутов для нового элемента
                raw_attrs = proxy.get_info(include_identifier=False)
                raw_attrs.pop("type", None)
                raw_attrs.pop("id", None)

                # Критические атрибуты
                critical_attrs = [
                    "ObjectPlacement",    # положение в пространстве
                    "Representation",     # геометрия
                    "ContainedInStructure", # связь со структурой здания
                    "HasAssociations",    # связи с материалами и другими объектами
                    "IsDefinedBy",        # определения свойств
                    "IsTypedBy",          # связи с типами
                    "IsGroupedBy",        # группировки
                    "ReferencedBy",       # ссылки
                    "Decomposes",         # декомпозиция
                    "IsDecomposedBy"      # декомпозиция
                ]

                # Создание нового элемента
                attr_values = {}
                for attr in critical_attrs:
                    if attr in raw_attrs:
                        attr_values[attr] = raw_attrs[attr]

                for attr_name in valid_attributes:
                    if attr_name in raw_attrs and attr_name not in critical_attrs:
                        attr_values[attr_name] = raw_attrs[attr_name]

                if has_predefined_type:
                    attr_values["PredefinedType"] = predefined

                # Проверка критических атрибутов
                missing_critical = [attr for attr in ["ObjectPlacement", "Representation"] 
                                  if attr not in attr_values]
                if missing_critical:
                    print(f"\t⚠️ Пропуск элемента: отсутствуют критические атрибуты: {', '.join(missing_critical)}")
                    stats["other_errors"] += 1
                    continue

                # Проверка геометрии
                if "Representation" in attr_values:
                    rep = attr_values["Representation"]
                    if not rep or not rep.Representations:
                        print(f"\t⚠️ Пропуск элемента: отсутствует геометрия")
                        stats["other_errors"] += 1
                        continue

                # Создание нового элемента
                new_elem = model.create_entity(entity_name, **attr_values)
                stats["converted"] += 1

                # Копирование связей
                relationship_status = copy_relationships(proxy, new_elem)
                print_relationship_summary(relationship_status)

                # Удаление старого proxy
                model.remove(proxy)

            except Exception as e:
                stats["other_errors"] += 1
                print(f"\t\t⚠️ Ошибка при конвертации {proxy.GlobalId}:")
                print(f"\t\t   ObjectType: {proxy.ObjectType}")
                print(f"\t\t   EntityName: {entity_name}")
                print(f"\t\t   PredefinedType: {predefined}")
                print(f"\t\t   Количество атрибутов в attr_values: {len(attr_values)}")
                print(f"\t\t   Атрибуты: {list(attr_values.keys())}")
                print(f"\t\t   Тип ошибки: {type(e).__name__}")
                print(f"\t\t   Сообщение ошибки: {str(e)}")
                print("\t\t   Полный стек ошибки:")
                traceback.print_exc()
                print("\t\t   Дополнительная информация:")
                try:
                    print(f"\t\t   - Representation: {proxy.Representation.is_a() if proxy.Representation else 'None'}")
                    print(f"\t\t   - ObjectPlacement: {proxy.ObjectPlacement.is_a() if proxy.ObjectPlacement else 'None'}")
                    print(f"\t\t   - OwnerHistory: {proxy.OwnerHistory.is_a() if proxy.OwnerHistory else 'None'}")
                    print(f"\t\t   - Количество связей: {len(model.get_inverse(proxy) or [])}")
                except Exception as info_e:
                    print(f"\t\t   - Ошибка при получении дополнительной информации: {str(info_e)}")
                print("--------------------------------")

        # Итоговая статистика
        print("\n--------------------------------")
        print(f"Конвертировано:                 {stats['converted']} элементов")
        print(f"Пропущено элементов без ':':    {stats['skipped_no_colon']} элементов")
        print(f"Ошибок проверки типа сущности:  {stats['entity_type_errors']} элементов")
        print(f"Других ошибок:                  {stats['other_errors']} элементов")
        
        # Сохранение результата
        output_path = ifc_path[:-4] + "_converted.ifc"
        model.write(output_path)
        success_msg = f"💾 Сохранено в: {output_path}"
        print(success_msg)
        print("--------------------------------" + "\n")
        return success_msg

    except Exception as e:
        error_msg = "❌ Фатальная ошибка при обработке файла:"
        print(error_msg)
        print(f"   Тип ошибки: {type(e).__name__}")
        print(f"   Сообщение: {str(e)}")
        print("   Полный стек ошибки:")
        traceback.print_exc()
        return error_msg + f"\n{type(e).__name__}: {str(e)}" 