"""Generate some nlu training data"""

from pathlib import Path
import random

################################################
# get current sentences for intent_inform_pest #
################################################
with open(f"{Path(__file__).parents[3]}/data/nlu/nlu-inform-pest.md", "r") as f:
    nlu_inform_pest = []
    while True:
        line = f.readline().rstrip('\n')
        if line == "## intent:intent_inform_pest":
            while True:
                sentence = f.readline().rstrip('\n')
                if not sentence or sentence[0] != "-":
                    break
                nlu_inform_pest.append(sentence)
            break

############################################
# Append some more, but do not duplicate   #
############################################
with open(f"{Path(__file__).parents[3]}/data/nlu/lookups/pest_name.txt", "r") as f:
    pest_names = f.read().splitlines()

pest_names = random.choices(pest_names, k=10)

with open(f"{Path(__file__).parents[3]}/data/nlu/nlu-inform-pest.md", "r") as f:
    lines = f.read().splitlines()
    for i, line in enumerate(lines):
        if line == "## intent:intent_inform_pest":
            for pest_name in pest_names:
                sentence = f"- [{pest_name}](pest_name)"
                if sentence not in nlu_inform_pest:
                    lines.insert(i + 1, sentence)
            break

with open(f"{Path(__file__).parents[3]}/data/nlu/nlu-inform-pest-new.md", "w") as f:
    f.write('\n'.join(lines))
