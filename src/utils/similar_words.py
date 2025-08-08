import re
from langdetect import detect
import pymorphy2
import spacy
from rapidfuzz import fuzz

morph = pymorphy2.MorphAnalyzer()
nlp = spacy.load("en_core_web_sm")

def is_russian_word(word: str) -> bool:
    return bool(re.search("[а-яА-Я]", word))

def lemmatize_word(word: str) -> str:
    if is_russian_word(word):
        parsed = morph.parse(word.lower())
        if parsed:  
            return parsed[0].normal_form
        return word.lower()
    else:
        doc = nlp(word.lower())
        if doc:
            return " ".join([token.lemma_ for token in doc])
        return word.lower()

def normalize_text(text: str) -> str:
    words = re.findall(r'\w+', text)
    lemmas = [lemmatize_word(word) for word in words]
    return " ".join(lemmas)

def similarity_percentage(channel_name: str, keyword: str) -> float:
    norm_channel = normalize_text(channel_name)
    norm_keyword = normalize_text(keyword)
    # Используем fuzzy ratio из rapidfuzz (0-100)
    score = fuzz.ratio(norm_channel, norm_keyword)
    return score

# Пример использования:
if __name__ == "__main__":
    channel = "Python-разработка и обучение"
    keyword = "Python-разработка и обучения"
    print(f"Схожесть: {similarity_percentage(channel, keyword)}%")
    print(f"Схожесть: {similarity_percentage(channel, keyword)}%")
