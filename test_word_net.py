from nltk.corpus import wordnet

def expand_query_with_wordnet(query):
    expanded_query = []
    for term in query.split():
        synonyms = []
        for syn in wordnet.synsets(term):
            synonyms.extend(syn.lemma_names())
        synonyms=list(set([term.lower() for term in synonyms]))
        expanded_query.extend(list(set(synonyms)))
    return expanded_query

# Example usage:
query = "car in town"
expanded_query = expand_query_with_wordnet(query)
print("Expanded query:", expanded_query)