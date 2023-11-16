# This is used to assemble prompts that fit within the 4k window of the largest fine-tuneable model
# to run SARA.
import os, json

records = []
SARA_LOCATION = os.getenv("SARA_LOCATION")  # you can download SARA v1 or v2 from https://nlp.jhu.edu/law/ then decompress
SARA_case_location = os.path.join(SARA_LOCATION, "cases")
print("Loading cases from", SARA_case_location)
for sara_case in os.listdir(SARA_case_location):
    if sara_case.endswith(".pl") and not "tax_case" in sara_case:
        new_record = dict()
        new_record["case id"] = sara_case.split(".")[0]
        with open(os.path.join(SARA_case_location, sara_case), "r") as f:
            caselines = f.readlines()
        assert caselines[0].strip() == "% Text"
        idx = 1
        text = ""
        while caselines[idx].startswith("% ") and not caselines[idx].startswith("% Question"):
            text += caselines[idx][2:]
            idx += 1
        while not caselines[idx].startswith("% Question"):
            idx += 1
        idx += 1  # skip over "% Question"
        text += caselines[idx][2:].strip()
        answer_text = text.split()[-1]
        new_record["answer"] = answer_text
        new_record["test case"] = text[: -1 * len(answer_text)].rstrip()
        records.append(new_record)

print("len(records)=", len(records))
records.sort(key=lambda x: x["case id"])

sections = ["1", "2", "63", "68", "151", "152", "3301", "3306", "7703"]
sections_text = dict()
for s in sections:
    with open(os.path.join(SARA_LOCATION, "statutes","source", "section" + s), "r") as f:
        sections_text[s] = f.read().replace("\n\n", "\n").strip()

outfile = open(os.path.join("..", "Data", "sara_4k_fits.jsonl"), "w")

for rec in records:
    json_dict = dict()
    json_dict["id"] = rec["case id"]
    prompt = "We are going to be doing Entailment/Contradiction reasoning applying the statute(s) below:\n"

    for s in sections:
        if ("section " + s + " ") in rec["test case"].lower() or \
            ("section " + s + "(") in rec["test case"].lower() or \
                ("s" + s) == rec["case id"]:
            prompt += sections_text[s] + "\n"

    answer_divider = rec["test case"].rfind("\n")
    assert answer_divider > 0
    prompt += "Premise: " + rec["test case"][:answer_divider] + "\n"
    prompt += "Hypothesis: "+ rec["test case"][answer_divider+1:] + "\n"
    prompt += "Answer: "
    json_dict["prompt"] = prompt
    json_dict["answer"] = rec["answer"]

    json_dict["texttype"] = "sara"
    json_dict["task"] = "entail_contradict"

    outfile.write(json.dumps(json_dict) + "\n")

outfile.close()