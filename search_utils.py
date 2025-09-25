import unicodedata

def normalize_word(word):
    return unicodedata.normalize('NFKC', word.lower())

def normal_search(word_list, query):
    query = normalize_word(query)
    return [w for w in word_list if normalize_word(w).startswith(query)]
