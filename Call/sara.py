# This handles the SARA tests
import argparse, json, call_utils, re, datetime
from collections import Counter

parser = argparse.ArgumentParser(description='Tests ability of LLMs to do the SARA tests')
parser.add_argument('--infile', required=True,
                    help='Where JSONL file is with the prompts and answers')
parser.add_argument('--model', default="gpt-3.5-turbo",
                    help='what model to call')
parser.add_argument('--id', type=str, default=None,
                    help='If we only want to run for one ID in the JSONL file, pass this')
parser.add_argument('--verbose', action='store_true',
                    help='provides lots of output')
parser.add_argument('--skipfirst', type=int, default=-1,
                    help='skips the first portion of the calls')
args = parser.parse_args()
print("args=", args)
print(datetime.datetime.now())

# This is the system prompt, used by OpenAI at minute 19:30 of the GPT-4
# launch livestream, available at https://www.youtube.com/watch?v=outcGtbnMuQ
SYSTEM_TEXT = "You are TaxGPT, a large language model trained by OpenAI.\n\n" + \
            "Carefully read & apply the tax code, being certain to spell out your " + \
            "calculations & reasoning so anyone can verify them. Spell out everything " + \
            "in painstaking detail & don't skip any steps!"

def dollar_string_to_float(txt) -> float:
    txt = txt.strip()
    txt = txt.lstrip("$")
    txt = txt.rstrip(".")
    txt = txt.replace(",", "")
    txt = txt.strip()
    return float(txt)

assert args.infile.endswith(".jsonl"), "expected infile to be a .jsonl file"
jsonl_in = open(args.infile, "r")

count_entailcontradict_correct = 0
count_entailcontradict_called = 0
histogram_entailcontradict = Counter()

calculate_percent_errors = []
count_calculate_correct = 0
count_calculate_called = 0

count_dollar_called = 0

for idx_s, s in enumerate(jsonl_in.readlines()):
    d = json.loads(s)
    if idx_s < args.skipfirst:
        print("Skipped", d["id"])
        continue

    if args.verbose:
        print("***********************")
        print("id=", d["id"])
    else:
        print(".", end="", flush=True)
    assert d["texttype"] == "sara"
    assert d["task"] in ["entail_contradict", "calculate"], "only tasks supported by this file"
    if args.id is not None and args.id != d["id"]:
        continue

    prompt = d["prompt"]
    if args.verbose:
        if len(prompt.split("\n")) < 10:
            print(prompt)
        else:
            print("\n".join(prompt.split("\n")[:6]))
            print(" ...")
            print("\n".join(prompt.split("\n")[-6:]))
        print("d[answer]=", d["answer"])

    LLM = call_utils.LLMChat(args.model, system_prompt=SYSTEM_TEXT)

    first_response_raw = LLM.chat(prompt)
    if args.verbose:
        print("first_response_raw=", first_response_raw)

    if d["task"] == "entail_contradict":
        assert d["answer"] in ["Entailment", "Contradiction"]
        second_response_raw = LLM.chat("Therefore, the answer (Entailment or Contradiction) is:")
    elif d["task"] == "calculate":
        second_response_raw = LLM.chat("Therefore, the answer (dollar figure) is:")
    if args.verbose:
        print("second_response_raw=", second_response_raw)

    if d["task"] == "entail_contradict":
        count_entailcontradict_called += 1
        result = "unclear"
        if "entail" in second_response_raw.lower():
            if d["answer"] == "Entailment":
                count_entailcontradict_correct += 1
                result = "True Positive"
            else:
                result = "False Positive"
        elif "contradict" in second_response_raw.lower():
            if d["answer"] == "Contradiction":
                result = "True Negative"
                count_entailcontradict_correct += 1
            else:
                result = "False Negative"
        if args.verbose:
            print("result=", result)
            if "True" not in result:
                print("WRONG!")
        histogram_entailcontradict.update([result])
    elif d["task"] == "calculate":
        count_calculate_called += 1
        dollar_figure = re.search("\$?(\d|,)*\d(\.\d\d)?\.?\s*$",  second_response_raw)
        dollar_amount = None
        if dollar_figure is not None:
            dollar_amount = dollar_string_to_float(dollar_figure[0])
        else:
            if args.verbose:
                print("Got no good dollar figure:", second_response_raw)

        groundtruth = dollar_string_to_float(d["answer"])
        if args.verbose:
            print("groundtruth=", groundtruth, " dollar_amount=", dollar_amount)
        if dollar_amount is not None and abs(dollar_amount-groundtruth) <= 1:
            count_calculate_correct += 1
        elif dollar_amount is None:
            calculate_percent_errors.append(1.0)
        else:
            error_amount = abs(dollar_amount-groundtruth)/(0.00001+groundtruth)
            error_amount = min(1, error_amount) # cap error at 100%
            if args.verbose:
                print("error_amount=",error_amount)
            calculate_percent_errors.append(error_amount) # cap error at 100%
    else:
        assert False, "not implemented"

if args.verbose:
    print("Histogram entail/contradict items:")
    for result, count in histogram_entailcontradict.items():
        print("{:6d}".format(count), result)

print("\nFINAL Numerical-Case Accuracy={:.3f}".format(count_calculate_correct/(0.00001 +float(count_calculate_called))), " (", count_calculate_correct, "/", count_calculate_called, ")")
print("FINAL average calculate_percent_errors= {:.3f}".format(sum(calculate_percent_errors)/(0.00001+len(calculate_percent_errors))))
print("FINAL Entail/Contradict-Case Accuracy={:.3f}".format(count_entailcontradict_correct/(0.00001 +float(count_entailcontradict_called))), " (", count_entailcontradict_correct, "/", count_entailcontradict_called, ")")
print(datetime.datetime.now())
