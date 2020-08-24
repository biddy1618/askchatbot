"""Some utility functions for using spacy with pandas"""
import spacy
import pandas as pd


def pd_tokens_from_spacy(nlp, text):
    """Processes the text with spacy and returns a MultiIndex pandas dataframe:
    MultiIndex:
        - s-id: sentence id
        - t-id: token id within the sentence
    
    Columns:
        ... : token attributes
    """
    token_attributes = [
        "text",
        "tag_",
        "pos_",
        "lemma_",
        "idx",
        "text_with_ws",
        "is_alpha",
        "is_punct",
        "is_space",
        "shape_",
        "is_stop",
    ]

    data = {}
    data["s-id"] = []
    data["t-id"] = []
    for token_attribute in token_attributes:
        data[token_attribute] = []
        if token_attribute == "tag_":
            data["tag_explained"] = []
    for sentence_id, sentence in enumerate(nlp(text).sents):
        data["s-id"].extend([sentence_id] * len(sentence))
        data["t-id"].extend(range(len(sentence)))
        for token_attribute in token_attributes:
            data[token_attribute].extend(
                [getattr(token, token_attribute) for token in sentence]
            )
            if token_attribute == "tag_":
                data["tag_explained"].extend(
                    [spacy.explain(token.tag_) for token in sentence]
                )

    df = pd.DataFrame(data)
    df = df.set_index(["s-id", "t-id"])
    return df


def is_this_a_question(sentence):
    """Returns True if it is a question, else False"""
    text = sentence.text.strip().lower()

    if text[-1] == "?":
        return True

    for word in [
        "is",
        "does",
        "do",
        "what",
        "when",
        "where",
        "who",
        "why",
        "what",
        "how",
    ]:
        if text.startswith(word):
            return True

    return False


def pd_sentences_from_spacy(nlp, text):
    """Processes the text with spacy and returns a pandas dataframe:
    Index:
        - s-id : sentence id
    
    Column:
        - sentence
        - is-question: True/False
    """

    sentences = list(nlp(text).sents)

    data = {}
    data["s-id"] = list(range(len(sentences)))
    data["sentence"] = [sentence.text for sentence in sentences]
    data["is_question"] = [is_this_a_question(sentence) for sentence in sentences]

    df = pd.DataFrame(data)
    df = df.set_index(["s-id"])
    return df


def pd_noun_chunks_from_spacy(nlp, text):
    """Processes the text with spacy and returns a MultiIndex pandas dataframe:
    MultiIndex:
        - s-id : sentence id
        - nc-id: noun chunk id within the sentence
    
    Column:
        - noun-chunk
    """

    data = {}
    data["s-id"] = []
    data["nc-id"] = []
    data["noun-chunk"] = []

    for sentence_id, sentence in enumerate(nlp(text).sents):
        chunks = list(nlp(sentence.text).noun_chunks)
        data["noun-chunk"].extend(chunks)
        data["s-id"].extend([sentence_id] * len(chunks))
        data["nc-id"].extend(range(len(chunks)))

    df = pd.DataFrame(data)
    df = df.set_index(["s-id", "nc-id"])
    return df


def pd_entities_from_spacy(nlp, text):
    """Processes the text with spacy and returns a MultiIndex pandas dataframe:
    MultiIndex:
        - s-id: sentence id
        - e-id: entity id within the sentence
    
    Columns:
        ... : entity attributes
    """
    entity_attributes = [
        "text",
        "start_char",
        "end_char",
        "label_",
    ]

    data = {}
    data["s-id"] = []
    data["e-id"] = []
    for entity_attribute in entity_attributes:
        data[entity_attribute] = []
        if entity_attribute == "label_":
            data["label_explained"] = []
    for sentence_id, sentence in enumerate(nlp(text).sents):
        entities = list(nlp(sentence.text).ents)
        data["s-id"].extend([sentence_id] * len(entities))
        data["e-id"].extend(range(len(entities)))
        for entity_attribute in entity_attributes:
            data[entity_attribute].extend(
                [getattr(entity, entity_attribute) for entity in entities]
            )
            if entity_attribute == "label_":
                data["label_explained"].extend(
                    [spacy.explain(entity.label_) for entity in entities]
                )

    df = pd.DataFrame(data)
    df = df.set_index(["s-id", "e-id"])
    return df
