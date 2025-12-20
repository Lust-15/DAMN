import re
def find_capitalized_words(text):
    text = re.sub(r'\s+', ' ', text.strip())
    sentences = re.split(r'(?<=[.!?])\s+', text)
    result = []
    for sentence in sentences:
        if not sentence:
            continue
        words = sentence.split()
        if len(words) == 0:
            continue
        for word in words[1:]:
            if (word and word[0].isupper() and
                    any(c.isalpha() for c in word)):
                clean_word = re.sub(r'[.,!?;:]$', '', word)
                if clean_word and clean_word[0].isupper():
                    if len(clean_word) > 1:
                        result.append(clean_word)

    return result

text = """АНКАРА, 20 дек – РИА Новости. Турция принимает дополнительные меры для защиты критически
 важных надводных и подводных объектов в Чёрном море на фоне инцидентов с беспилотными летательными
  аппаратами (БПЛА), заявил министр национальной обороны республики Яшар Гюлер.
Ранее министерство обороны Турции сообщило, что беспилотник, предположительно вышедший из-под контроля,
 был сбит истребителем F-16 в турецком воздушном пространстве над Чёрным морем. При этом принадлежность
  БПЛА не уточнялась."""

result = find_capitalized_words(text)
print(result)