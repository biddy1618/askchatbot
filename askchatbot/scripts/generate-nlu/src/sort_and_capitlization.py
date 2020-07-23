"""Generate some nlu training data"""

from pathlib import Path
import random

NLU_FILE = "nlu-hi-bye-yes-no-thanks.md"
INTENT_NAME = "intent_no"
intent_sentences = []
########################################
# get current sentences for the intent #
########################################
with open(f"{Path(__file__).parents[3]}/data/nlu/{NLU_FILE}", "r") as f:
    while True:
        line = f.readline().rstrip("\n")
        if line == f"## intent:{INTENT_NAME}":
            while True:
                sentence = f.readline().rstrip("\n")
                if not sentence or sentence[0] != "-":
                    break
                intent_sentences.append(sentence)
            break

#############################################
# Sort, and for each both lower & upper:    #
# - for whole sentence                      #
# - for first character of first word       #
# but do not duplicate                      #
#############################################
def capitalize_nth(s, n):
    """capitalize the nth character in a string"""
    return s[:n].lower() + s[n:].capitalize()


basis_sentences = sorted(list({sentence.lower() for sentence in intent_sentences}))
sentences = []
for sentence in basis_sentences:
    sentences.extend(
        [sentence.lower(), capitalize_nth(sentence, 2), sentence.upper(),],
    )
    if len(sentence) > 3:
        sentences.append(
            capitalize_nth(sentence, random.choice(list(range(3, len(sentence)))))
        )

...


with open(f"{Path(__file__).parents[3]}/data/nlu/{NLU_FILE}", "r") as f:
    lines = f.read().splitlines()
    for i, line in enumerate(lines):
        if line == f"## intent:{INTENT_NAME}":
            for sentence in sentences:
                lines.insert(i + 1, sentence)
            break

with open(f"{Path(__file__).parents[3]}/data/nlu/{NLU_FILE}-new.md", "w") as f:
    f.write("\n".join(lines))

...
