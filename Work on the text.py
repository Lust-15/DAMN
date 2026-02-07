import pymorphy3
import re
from collections import Counter


class KeywordFinder:
    def __init__(self, keywords_list):
        """
        Инициализация поисковика ключевых слов

        Args:
            keywords_list (list): Список ключевых слов в начальной форме
        """
        self.morph = pymorphy3.MorphAnalyzer()
        self.keywords_base_forms = set(keywords_list)

        # Создаем формы для каждого ключевого слова
        self.keyword_forms = self._prepare_keyword_forms(keywords_list)

    def _prepare_keyword_forms(self, keywords):
        """Создает все возможные формы для ключевых слов"""
        keyword_forms = {}

        for word in keywords:
            parsed = self.morph.parse(word)[0]
            # Для существительных
            if 'NOUN' in parsed.tag:
                forms = set()
                # Добавляем разные падежи и числа
                for case in ['nomn', 'gent', 'datv', 'accs', 'ablt', 'loct']:
                    for number in ['sing', 'plur']:
                        try:
                            form = parsed.inflect({case, number})
                            if form:
                                forms.add(form.word.lower())
                        except:
                            pass
                keyword_forms[word] = forms
            # Для глаголов
            elif 'VERB' in parsed.tag or 'INFN' in parsed.tag:
                forms = set()
                # Добавляем разные формы глагола
                for tense in ['pres', 'past']:
                    for person in ['1per', '2per', '3per']:
                        for number in ['sing', 'plur']:
                            try:
                                form = parsed.inflect({tense, person, number})
                                if form:
                                    forms.add(form.word.lower())
                            except:
                                pass
                keyword_forms[word] = forms

            # Для прилагательных
            elif 'ADJF' in parsed.tag or 'ADJS' in parsed.tag:
                forms = set()
                for case in ['nomn', 'gent', 'datv', 'accs', 'ablt', 'loct']:
                    for number in ['sing', 'plur']:
                        for gender in ['masc', 'femn', 'neut']:
                            try:
                                form = parsed.inflect({case, number, gender})
                                if form:
                                    forms.add(form.word.lower())
                            except:
                                pass
                keyword_forms[word] = forms
            # Для других частей речи
            else:
                forms = {word.lower()}
                try:
                    # Пробуем разные формы
                    for form in [word, parsed.normal_form]:
                        if form:
                            forms.add(form.lower())
                except:
                    pass
                keyword_forms[word] = forms

        return keyword_forms

    def find_keywords(self, text, include_counts=False):
        """
        Ищет ключевые слова в тексте

        Args:
            text (str): Текст для анализа
            include_counts (bool): Включать ли подсчет частоты

        Returns:
            dict или list: Найденные ключевые слова
        """
        # Очищаем текст от лишних символов
        text_clean = re.sub(r'[^\w\s-]', ' ', text.lower())
        words = re.findall(r'\b\w+\b', text_clean)

        found_keywords = Counter()
        # Поиск ключевых слов
        for word in words:
            # Приводим слово к нормальной форме
            parsed = self.morph.parse(word)[0]
            normal_form = parsed.normal_form.lower()

            # Проверяем прямое совпадение с ключевыми словами
            if normal_form in self.keywords_base_forms:
                found_keywords[normal_form] += 1
                continue

            # Проверяем совпадение с формами ключевых слов
            for keyword, forms in self.keyword_forms.items():
                if word.lower() in forms:
                    found_keywords[keyword] += 1
                    break

        if include_counts:
            return dict(found_keywords)
        else:
            return list(found_keywords.keys())

    def find_keywords_with_context(self, text, context_words=3):
        """
        Находит ключевые слова с контекстом

        Args:
            text (str): Текст для анализа
            context_words (int): Количество слов контекста с каждой стороны

        Returns:
            list: Список словарей с ключевым словом и контекстом
        """
        # Разбиваем текст на слова с сохранением позиций
        words_with_pos = list(enumerate(re.findall(r'\b\w+\b', text.lower())))
        found_keywords = []

        for idx, word in words_with_pos:
            # Приводим слово к нормальной форме
            parsed = self.morph.parse(word)[0]
            normal_form = parsed.normal_form.lower()

            # Проверяем прямое совпадение
            if normal_form in self.keywords_base_forms:
                # Получаем контекст
                start = max(0, idx - context_words)
                end = min(len(words_with_pos), idx + context_words + 1)

                context = ' '.join([w for _, w in words_with_pos[start:end]])
                found_keywords.append({
                    'keyword': normal_form,
                    'form_found': word,
                    'context': context,
                    'position': idx
                })
                continue

            # Проверяем совпадение с формами
            for keyword, forms in self.keyword_forms.items():
                if word.lower() in forms:
                    # Получаем контекст
                    start = max(0, idx - context_words)
                    end = min(len(words_with_pos), idx + context_words + 1)

                    context = ' '.join([w for _, w in words_with_pos[start:end]])
                    found_keywords.append({
                        'keyword': keyword,
                        'form_found': word,
                        'context': context,
                        'position': idx
                    })
                    break

        return found_keywords


