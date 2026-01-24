import requests
from bs4 import BeautifulSoup
import re


def extract_all_text(url):
    """Извлечение всего текста с веб-страницы"""
    try:
        # Заголовки для имитации браузера
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        # Загружаем страницу
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        # Парсим HTML
        soup = BeautifulSoup(response.content, 'html.parser')

        # Удаляем ненужные теги (скрипты, стили и т.д.)
        for tag in soup(['script', 'style', 'iframe', 'noscript', 'meta', 'link']):
            tag.decompose()

        # Получаем весь текст
        all_text = soup.get_text(separator='\n', strip=True)

        # Удаляем лишние пустые строки и пробелы
        cleaned_text = re.sub(r'\n\s*\n', '\n\n', all_text)
        cleaned_text = re.sub(r'\s{2,}', ' ', cleaned_text)

        return cleaned_text

    except Exception as e:
        return f"Ошибка при загрузке страницы: {e}"


def main():
    print("=== ПРОСТОЙ ТЕКСТОВЫЙ ЭКСТРАКТОР ===")
    print("Получает весь текст с веб-страницы")
    print("=" * 40)

    while True:
        url = input("\nВведите URL (или 'выход'): ").strip()

        if url.lower() in ['выход', 'exit', 'quit', '']:
            print("Программа завершена.")
            break

        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url

        print("\nЗагружаю и обрабатываю страницу...\n")

        # Извлекаем текст
        text = extract_all_text(url)

        # Выводим результат
        print("=" * 60)
        print(text)
        print("=" * 60)

        # Показываем статистику
        lines = text.split('\n')
        words = text.split()
        print(f"\nСтатистика: {len(lines)} строк, {len(words)} слов, {len(text)} символов")


if __name__ == "__main__":
    main()