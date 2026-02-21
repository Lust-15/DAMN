import sys
from natasha import (
    Segmenter,
    NewsEmbedding,
    NewsNERTagger,
    MorphVocab,
    Doc
)


def load_natasha_models():
    try:
        segmenter = Segmenter()
        emb = NewsEmbedding()
        ner_tagger = NewsNERTagger(emb)
        morph_vocab = MorphVocab()
        return segmenter, ner_tagger, morph_vocab
    except Exception as e:
        print(f"Ошибка загрузки моделей Natasha: {e}")
        print("Убедитесь, что установлены: pip install natasha navec pymorphy2 razdel")
        sys.exit(1)


def extract_entities(text, segmenter, ner_tagger, morph_vocab):
    """
    Извлекает именованные сущности из текста.
    Возвращает словарь: {тип_сущности: множество(лемматизированных_текстов)}
    и список словарей с детальной информацией (текст, тип, лемма, предложение).
    """
    doc = Doc(text)
    doc.segment(segmenter)
    doc.tag_ner(ner_tagger)

    entities = {}
    details = []

    for span in doc.spans:
        # лемматизация
        span.normalize(morph_vocab)
        entity_type = span.type
        entity_text = span.text
        entity_normal = span.normal

        # собираем по категориям
        if entity_type not in entities:
            entities[entity_type] = set()
        entities[entity_type].add(entity_normal)

        # находим предложение, в котором находится сущность
        sentence = ""
        for sent in doc.sents:
            if span.start >= sent.start and span.stop <= sent.stop:
                sentence = sent.text
                break

        details.append({
            'text': entity_text,
            'normal': entity_normal,
            'type': entity_type,
            'sentence': sentence.strip()
        })

    return entities, details


def compare_entities(ref_entities, test_entities):
    """
    Сравнивает множества сущностей эталона и проверяемого текста.
    Возвращает словарь с пропущенными и лишними сущностями.
    """
    result = {}
    all_types = set(ref_entities.keys()) | set(test_entities.keys())

    for typ in all_types:
        ref_set = ref_entities.get(typ, set())
        test_set = test_entities.get(typ, set())

        missing = ref_set - test_set
        extra = test_set - ref_set

        if missing or extra:
            result[typ] = {
                'missing': sorted(missing),
                'extra': sorted(extra)
            }

    return result


def print_report(ref_details, test_details, comparison):
    """Выводит отчёт о сравнении сущностей."""
    print("\n" + "=" * 80)
    print("ОТЧЁТ СРАВНЕНИЯ ТЕКСТОВ (NER-уровень)")
    print("=" * 80)

    # Статистика
    ref_count = sum(
        len(set(d['normal'] for d in ref_details if d['type'] == t)) for t in set(d['type'] for d in ref_details))
    test_count = sum(
        len(set(d['normal'] for d in test_details if d['type'] == t)) for t in set(d['type'] for d in test_details))

    print(f"\n📊 Статистика:")
    print(f"  Сущностей в эталонном тексте: {ref_count}")
    print(f"  Сущностей в проверяемом тексте: {test_count}")
    print(f"  Категории с расхождениями: {len(comparison)}")

    if not comparison:
        print("\n✅ Все именованные сущности совпадают!")
        return

    # Детали по категориям
    for typ, diffs in comparison.items():
        print(f"\n🔹 Категория: {typ}")

        if diffs['missing']:
            print(f"  ❌ Пропущено (есть в эталоне, нет в проверяемом):")
            for ent in diffs['missing']:
                # ищем контекст в эталонном тексте
                ctx = next((d['sentence'] for d in ref_details if d['normal'] == ent and d['type'] == typ), '')
                print(f"    - {ent}")
                if ctx:
                    print(f"      Контекст: {ctx[:100]}...")

        if diffs['extra']:
            print(f"  ⚠️  Лишнее (есть в проверяемом, нет в эталоне):")
            for ent in diffs['extra']:
                ctx = next((d['sentence'] for d in test_details if d['normal'] == ent and d['type'] == typ), '')
                print(f"    - {ent}")
                if ctx:
                    print(f"      Контекст: {ctx[:100]}...")

    print("\n" + "=" * 80)


def read_multiline_input(prompt):
    """Читает многострочный ввод от пользователя до пустой строки."""
    print(prompt)
    print("(Введите текст, для завершения оставьте пустую строку и нажмите Enter)")
    lines = []
    while True:
        line = input()
        if line == "":
            break
        lines.append(line)
    return "\n".join(lines)


def main():
    print("🔍 Анализ текстов с помощью NER (библиотека Natasha)")
    print("=" * 80)

    # Загрузка моделей
    print("Загрузка NLP-моделей...")
    segmenter, ner_tagger, morph_vocab = load_natasha_models()
    print("Модели загружены.\n")

    # Ввод эталонного текста
    ref_text = read_multiline_input("Введите ЭТАЛОННЫЙ текст (второй текст, где всё верно):")
    if not ref_text.strip():
        print("Ошибка: эталонный текст не может быть пустым.")
        sys.exit(1)

    # Ввод проверяемого текста
    test_text = read_multiline_input("Введите ПРОВЕРЯЕМЫЙ текст (первый текст, который нужно проверить):")
    if not test_text.strip():
        print("Ошибка: проверяемый текст не может быть пустым.")
        sys.exit(1)

    # Извлечение сущностей
    print("\nОбработка текстов...")
    ref_entities, ref_details = extract_entities(ref_text, segmenter, ner_tagger, morph_vocab)
    test_entities, test_details = extract_entities(test_text, segmenter, ner_tagger, morph_vocab)

    # Сравнение
    comparison = compare_entities(ref_entities, test_entities)

    # Вывод отчёта
    print_report(ref_details, test_details, comparison)


if __name__ == "__main__":
    main()