# Utilities used by all generation
import re, Levenshtein, tiktoken

def strip_line_to_text(intext:str) -> str:
    rv = intext.strip()
    if rv.startswith("("):
        return rv[rv.find(")")+1:].lstrip()
    if rv.startswith("["):
        return rv[rv.find("]")+1:].lstrip()
    if re.match("[1-9][0-9]?:", rv):
        return rv[rv.find(":")+1:].lstrip()
    return rv

def text_too_similar(candidate_text:str, other_text:str) -> bool:
    other_text = other_text.strip().lower()
    candidate_text = candidate_text.strip().lower()

    if candidate_text in other_text:
        return True # subset is definitely too close

    LEVENSHTEIN_CUTOFF = 5  # avoids near matches
    lev_dist = Levenshtein.distance(other_text, candidate_text,
                                    score_cutoff=LEVENSHTEIN_CUTOFF)
    if lev_dist < LEVENSHTEIN_CUTOFF:
        return True # within this cutoff is also too close
    return False


TYPE_LEAF = "leaf"
TYPE_DEFINITIONS = "definition"
TYPE_APPLIES_TO = "applies-to"

MIN_NUM_WORDS = 4

definition_re = re.compile('[Tt]he\s+term\s+["“]([^"”]+)["”]\s+means')

# We use the tokenizer of gpt-3.5 to measure length.
# For safety margin, since other LLMs use different tokenizers, we
# generally assume other tokenizers might be as much as 20% less efficient at worst.
baseline_encoder = tiktoken.encoding_for_model("gpt-3.5-turbo")
def get_num_tokens(instr:str) -> int:
    return len(baseline_encoder.encode(instr))