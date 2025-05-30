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

        processed_styles = set()  # Множество для записи настроек стиля

        for input_filename in input_filenames:  # Цикл для обработки файлов отчетов
            soup = Parser_html.parse_html(input_filename)  # Получение файла html

            for style in soup.find_all('style'):  # Цикл для обработки элементов в теге <style>
                style_content = style.get_text(strip=True)
                if style_content not in processed_styles:
                    new_style = BeautifulSoup().new_tag('style')
                    new_style.string = style.get_text()
                    head_tag.append(new_style)
                    processed_styles.add(style_content)

            # Получение содержимого тегов <h2> <div> <p>
            h2_tag = soup.find('h2')
            if h2_tag is not None:
                h2_tag.string = os.path.basename(input_filename).replace('.html', '')
            else:
                h2_tag = soup.new_tag('h2')
                h2_tag.string = os.path.basename(input_filename).replace('.html', '') + " (нет заголовка)"

            link_tag = soup.new_tag('a')
            link_tag['href'] = os.path.basename(input_filename)
            link_tag.string = 'Ссылка'

            container_div = soup.find('div', {'class': 'container'})
            p_tag = None
            if container_div is not None:
                p_tag = container_div.find_next('p')

            hr_tag = soup.new_tag("hr")

            # Добавление в body: всегда добавляем хотя бы заголовок и ссылку
            body_tag.append(h2_tag)
            body_tag.append(link_tag)
            if container_div is not None:
                body_tag.append(container_div)
            else:
                empty_div = soup.new_tag('div')
                empty_div.string = "Нет блока container в отчете"
                body_tag.append(empty_div)
            if p_tag is not None:
                body_tag.append(p_tag)
            body_tag.append(hr_tag)

        consolidated_soup.append(body_tag)

        # Сохранение сводного отчета
        output_file_path = f'{input_dir}/{output_filename}.html'
        Parser_html.save_consolidated_html(consolidated_soup, output_file_path)


if __name__ == '__main__':
    # Проверка работы функции
    input_dir = r'c:\Users\...\reports'
    output_filename = 'Сводный отчет'
    Parser_html.get_consolidated_html(input_dir, output_filename)