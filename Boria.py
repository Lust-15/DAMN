import re
from collections import Counter
from typing import Dict, List, Tuple, Set
import itertools


class TextComparator:
    def __init__(self):
        # Паттерны для поиска фактов
        self.patterns = {
            'dates': r'\b\d{1,2}[./]\d{1,2}[./]\d{2,4}\b|\b\d{4}\s*года?\b|\b(?:января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)\s+\d{1,4}\b',
            'numbers': r'\b\d+[.,]?\d*\b',
            'money': r'\b\d+\s*(?:тыс|млн|млрд|триллион)[а-я]*\b|\$\s?\d+|€\s?\d+|\d+\s*(?:доллар|евро|рубл)[ейа-я]*\b',
            'percentages': r'\b\d+[.,]?\d*\s*%|\b\d+[.,]?\d*\s*процент[а-ов]*\b',
            'names': r'\b[А-ЯЁ][а-яё]+\s+[А-ЯЁ][а-яё]+(?:\s+[А-ЯЁ][а-яё]+)?\b',
            'organizations': r'(?:ООО|ЗАО|АО|ПАО|ИП|ОАО)\s*[«"](?:[^»"]+)[»"]|\b[А-ЯЁ]{2,}\b(?:\s[А-ЯЁ]{2,})*',
        }

    def extract_facts(self, text: str) -> Dict[str, List[str]]:
        """Извлекает факты из текста по категориям"""
        facts = {}
        for category, pattern in self.patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            # Фильтруем ложные срабатывания
            if category == 'numbers':
                matches = [m for m in matches if len(m) > 1 or m in '0123456789']
            facts[category] = sorted(set(matches))  # убираем дубликаты
        return facts

    def normalize_text(self, text: str) -> str:
        """Нормализует текст для сравнения"""
        # Приводим к нижнему регистру, убираем лишние пробелы и пунктуацию
        text = text.lower()
        text = re.sub(r'[^\w\s.,!?-]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def find_sentences_with_facts(self, text: str, facts_dict: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """Находит предложения, содержащие факты"""
        sentences = re.split(r'[.!?]+', text)
        result = {}

        for category, facts in facts_dict.items():
            result[category] = []
            for sentence in sentences:
                sentence_lower = sentence.lower()
                for fact in facts:
                    fact_lower = fact.lower()
                    # Проверяем, есть ли факт в предложении (частичное совпадение для чисел и дат)
                    if category in ['dates', 'numbers', 'money', 'percentages']:
                        # Для чисел ищем точное совпадение в границах слова
                        if re.search(r'\b' + re.escape(fact_lower) + r'\b', sentence_lower):
                            result[category].append(sentence.strip())
                            break
                    elif fact_lower in sentence_lower:
                        result[category].append(sentence.strip())
                        break

        return result

    def compare_texts(self, text1: str, text2: str, detailed: bool = True) -> Dict:
        """
        Сравнивает два текста и находит неточности в первом

        Args:
            text1: Текст для проверки
            text2: Эталонный текст
            detailed: Подробный отчет

        Returns:
            Словарь с результатами сравнения
        """
        # Извлекаем факты из обоих текстов
        facts1 = self.extract_facts(text1)
        facts2 = self.extract_facts(text2)

        # Находим предложения с фактами
        sentences1 = self.find_sentences_with_facts(text1, facts1)
        sentences2 = self.find_sentences_with_facts(text2, facts2)

        # Сравниваем факты по категориям
        discrepancies = {
            'missing_facts': {},  # Факты, которые есть во втором тексте, но отсутствуют в первом
            'different_facts': {},  # Факты, которые различаются
            'extra_facts': {},  # Факты, которые есть в первом тексте, но отсутствуют во втором
            'similar_sentences': [],  # Похожие предложения с разными фактами
        }

        # Сравниваем каждую категорию фактов
        for category in self.patterns.keys():
            set1 = set(facts1.get(category, []))
            set2 = set(facts2.get(category, []))

            # Факты, которые есть в эталоне, но отсутствуют в проверяемом тексте
            missing = set2 - set1
            if missing:
                discrepancies['missing_facts'][category] = list(missing)

            # Факты, которые есть только в проверяемом тексте (возможно, ошибочные)
            extra = set1 - set2
            if extra:
                discrepancies['extra_facts'][category] = list(extra)

            # Общие факты (возможно, с разными значениями - проверяем нормализацию)
            common = set1 & set2

            # Для общих фактов проверяем контекст
            for fact in common:
                sent1_list = [s for s in sentences1.get(category, []) if fact.lower() in s.lower()]
                sent2_list = [s for s in sentences2.get(category, []) if fact.lower() in s.lower()]

                if sent1_list and sent2_list:
                    sent1 = sent1_list[0]
                    sent2 = sent2_list[0]

                    # Если предложения сильно различаются по смыслу
                    if detailed and self.normalize_text(sent1) != self.normalize_text(sent2):
                        discrepancies['similar_sentences'].append({
                            'fact': fact,
                            'sentence_in_text1': sent1,
                            'sentence_in_text2': sent2,
                            'category': category
                        })

        # Поиск противоречий в предложениях с одинаковыми фактами
        contradictions = []
        if detailed:
            for item in discrepancies['similar_sentences']:
                contradictions.append(f"Факт: {item['fact']} ({item['category']})")
                contradictions.append(f"В тексте 1: {item['sentence_in_text1']}")
                contradictions.append(f"В тексте 2: {item['sentence_in_text2']}")
                contradictions.append("-" * 50)

        # Подсчет статистики
        stats = {
            'total_facts_in_text1': sum(len(v) for v in facts1.values()),
            'total_facts_in_text2': sum(len(v) for v in facts2.values()),
            'missing_facts_count': sum(len(v) for v in discrepancies['missing_facts'].values()),
            'extra_facts_count': sum(len(v) for v in discrepancies['extra_facts'].values()),
            'contradictions_count': len(discrepancies['similar_sentences']),
        }

        return {
            'discrepancies': discrepancies,
            'statistics': stats,
            'contradictions_text': '\n'.join(contradictions) if contradictions else "Прямых противоречий не найдено",
            'facts_text1': facts1,
            'facts_text2': facts2,
        }

    def print_report(self, comparison_result: Dict):
        """Печатает понятный отчет о сравнении"""
        result = comparison_result

        print("=" * 80)
        print("АНАЛИЗ ТЕКСТОВ: НЕТОЧНОСТИ В ПЕРВОМ ТЕКСТЕ")
        print("=" * 80)

        print("\n📊 СТАТИСТИКА:")
        print(f"Фактов в проверяемом тексте: {result['statistics']['total_facts_in_text1']}")
        print(f"Фактов в эталонном тексте: {result['statistics']['total_facts_in_text2']}")
        print(f"Пропущенных фактов: {result['statistics']['missing_facts_count']}")
        print(f"Лишних фактов (возможные ошибки): {result['statistics']['extra_facts_count']}")
        print(f"Найдено противоречий: {result['statistics']['contradictions_count']}")

        if result['statistics']['missing_facts_count'] > 0:
            print("\n🔴 ПРОПУЩЕННЫЕ ФАКТЫ (есть во втором тексте, нет в первом):")
            for category, facts in result['discrepancies']['missing_facts'].items():
                if facts:
                    print(f"\n{category.upper()}:")
                    for fact in facts:
                        print(f"  - {fact}")

        if result['statistics']['extra_facts_count'] > 0:
            print("\n🟡 ЛИШНИЕ ФАКТЫ (есть в первом тексте, но нет во втором - проверьте!):")
            for category, facts in result['discrepancies']['extra_facts'].items():
                if facts:
                    print(f"\n{category.upper()}:")
                    for fact in facts:
                        print(f"  - {fact}")

        print("\n⚡ ПРОТИВОРЕЧИЯ В КОНТЕКСТЕ:")
        print(result['contradictions_text'])

        print("\n" + "=" * 80)
        print("Для ручной проверки:")
        print("1. Проверьте все даты и числа")
        print("2. Убедитесь, что имена и названия написаны правильно")
        print("3. Проверьте контекст - одинаковые факты могут использоваться по-разному")
        print("=" * 80)


# Пример использования
def main():
    # Пример текстов
    text1 = """
    МОСКВА, 7 фев — РИА Новости.
Тегеран не будет обсуждать свою ракетную программу, заявил телеканалу
Al Jazeera
глава МИД Ирана Аббас Аракчи.

Также министр исключил вывоз обогащенного урана из страны. По его словам, точная дата второго раунда переговоров пока не определена.

Аракчи добавил, что
Иран
ответит ударами по американским базам в районе Персидского залива в случае атаки со стороны США.

Переговоры Вашингтона и Тегерана по ядерной тематике прошли накануне в
Маскате
. Стороны договорились продолжить диалог, но сначала проведут консультации в столицах. Иран на переговорах представлял Аракчи, а Штаты — спецпосланник Стивен Уиткофф.

Контакты сторон стали первыми после ирано-израильского конфликта в июне 2025 года. К тому моменту Тегеран и Вашингтон провели пять раундов консультаций.

В конце января глава Белого дома
Дональд Трамп
сообщил, что США перебрасывают к Ирану более сильную армаду кораблей, чем была у берегов Венесуэлы. По его словам, власти республики хотят заключить сделку по ядерной программе и только они знают, есть ли для этого крайний срок.

Со своей стороны, иранские власти призывали возобновить диалог по ядерной тематике на принципах равенства и взаимоуважения.

Как сообщала NYT, в случае провала переговоров США допускают удары по ядерным и ракетным объектам, операции, направленные на ослабление руководства страны, а также возможность рейдов американских сил на территорию Ирана. Источники уточнили, что Трамп пока не санкционировал операцию и не сделал окончательный выбор из предложенных вариантов.

Тегеран заявил о готовности ответить на любую попытку атаки со стороны США, даже ограниченную: дальности иранских ракет хватит, чтобы долететь до американских баз в регионе.
    """

    text2 = """
    Иран не будет обсуждать свою ракетную программу - МИДИран не будет обсуждать свою ракетную программу - МИД
    Иран не собирается обсуждать свою ракетную программу ни сейчас, ни в будущем, это касающийся обороны вопрос, заявил глава МИД Ирана Аббас Аракчи телеканалу Al Jazeera.
"Мы не можем вести переговоры по ракетам ни сейчас, ни в будущем, поскольку это вопрос обороны", - сказал министр.
Он добавил, что Иран ответит нападением на американские базы в регионе Персидского залива в случае атаки со стороны США.
 
"У нас нет возможности атаковать американскую территорию, если Вашингтон нападет на нас, то мы будем атаковать его базы в регионе", - сказал Аракчи.
 
Также он заявил, что обогащенный уран не будут вывозить из Ирана.
"Степень обогащения урана зависит от наших потребностей. Обогащенный уран не покидает территорию Ирана", - сказал министр.
По его словам, делегации Ирана и США в ходе переговоров в Омане имели возможность пожать руки друг другу, несмотря на непрямой характер встречи. Аракчи отметил, что решение по проблеме иранской ядерной программы можно найти только путем переговоров.
 
 
В пятницу в оманской столице Маскате прошли переговоры между делегациями США и Ирана, чтобы решить между сторонами разногласия по иранской ядерной программе.
Россия готова внести свой вклад в решение проблемы с запасами обогащенного урана в Иране, если и когда Вашингтону и Тегерану удастся договориться об урегулировании кризиса, заявил в четверг глава МИД РФ Сергей Лавров.
Встреча Ирана и США при посредничестве Омана прошла в пятницу впервые после многомесячной паузы в переговорном процессе, возникшей из-за открытой фазы ирано-израильского конфликта в июне 2025 года. Исламская республика и Соединенные Штаты к тому времени провели пять раундов консультаций.
    """

    comparator = TextComparator()
    result = comparator.compare_texts(text1, text2, detailed=True)
    comparator.print_report(result)

    # Пример с пользовательскими текстами
    print("\n\n" + "=" * 80)
    print("ХОТИТЕ ПРОВЕРИТЬ СВОИ ТЕКСТЫ?")
    print("=" * 80)

    use_custom = input("\nИспользовать свои тексты? (y/n): ").lower()

    if use_custom == 'y':
        print("\nВведите ПЕРВЫЙ текст (который нужно проверить):")
        print("(Введите 'END' на отдельной строке для завершения)")
        lines1 = []
        while True:
            line = input()
            if line.strip() == 'END':
                break
            lines1.append(line)
        custom_text1 = '\n'.join(lines1)

        print("\nВведите ВТОРОЙ текст (эталонный):")
        print("(Введите 'END' на отдельной строке для завершения)")
        lines2 = []
        while True:
            line = input()
            if line.strip() == 'END':
                break
            lines2.append(line)
        custom_text2 = '\n'.join(lines2)

        if custom_text1 and custom_text2:
            print("\n" + "=" * 80)
            print("АНАЛИЗ ВАШИХ ТЕКСТОВ...")
            print("=" * 80)
            result = comparator.compare_texts(custom_text1, custom_text2, detailed=True)
            comparator.print_report(result)


if __name__ == "__main__":
    main()