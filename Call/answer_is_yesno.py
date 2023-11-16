# This handles tests (basically, "applies to") that answer Yes or No
import argparse, json, call_utils, re, datetime, os
from collections import Counter

parser = argparse.ArgumentParser(description='Tests ability of LLMs to answer yes/no questions')
parser.add_argument('--infile', required=True,
                    help='Where JSONL file is with the prompts and answers')
parser.add_argument('--model', default="gpt-3.5-turbo",
                    help='what model to call')
parser.add_argument('--id', type=str, default=None,
                    help='If we only want to run for one ID in the JSONL file, pass this')
parser.add_argument('--maxnumrun', type=int, default=1000000000000,
                    help='maximum number of prompts to call (still done in order)')
parser.add_argument('--verbose', action='store_true',
                    help='provides lots of output')
args = parser.parse_args()
print("======================================================")
print("args=", args)
print(datetime.datetime.now())

name_detailed_array = "bltRESULTS_" + args.infile.split(os.path.sep)[-1][:-len(".jsonl")]
if args.verbose:
    # with grep, it will be possible to extract results into this python code.
    # pandas might be better, but pandas is brittle to changes in the fields put
    # into the JSONL file coming in.
    print(name_detailed_array + "=[] # use grep on \"bltRESULTS_\" to get these lists for data analysis")

# Even when given the second prompt "Therefore, the answer (Yes or No) is", GPT3 sometimes
# gives answers with lots of random punctuation other than just "Yes" or "No".
# Annoyingly this sometimes includes a whole long sentence after the "Yes" or "No"
def is_match(response:str, query:str) -> bool:
    clean = response.replace(".","").replace(":","").replace("-","").replace(":","").strip().lower()
    if clean.startswith(query):
        return True
    if clean.endswith(query):
        return True
    return False

def is_yes(response:str) -> bool:
    return is_match(response, "yes")
def is_no(response:str) -> bool:
    return is_match(response, "no")

histogram_results = Counter()

assert args.infile.endswith(".jsonl"), "expected infile to be a .jsonl file"
jsonl_in = open(args.infile, "r")
count_correct = 0
count_called = 0
length_first_response = [] # collects number of words in first response; good analytics
count_first = 0 # since we ask "Let's think step-by-step", this counts how many have the word "first"
count_first_thennextsecond = 0 # counts how often we have "first" then either "then" or
                               # "next" or "second", signs of continuing thinking step by step

for idx_s, s in enumerate(jsonl_in.readlines()):
    if count_called >= args.maxnumrun:
        print("Cutting off due to --maxnumrun", args.maxnumrun)
        break

    d = json.loads(s)
    if args.verbose:
        d_copy = d.copy()  # will be used for printing
        d_copy.pop("prompt")  # not needed for printing, as too long
        d_copy["len(text_lines)"] = len(d_copy.pop("text_lines"))  # not needed for printing, as too long
        if count_called == 0:
            print("TASK", d["task"], " TEXTTYPE", d["texttype"])
        print("***********************")
        print("id=", d["id"])
    else:
        print(".", end="", flush=True)
    assert d["task"] == 'appliesto', "only task supported by this file"

    if args.id is not None and args.id != d["id"]:
        continue
    count_called += 1

    prompt = d["prompt"]
    if args.verbose:
        print(prompt)

    answer = d["answer"]
    if args.verbose:
        print("GROUNDTRUTH=", answer)
    assert answer in ["Yes", "No"]

    # Make the first LLM call (we will always make a second)
    LLM = call_utils.LLMChat(args.model)

    first_response = LLM.chat(prompt)
    if args.verbose:
        print("first_response=", first_response)
        d_copy["first_response"] = first_response
        words_first_response = len(first_response.split())
        print("length of first_response.split =", words_first_response)
        length_first_response.append(words_first_response)
        idx_first = first_response.lower().find("first")
        if idx_first >= 0:
            count_first += 1
            idx_then = first_response.lower().find("then", idx_first)
            idx_next = first_response.lower().find("next", idx_first)
            idx_second = first_response.lower().find("second", idx_first)
            if idx_then > 0 or idx_next > 0 or idx_second > 0:
                count_first_thennextsecond += 1

    second_response = LLM.chat("Therefore, the answer (Yes or No) is")
    if args.verbose:
        print("second_response=", second_response)
        d_copy["second_response"] = second_response

    result = "unclear"
    if is_yes(second_response):
        if answer == "Yes":
            count_correct += 1
            result = "True Positive"
        else:
            result = "False Positive"
    elif is_no(second_response):
        if answer == "No":
            result = "True Negative"
            count_correct += 1
        else:
            result = "False Negative"
    if args.verbose:
        print("result=", result)
    if "True" not in result and args.verbose:
        print("WRONG!")

    histogram_results.update([result])
    if args.verbose:
        d_copy["result"] = result

    if args.verbose:
        print(name_detailed_array + ".append(" + str(d_copy) + ")")

if args.verbose:
    print("average length_first_response = ", float(sum(length_first_response))/len(length_first_response))
    print("count_first=", count_first)
    print("count_first_thennextsecond=", count_first_thennextsecond)

    print("****************************")
    for result, count in histogram_results.items():
        print("{:6d}".format(count), result)






print("\nFINAL Accuracy={:.3f}".format(count_correct/float(count_called)),
      "(", count_correct, "/", count_called, ")",
      d["texttype"],d["task"])
print("above was for args=", args)
print(datetime.datetime.now())
