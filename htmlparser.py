import os
from bs4 import BeautifulSoup
from datetime import datetime


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
                margin: 10px 0;
                padding: 5px 25px;
                border: 2px solid #0066cc;
                border-radius: 8px;
                background: linear-gradient(135deg, #f8f9ff 0%, #e6f3ff 100%);
                box-shadow: 0 2px 8px rgba(0, 102, 204, 0.1);
            }
            .ifc-header {
                color: #0066cc;
                font-size: 20px;
                font-weight: bold;
                margin-bottom: 15px;
                padding: 8px 12px 8px 40px;
                background: #ffffff;
                border-radius: 5px;
                border-left: 5px solid #0066cc;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
                cursor: pointer;
                user-select: none;
                transition: all 0.3s ease;
                position: relative;
            }
            .ifc-header:hover {
                background: #f0f8ff;
                transform: translateX(5px);
            }
            .ifc-header::after {
                content: "▼";
                position: absolute;
                left: 12px;
                top: 50%;
                transform: translateY(-50%);
                transition: transform 0.3s ease;
                font-size: 14px;
                color: #0066cc;
            }
            .ifc-header.collapsed::after {
                transform: translateY(-50%) rotate(-90deg);
            }
            .ifc-content {
                transition: all 0.3s ease;
                overflow: hidden;
            }
            .ifc-content.collapsed {
                max-height: 0;
                opacity: 0;
                margin: 0;
                padding: 0;
            }
            .report-item {
                margin: 10px 0;
                padding: 12px;
                background: #ffffff;
                border-radius: 5px;
                border: 1px solid #e0e0e0;
            }
            .report-item:nth-child(even) {
                background: #fafafa;
            }
            .report-item h2 {
                font-size: 16px;
                margin: 0 0 8px 0;
            }
            .report-item p {
                font-size: 14px;
                margin: 5px 0;
            }
            .report-item a {
                font-size: 14px;
            }
            .report-item div {
                font-size: 14px;
            }
            .container {
                margin-bottom: 10px;
                margin-top: 5px;
            }
            .container.na-result {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 10px;
                color: #666;
                opacity: 0.2;
            }
            .container.na-result::before {
                content: "Skipped";
                display: block;
                color: #888;
                margin-bottom: 5px;
            }
            /* Стили для fail percent элементов содержащих N/A */
            .fail.percent.na-result {
                color: #888 !important;
                background-color: #ddd !important;
                border-color: #bbb !important;
                opacity: 0.5;
            }
            .fail.percent.na-result::before {
                content: "Skipped -";
                display: inline-block;
                font-weight: bold;
                color: #888;
                margin-right: 5px;
                font-size: 10px;
            }
            body {
                font-family: Arial, sans-serif;
                line-height: 1.4;
                margin: 15px 100px;
                background: #f5f5f5;
                font-size: 14px;
            }
            .controls {
                position: fixed;
                top: 30px;
                right: 20px;
                z-index: 1000;
            }
            .control-btn {
                background: #a9a9a9;
                color: white;
                border: none;
                padding: 5px;
                margin: 5px;
                border-radius: 5px;
                cursor: pointer;
                font-size: 11px;
                transition: all 0.3s ease;
                display: block;
                width: 100%;
                text-align: left;
            }
            .control-btn:hover {
                background: #0052a3;
                transform: translateY(-1px);
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
            }
            .control-btn:active {
                transform: translateY(0);
            }
        '''
        head_tag.append(style_tag)

        # Добавление JavaScript для функциональности спойлеров
        script_tag = BeautifulSoup().new_tag('script')
        script_tag.string = '''
            document.addEventListener('DOMContentLoaded', function() {
                // Добавляем обработчики событий для всех заголовков IFC
                const headers = document.querySelectorAll('.ifc-header');
                headers.forEach(function(header) {
                    header.addEventListener('click', function() {
                        const group = this.closest('.ifc-group');
                        const content = group.querySelector('.ifc-content');
                        
                        // Переключаем состояние
                        this.classList.toggle('collapsed');
                        content.classList.toggle('collapsed');
                    });
                });
                
                // Обработчик для кнопки "Свернуть все"
                document.getElementById('collapse-all').addEventListener('click', function() {
                    headers.forEach(function(header) {
                        const group = header.closest('.ifc-group');
                        const content = group.querySelector('.ifc-content');
                        
                        if (!content.classList.contains('collapsed')) {
                            header.classList.add('collapsed');
                            content.classList.add('collapsed');
                        }
                    });
                });
                
                // Обработчик для кнопки "Развернуть все"
                document.getElementById('expand-all').addEventListener('click', function() {
                    headers.forEach(function(header) {
                        const group = header.closest('.ifc-group');
                        const content = group.querySelector('.ifc-content');
                        
                        if (content.classList.contains('collapsed')) {
                            header.classList.remove('collapsed');
                            content.classList.remove('collapsed');
                        }
                    });
                });
                
                // Обработка fail percent элементов с N/A
                const failPercentElements = document.querySelectorAll('.fail.percent');
                failPercentElements.forEach(function(element) {
                    const text = element.textContent || element.innerText;
                    if (text.includes('N/A') || text.includes('N/A%')) {
                        element.classList.add('na-result');
                        element.title = 'N/A результат - проверка пропущена';
                    }
                });
            });
        '''
        head_tag.append(script_tag)

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
        for index, (ifc_name, group_files) in enumerate(ifc_groups.items(), 1):
            # Создаём контейнер для группы IFC файлов
            ifc_group_div = BeautifulSoup().new_tag('div', attrs={'class': 'ifc-group'})
            
            # Добавляем заголовок IFC файла
            ifc_header = BeautifulSoup().new_tag('h1', attrs={'class': 'ifc-header'})
            ifc_header.string = f'#{index} - {ifc_name}.ifc'
            ifc_group_div.append(ifc_header)

            # Создаём контейнер для содержимого группы
            ifc_content_div = BeautifulSoup().new_tag('div', attrs={'class': 'ifc-content'})

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

                # Получение даты последнего изменения файла
                file_modification_time = datetime.fromtimestamp(os.path.getmtime(input_filename))
                date_str = file_modification_time.strftime("%d.%m.%y - %H:%M:%S")

                link_tag = soup.new_tag('a')
                link_tag['href'] = os.path.basename(input_filename)
                link_tag['target'] = '_blank'
                link_tag.string = f'Ссылка на отчёт (от {date_str})'

                container_div = soup.find('div', {'class': 'container'})
                p_tag = None
                if container_div is not None:
                    # Проверяем содержимое container на наличие N/A%
                    container_text = container_div.get_text()
                    # Обрабатываем fail percent элементы с N/A
                    fail_percent_elements = container_div.find_all(class_=['fail', 'percent'])
                    for element in fail_percent_elements:
                        if 'fail' in element.get('class', []) and 'percent' in element.get('class', []):
                            element_text = element.get_text()
                            if 'N/A' in element_text or 'N/A%' in element_text:
                                element['class'] = element.get('class', []) + ['na-result']
                                element['title'] = 'N/A результат - проверка пропущена'
                    
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

                # Добавляем отчёт в контейнер содержимого
                ifc_content_div.append(report_item_div)

            # Добавляем контейнер содержимого в группу
            ifc_group_div.append(ifc_content_div)

            # Добавляем группу в body
            body_tag.append(ifc_group_div)

        # Добавление кнопок управления спойлерами
        controls_div = BeautifulSoup().new_tag('div', attrs={'class': 'controls'})
        collapse_all_btn = BeautifulSoup().new_tag('button', attrs={'class': 'control-btn', 'id': 'collapse-all'})
        collapse_all_btn.string = '▲ Свернуть все'
        expand_all_btn = BeautifulSoup().new_tag('button', attrs={'class': 'control-btn', 'id': 'expand-all'})
        expand_all_btn.string = '▼ Развернуть все'
        
        controls_div.append(collapse_all_btn)
        controls_div.append(expand_all_btn)
        body_tag.append(controls_div)

        consolidated_soup.append(body_tag)

        # Сохранение сводного отчета
        output_file_path = f'{input_dir}/{output_filename}.html'
        Parser_html.save_consolidated_html(consolidated_soup, output_file_path)


if __name__ == '__main__':
    # Проверка работы функции
    input_dir = r'c:\Users\...\reports'
    output_filename = 'Сводный отчет'
    Parser_html.get_consolidated_html(input_dir, output_filename)