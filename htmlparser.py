import os
from bs4 import BeautifulSoup


class Parser_html:
    """
    Класс содержит методы для формирвоания сводного отчета html
    """

    def __init__(self):
        pass

    @staticmethod
    def parse_html(file_path):
        """
        Функция для получения файла html c помощью библиотеки BeautifulSoup
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
            return soup

    @staticmethod
    def save_consolidated_html(consolidated_soup, output_filename):
        """
        Функция для сохранения файла html
        """
        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write(consolidated_soup.prettify())

    @staticmethod
    def get_consolidated_html(input_dir, output_filename):
        """
        Функция для формирования сводного html документа из отчетов ids
        """
        input_filenames = [os.path.join(input_dir, filename) for filename in os.listdir(input_dir) if filename.endswith(
            '.html') and 'Сводный' not in filename]  # Списковое включение для формирование списка названий файлов с абсолютными путями. При обработке добавляются только файлы html и исключаются файл сводного отчета

        # Создание документа html и основных тегов
        consolidated_soup = BeautifulSoup('<html lang="ru">', 'html.parser')
        head_tag = BeautifulSoup().new_tag('head')
        meta_tag = BeautifulSoup().new_tag('meta', charset='UTF-8')
        title_tag = BeautifulSoup().new_tag('title')
        body_tag = BeautifulSoup().new_tag('body')

        # Добавление тегов в документ
        head_tag.append(meta_tag)
        head_tag.append(title_tag)
        consolidated_soup.append(head_tag)

        title_tag.string = 'Сводный отчет'

        # Добавление CSS стилей для визуального разделения
        style_tag = BeautifulSoup().new_tag('style')
        style_tag.string = '''
            .ifc-group {
                margin: 30px 0;
                padding: 20px;
                border: 2px solid #0066cc;
                border-radius: 8px;
                background: linear-gradient(135deg, #f8f9ff 0%, #e6f3ff 100%);
                box-shadow: 0 2px 8px rgba(0, 102, 204, 0.1);
            }
            .ifc-header {
                color: #0066cc;
                font-size: 24px;
                font-weight: bold;
                margin-bottom: 20px;
                padding: 10px 15px;
                background: #ffffff;
                border-radius: 5px;
                border-left: 5px solid #0066cc;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
            }
            .report-item {
                margin: 15px 0;
                padding: 15px;
                background: #ffffff;
                border-radius: 5px;
                border: 1px solid #e0e0e0;
            }
            .report-item:nth-child(even) {
                background: #fafafa;
            }
            body {
                font-family: Arial, sans-serif;
                line-height: 1.6;
                margin: 20px;
                background: #f5f5f5;
            }
        '''
        head_tag.append(style_tag)

        processed_styles = set()  # Множество для записи настроек стиля

        # Группировка файлов по IFC файлам
        ifc_groups = {}
        for input_filename in input_filenames:
            filename = os.path.basename(input_filename).replace('.html', '')
            # Извлекаем имя IFC файла (всё до двойного подчёркивания)
            # Формат файла: {ifc_name}__{ids_name}.html
            if '__' in filename:
                # Находим двойное подчёркивание и берём всё что до него
                double_underscore_index = filename.find('__')
                ifc_name = filename[:double_underscore_index]
            else:
                ifc_name = filename
            
            if ifc_name not in ifc_groups:
                ifc_groups[ifc_name] = []
            ifc_groups[ifc_name].append(input_filename)

        # Обработка файлов по группам IFC
        for ifc_name, group_files in ifc_groups.items():
            # Создаём контейнер для группы IFC файлов
            ifc_group_div = BeautifulSoup().new_tag('div', attrs={'class': 'ifc-group'})
            
            # Добавляем заголовок IFC файла
            ifc_header = BeautifulSoup().new_tag('h1', attrs={'class': 'ifc-header'})
            ifc_header.string = f'IFC файл: {ifc_name}'
            ifc_group_div.append(ifc_header)

            for input_filename in group_files:  # Цикл для обработки файлов отчетов
                soup = Parser_html.parse_html(input_filename)  # Получение файла html

                for style in soup.find_all('style'):  # Цикл для обработки элементов в теге <style>
                    style_content = style.get_text(strip=True)
                    if style_content not in processed_styles:
                        new_style = BeautifulSoup().new_tag('style')
                        new_style.string = style.get_text()
                        head_tag.append(new_style)
                        processed_styles.add(style_content)

                # Создаём контейнер для каждого отчёта
                report_item_div = BeautifulSoup().new_tag('div', attrs={'class': 'report-item'})

                # Получение содержимого тегов <h2> <div> <p>
                h2_tag = soup.find('h2')
                if h2_tag is not None:
                    h2_tag.string = os.path.basename(input_filename).replace('.html', '')
                else:
                    h2_tag = soup.new_tag('h2')
                    h2_tag.string = os.path.basename(input_filename).replace('.html', '') + " (нет заголовка)"

                link_tag = soup.new_tag('a')
                link_tag['href'] = os.path.basename(input_filename)
                link_tag.string = 'Ссылка на отчёт'

                container_div = soup.find('div', {'class': 'container'})
                p_tag = None
                if container_div is not None:
                    p_tag = container_div.find_next('p')

                # Добавление элементов в контейнер отчёта
                report_item_div.append(h2_tag)
                report_item_div.append(link_tag)
                if container_div is not None:
                    report_item_div.append(container_div)
                else:
                    empty_div = soup.new_tag('div')
                    empty_div.string = "Нет блока container в отчете"
                    report_item_div.append(empty_div)
                if p_tag is not None:
                    report_item_div.append(p_tag)

                # Добавляем отчёт в группу
                ifc_group_div.append(report_item_div)

            # Добавляем группу в body
            body_tag.append(ifc_group_div)

        consolidated_soup.append(body_tag)

        # Сохранение сводного отчета
        output_file_path = f'{input_dir}/{output_filename}.html'
        Parser_html.save_consolidated_html(consolidated_soup, output_file_path)


if __name__ == '__main__':
    # Проверка работы функции
    input_dir = r'c:\Users\...\reports'
    output_filename = 'Сводный отчет'
    Parser_html.get_consolidated_html(input_dir, output_filename)