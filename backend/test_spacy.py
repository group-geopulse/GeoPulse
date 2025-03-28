import spacy
nlp = spacy.load("en_core_web_lg")
doc = nlp("This is a test sentence.")
print([(ent.text, ent.label_) for ent in doc.ents])