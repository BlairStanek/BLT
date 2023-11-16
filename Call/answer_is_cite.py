# This handles tests that call for the LLM to return a citation
import argparse, json, call_utils, re, datetime
import os.path
from collections import Counter

parser = argparse.ArgumentParser(description='Tests ability of LLMs to get cite containing particular text')
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

assert args.infile.endswith(".jsonl")
name_detailed_array = "bltRESULTS_" + args.infile.split(os.path.sep)[-1][:-len(".jsonl")]
if args.verbose:
    # with grep, it will be possible to extract results into this python code.
    # pandas might be better, but pandas is brittle to changes in the fields put
    # into the JSONL file coming in.
    print(name_detailed_array + "=[] # use grep on \"bltRESULTS_\" to get these lists for data analysis")

# These can be used to develop histograms of errors
positions_correct = [] # absolute locations by percentile
positions_wrong = [] # absolute locations by percentile
errors_qualitative = Counter()
errors_line_relative = Counter()

assert args.infile.endswith(".jsonl"), "expected infile to be a .jsonl file"
jsonl_in = open(args.infile, "r")
count_correct = 0
count_called = 0
for idx_s, s in enumerate(jsonl_in.readlines()):
    if count_called >= args.maxnumrun:
        print("Cutting off due to --maxnumrun", args.maxnumrun)
        break

    d = json.loads(s)
    if args.verbose:
        d_copy = d.copy() # will be used for printing
        d_copy.pop("prompt") # not needed for printing, as too long
        d_copy["len(text_lines)"] = len(d_copy.pop("text_lines"))  # not needed for printing, as too long

        if count_called == 0:
            print("TASK", d["task"], " TEXTTYPE", d["texttype"])
        print("***********************")
        print("id=", d["id"])
    else:
        print(".", end="", flush=True)
    assert d["task"] in ['text2cite','defined2cite'], "only tasks supported by this file"
    if args.id is not None and args.id != d["id"]:
        continue
    count_called += 1

    prompt = d["prompt"]
    if args.verbose:
        print(prompt)

    LLM = call_utils.LLMChat(args.model)

    response_raw = LLM.chat(prompt)

    if args.verbose:
        d_copy["response_raw"] = response_raw
        print("CORRECT=", d["answer"])
        if "alternative_answer" in d:
            print("Alternative Correct=", d["alternative_answer"])
        print("response_raw=", response_raw)

    # Sometimes an LLM will regurgitate the text we are looking for in the response; remove it!
    response = response_raw
    target_text = d["target_text"].rstrip(".;:,-‒–—").strip()
    idx_target = response_raw.lower().find(target_text.lower())
    if idx_target >= 0 :
        if args.verbose:
            print("Removed regurgitation of original text")
        response = response[:idx_target] + response[idx_target+len(target_text):]
        if args.verbose:
            print("response=", response)

    correct = False
    relative_error = None
    if d["texttype"] == "transcript":
        cite_text = d["text_lines"][d["idx_line"]]["cite"]
        correct_line = None
        correct_page = None
        if d["num_pages"] == 1:
            assert cite_text.startswith("line ")
            correct_line = int(cite_text[len("line "):].strip())
        else:
            assert cite_text.startswith("line ")
            assert cite_text.find(" of page ") > 0
            answer_numbers = re.findall("\d+", cite_text)
            assert len(answer_numbers) == 2
            correct_line = int(answer_numbers[0])
            correct_page = int(answer_numbers[1])

        response_numbers_all_str = re.findall("\d+",response)
        response_numbers = set([int(x) for x in response_numbers_all_str]) # turning into a set removes duplicates
        response_numbers_firstline_str = re.findall("\d+",response.split("\n")[0])
        response_numbers_firstline = set([int(x) for x in response_numbers_firstline_str])

        if d["num_pages"] == 1:
            if len(response_numbers_firstline) == 1:
                response_numbers = response_numbers_firstline # work from the first line if correct numbers
            if len(response_numbers) != 1:
                if args.verbose:
                    print("Expected 1 number, got", len(response_numbers), ":", response_numbers)
            elif int(list(response_numbers)[0]) != correct_line:
                relative_error = str(list(response_numbers)[0] - correct_line) # transcript relative errors are strings
                if args.verbose:
                    print("relative error=", relative_error)
                # errors_line_relative.update([relative_error]) # record the relative error
            else:
                correct = True
        elif d["num_pages"] > 1:
            if len(response_numbers_firstline) == 2:
                response_numbers = response_numbers_firstline
            if len(response_numbers) != 2:
                if args.verbose:
                    print("Expected 2 numbers, got", len(response_numbers), ":", response_numbers)
            else:
                num1 = list(response_numbers)[0]
                num2 = list(response_numbers)[1]
                # page numbers are always greater than the maximum line number, so we assume that
                # if the second number is within the line number range, that's the line number.
                if num2 <= d["lines_per_page"]:
                    response_line = num2
                    response_page = num1
                else:
                    response_line = num1
                    response_page = num2
                if response_line == correct_line and \
                    response_page == correct_page:
                    correct = True
                else:
                    # transcript relative errors are strings
                    relative_error = str(response_page - correct_page) + ":" + str(response_line - correct_line)
                    if args.verbose:
                        print("relative error=", relative_error)
                    # errors_line_relative.update([relative_error]) # record the relative error
    else: # then dealing with statutes (i.e., not transcripts)
        if "section_correct" in d:
            answer_sectionnum = call_utils.standardize_text(d["section_correct"])
            assert "sections" in d, "should be present whenever section_correct is"
            sections_str = "(" + \
                           "|".join([call_utils.standardize_text(s[s.find("/s")+2:]) for s in d["sections"]]) +\
                           ")"  # Build up regex string of all possible sections
        else:
            assert d["text_lines"][0]["cite"].lower().startswith("section ")
            answer_sectionnum = d["text_lines"][0]["cite"][len("section "):]
            sections_str = answer_sectionnum

        answer = call_utils.standardize_text(d["answer"])
        assert answer.lower().startswith("section " + answer_sectionnum.lower()+"(")
        answer = answer[len("section "):]
        answer_subdivisions = answer[len(answer_sectionnum):]
        alternative_answer = None
        alternative_answer_subdivisions = None
        if "alternative_answer" in d:
            alternative_answer = call_utils.standardize_text(d["alternative_answer"])
            assert alternative_answer.lower().startswith("section " + answer_sectionnum.lower() + "(")
            alternative_answer = alternative_answer[len("section "):]
            alternative_answer_subdivisions = alternative_answer[len(answer_sectionnum):]
        response = call_utils.standardize_text(response)

        # Just looking for string being contained is incorrect, since "section 1001(c)" is not "section 1001(c)(4)".
        # So we look for all strings that match the basic format expected.
        re_matches = list(re.finditer("(^|\s|sec[.]|Sec[.]|§)"+ \
                                      "(?P<num>" + sections_str + "(\(\w+\))+)",
                                      response))
        set_matches = set([x.group('num') for x in re_matches])

        error = None
        if len(set_matches) == 1 and list(set_matches)[0] in [answer, alternative_answer]:
            correct = True
        elif len(set_matches) == 2 and \
            list(set_matches)[0] in [answer, alternative_answer] and \
            list(set_matches)[1] in [answer, alternative_answer]:
            correct = True
        elif len(set_matches) > 1:
            error = [call_utils.MULTIPLE_SOMEWRONG]
        elif len(set_matches) == 0:
            if (" " + answer_subdivisions + " " ) in response or \
                (" " + answer_subdivisions + "." ) in response or \
                  answer_subdivisions == response:
                # Sometimes the LLM, despite having the prompt give an example like
                # (Use standard legal formatting like section 1001(b)(2)) will still
                # return just the (b)(2).  This is wrong, since it would be an incorrect cite
                # in a legal memorandum or brief.
                error = [call_utils.SECTIONNUM_OMITTED]
            elif alternative_answer_subdivisions is not None and \
                    (" " + alternative_answer_subdivisions + " ") in response:
                error = [call_utils.SECTIONNUM_OMITTED]
            else:
                error = [call_utils.NOT_FOUND]
        else: # This is the general error-handling, where there is one wrong answer
            assert len(set_matches) == 1
            # We want 2 types of info: qualitative description of what went wrong; and the line delta
            wrong_answer = list(set_matches)[0]

            if not wrong_answer.startswith(answer_sectionnum):
                error = [call_utils.WRONG_SECTION]
            else:
                error = call_utils.analyze_error(answer_subdivisions,
                                                 wrong_answer[len(answer_sectionnum):]) # gets qualitative description
            line_idx_wrong_answer = None
            for idx in range(len(d["text_lines"])): # get line delta
                if call_utils.standardize_text(d["text_lines"][idx]["cite"]).endswith(wrong_answer):
                    line_idx_wrong_answer = idx
            if line_idx_wrong_answer is not None:
                relative_error = line_idx_wrong_answer-d["idx_line"]
                if args.verbose:
                    print("relative error=", relative_error)
                # errors_line_relative.update([relative_error]) # statute relative errors are ints
        if error is not None:
            error_str = ",".join(error)
            d_copy["errors_qualitative"] = error_str
            errors_qualitative.update([error_str])
            if args.verbose:
                print("error is", error_str)

    position = float(d["idx_line"])/len(d["text_lines"]) # used for making positional histograms

    d_copy["correct"] = correct
    if args.verbose:
        print(name_detailed_array + ".append(" + str(d_copy) + ")")

    if correct:
        if args.verbose:
            print("Correct")
        count_correct += 1
        positions_correct.append(position)
    else:
        if args.verbose:
            print("WRONG!")
        if relative_error is not None:
            errors_line_relative.update([relative_error])
            d_copy["relative_error"] = relative_error
        positions_wrong.append(position)

if args.verbose:
    print("*********")
    print("positions_correct=", positions_correct)
    print("positions_wrong=", positions_wrong)

    print("errors_qualitative: -------------------")
    errors_qualitative_list = list(errors_qualitative.items())
    errors_qualitative_list.sort(key=lambda x: x[1], reverse=True)  # sort by COUNT (i.e. [1]), not errors
    for x in errors_qualitative_list:
        print("{:5d}".format(x[1]), " ", x[0])

    print("errors_line_relative: -------------------")
    errors_line_relative_list = list(errors_line_relative.items())
    errors_line_relative_list.sort(key=lambda x: x[0]) # sort by relative error
    for x in errors_line_relative_list:
        print(x[0], " ", x[1])
print("\nFINAL Accuracy={:.3f}".format(count_correct/float(count_called)),
      " (", count_correct, "/", count_called, ")",
      d["texttype"],d["task"])
print("above was for args=", args)
print(datetime.datetime.now())