def get_default_keywords():
    """Возвращает список ключевых слов по умолчанию"""
    return ['Политика', 'Президент', 'Правительство', 'Выборы',
            'Голосование', 'Дебаты', 'Власть', 'Парламент',
            'Закон', 'Референдум', 'Соглашение', 'Санкции',
            'Дипломатия', 'Оппозиция', 'Коалиция', 'Экономика',
            'Кризис', 'Безработица', 'Долг', 'Налоги',
            'Инфляция', 'Рынок', 'Инвестиции', 'Бюджет',
            'Курс валют', 'Биржа', 'Компания', 'Банк',
            'Стоимость', 'Цены', 'Катастрофа', 'Протест',
            'Конфликт', 'Война', 'Пожар', 'Терроризм',
            'Беженцы', 'Преступление', 'Коррупция', 'Авария',
            'Суд', 'Расследование', 'Пострадавшие', 'Спасатели',
            'Здоровье', 'Вакцина', 'Вирус', 'Пандемия',
            'Медицина', 'Врачи', 'Наука', 'Исследование',
            'Открытие', 'Технология', 'Инновация', 'Прорыв',
            'Ученые', 'Эксперимент', 'Космос', 'Спорт',
            'Олимпиада', 'Матч', 'Турнир', 'Чемпионат',
            'Футбол', 'Игрок', 'Тренер', 'Культура',
            'Фестиваль', 'Концерт', 'Фильм', 'Артист',
            'Знаменитость', 'Награда', 'Климат', 'Экология',
            'Потепление', 'Загрязнение', 'Выбросы', 'Окружающая среда',
            'Природа', 'Катаклизм', 'Ураган', 'Землетрясение',
            'Засуха', 'Лесные пожары', 'Биоразнообразие', 'Защита',
            'Устойчивое развитие', 'Срочно', 'Новость', 'Фейк',
            'Истина', 'Будущее', 'Цензура', 'Население',
            'Энергия', 'Информация', 'Эксклюзив', 'Заявление',
            'Реакция', 'Последствия', 'Прогноз']


def main():
    """Основная функция программы"""

    # Установите библиотеку если нужно:
    # pip install pymorphy3
    print("ПОИСК КЛЮЧЕВЫХ СЛОВ В ТЕКСТЕ")
    # Используем ключевые слова по умолчанию или свои
    keywords = get_default_keywords()
    # Инициализируем поисковик
    finder = KeywordFinder(keywords)
    print("\nВведите текст для анализа (Ctrl+D для завершения ввода):")
    lines = []
    try:
        while True:
            line = input()
            lines.append(line)
    except EOFError:
        pass
    text = '\n'.join(lines)

    if text:
        analyze_text(finder, text)
    else:
        print("Текст не введен!")



def analyze_text(finder, text):
    """Анализирует текст и выводит результаты"""

    # Статистика текста
    words_count = len(re.findall(r'\b\w+\b', text.lower()))

    # Поиск ключевых слов с подсчетом
    found_keywords = finder.find_keywords(text, include_counts=True)

    if found_keywords:
        print("\nКлючевые слова:")

        # Сортируем по частоте
        sorted_keywords = sorted(found_keywords.items(),
                                 key=lambda x: x[1],
                                 reverse=True)

        for keyword, count in sorted_keywords:
            print(f"{keyword}")

    else:
        print("\nКлючевые слова не найдены!")


if __name__ == "__main__":
    # Установите библиотеку если нужно:
    # pip install pymorphy3

    try:
        import pymorphy3

        main()
    except ImportError:
        print("Ошибка: Библиотека pymorphy3 не установлена!")
        print("Установите её командой: pip install pymorphy3")
        print("Или используйте: pip install pymorphy3[fast] для более быстрой работы")