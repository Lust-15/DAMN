import requests
from bs4 import BeautifulSoup


def get_article_text_by_exact_class(url):
    """Ищет текст в элементах с точным классом article__text"""
    try:
        # Загружаем страницу
        response = requests.get(url)
        response.encoding = 'utf-8'

        # Парсим HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        article_divs = soup.select('div.article__text,p.topic-body__content-text')

        # Собираем текст из найденных элементов
        all_text = []
        for div in article_divs:
            # Получаем весь текст из div, включая вложенные элементы
            text = div.get_text(separator='\n', strip=False)
            if text and text.strip():  # Проверяем, что текст не пустой
                # Очищаем текст от лишних пробелов
                cleaned_text = '\n'.join(line.strip() for line in text.split('\n') if line.strip())
                all_text.append(cleaned_text)

        if all_text:
            # Объединяем все найденные тексты
            result_text = "\n\n" + "\n\n".join(all_text) + "\n\n"
            return result_text
        else:
            return f"Элементов <div class='article__text'> не найдено на странице {url}"

    except Exception as e:
        return f"Ошибка: {e}"
# Основная программа
url = input("\nВведите URL сайта: ").strip()

# Проверяем URL
if not url.startswith(('http://', 'https://')):
    url = 'https://' + url
# Получаем текст из article__text
article_text = get_article_text_by_exact_class(url)
if "Элементов <div class='article__text'> не найдено" in article_text or "Ошибка:" in article_text:
    print(article_text)
    print("\n" + "=" * 70)
else:
    print(article_text)
