# This handles tests that call for the LLM to return text
import argparse, json, call_utils, re, datetime, os
from collections import Counter

parser = argparse.ArgumentParser(description='Tests ability of LLMs to retrieve particular text')
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

# Helper function. Returns empty string if cannot find.
def find_substring(s:str, start:str, end:str):
    start_loc = s.find(start)
    if start == "'" and start_loc > 0 and s[start_loc-1].isalpha():
        return "" # don't confuse apostrophes for quote starts

    end_loc = s.rfind(end)

    if 0 <= start_loc < end_loc:
        return s[start_loc+1:end_loc].strip()
    return ""

# Extracting a line of text returned by an LLM can be tricky.  Here are some problematic ones:
#  - Response: The text at section 4133(d)(2) is as follows: "The Department...
# Problematic Response: The exact text of section 9300(b)(2)(B)(ii)(II)(bb) is: "The term "cushown" means- (aa) any mativent, or (bb) any comption."
#         We don't want to return just "The term"
# If we cannot do it via simple rules, then return None.
def extract_text(response_raw:str) -> str:
    doublestraight = find_substring(response_raw, '"', '"')
    singlestraight = find_substring(response_raw, "'", "'")
    doublecurly = find_substring(response_raw, '“', '”')
    singlecurly = find_substring(response_raw, "‘", "’")

    maxlen = max(len(doublestraight), len(singlestraight), len(doublecurly), len(singlecurly))

    if maxlen == 0:
        pass
    elif maxlen == len(doublestraight):
        return doublestraight
    elif maxlen == len(singlestraight):
        return singlestraight
    elif maxlen == len(doublecurly):
        return doublecurly
    elif maxlen == len(singlecurly):
        return singlecurly

    # another possibility is that the answer follows a colon
    if response_raw.find(":") >= 0:
        return response_raw[response_raw.find(":")+1:].strip()

    return None # the default, as nothing was returned


def text_to_tokens(text:str) -> list:
    return re.findall(r'\w+', text)

def tokens_to_stripped_text(tokens:list) -> str:
    if len(tokens) == 0:
        return ""
    FINAL_TOKENS_TO_IGNORE = ["or", "and", "but", "yet", "however", "nor"]
    if tokens[-1] in FINAL_TOKENS_TO_IGNORE:
        return " ".join(tokens[:-1])
    else:
        return " ".join(tokens)


# This attempts in multiple ways to check whether the actual answer has been returned.
def is_match(response:str, answer:str, answer_stripped:str, header:str) -> bool:
    assert answer == answer.lower() and \
        answer_stripped == answer_stripped.lower() and \
        response == response.lower() and \
        (header is None or header == header.lower()), "All should already be in lowercase"

    original_response = response

    answer = answer.strip().rstrip(".")
    answer_stripped = call_utils.strip_line_to_text(answer).strip().rstrip(".")
    response = response.strip().rstrip(".").strip('"') \
        .strip("'").rstrip("”").rstrip("’").lstrip("“").lstrip("‘").rstrip(".")
    if response == answer or response == answer_stripped: # most basic cases
        return True

    answer_minus_header = answer_stripped
    if header is not None:
        header_stripped = header.strip()
        if answer.startswith(header_stripped):
            answer_minus_header = answer[len(header_stripped):].strip()
            if response == answer_minus_header:
                return True

    # This handles the situation where the quoted text is there with wonky quote marks
    response_normalizepunct = re.sub("[\"‘“”’]", "'", original_response)
    answer_normalizepunct = re.sub("[\"‘“”’]", "'", answer)
    answer_stripped_normalizepunct = re.sub("[\"‘“”’]", "'", answer_stripped)
    answer_minus_header_normalizepunct = re.sub("[\"‘“”’]", "'", answer_minus_header)
    if "'" + answer_normalizepunct + "'" in response_normalizepunct or \
       "'" + answer_stripped_normalizepunct + "'" in response_normalizepunct or \
       "'" + answer_minus_header_normalizepunct + "'" in response_normalizepunct:
        return True

    # Now try these same variations but with all non-alphanumeric characters ignored
    answer_tokens = text_to_tokens(answer)
    answer_stripped_tokens = text_to_tokens(answer_stripped)
    answer_minus_header_tokens = text_to_tokens(answer_minus_header)
    response_tokens = text_to_tokens(response)

    for tokens in [answer_tokens, answer_stripped_tokens, answer_minus_header_tokens]:
        if tokens_to_stripped_text(tokens) == tokens_to_stripped_text(response_tokens):
            return True
    return False

TERM_STRIP = "., " # these are characters we want to strip from defined terms

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
    assert d["task"] in ['cite2text','cite2defined','cite2amendedtext'], "only tasks supported by this file"

    if args.id is not None and args.id != d["id"]:
        continue
    count_called += 1

    prompt = d["prompt"]
    if args.verbose:
        print(prompt)

    answer = call_utils.standardize_text(d["answer"].lower())
    if args.verbose:
        print("GROUNDTRUTH=", answer)
        if "unamended_answer" in d:
            print("unamended_answer=", d["unamended_answer"])

    # Make the actual LLM call
    LLM = call_utils.LLMChat(args.model)

    response_raw = LLM.chat(prompt)
    if args.verbose:
        print("response_raw=", response_raw)
    response_raw = call_utils.standardize_text(response_raw.lower())
    best_response = response_raw  # used for error analysis if answer is incorrect

    correct = False
    if d["task"] in ['cite2text', 'cite2amendedtext']: # we expect the text of a line back
        answer_stripped = call_utils.strip_line_to_text(answer).lower()
        header = d["text_lines"][d["idx_line"]].get("header", None)
        if header is not None:
            header = header.lower()
        if args.verbose:
            print("header=", header)

        if is_match(response_raw, answer, answer_stripped, header):
            correct = True
        else:
            response_lines = response_raw.strip().split("\n")
            if 1 == len(response_lines): # for single lines, best bet is looking for quote marks
                extracted_response = extract_text(response_raw)
                if args.verbose:
                    print("extracted_response=", extracted_response)
                if extracted_response is None:
                    best_response = response_raw
                else:
                    best_response = extracted_response
            else: # handling multiple lines
                # Consider whether the second line with non-space text is the answer
                if (response_lines[1].isspace() or len(response_lines[1]) == 0) and \
                        is_match(response_lines[2], answer, answer_stripped, header):
                    correct = True
                elif not response_lines[1].isspace() and \
                        is_match(response_lines[1], answer, answer_stripped, header):
                    correct = True
                else:
                    if len(response_lines) > 3 and \
                        (response_lines[1].isspace() or len(response_lines[1]) == 0) and \
                            (response_lines[3].isspace() or len(response_lines[3]) == 0):
                        # If there is a line separated by linespaces after intro and before something else,
                        # that is the best response
                        best_response = response_lines[2]
                    else:
                        # Otherwise go with everything other than the first line
                        best_response = " ".join(response_lines[1:])
            if is_match(best_response, answer, answer_stripped, header):
                correct = True
    elif d["task"] == 'cite2defined': # Here is how we handle when we are looking for a term being defined
        if response_raw.startswith(answer):
            correct = True
        elif response_raw.split("\n")[0].strip("\"'“”‘’.,!;:-").strip().endswith(answer):
            correct = True
        elif re.search("[\"‘“']" + answer + "[.,; ]?[\"'”’]", response_raw):
            correct = True
        else:
            response_raw = response_raw.strip(TERM_STRIP)

            if response_raw == answer:
                correct = True
            else:
                best_response = response_raw
                extracted_response = extract_text(response_raw)
                if args.verbose:
                    print("extracted_response=", extracted_response)
                if extracted_response is not None:
                    extracted_response = extracted_response.strip(TERM_STRIP)
                    best_response = extracted_response
                    if extracted_response == answer:
                        correct = True
                elif response_raw.strip(".,;'!").strip().endswith(answer):
                    correct = True # The assumption is that if we end with the term, that is the direct object



    # if correct != correct2:
    #     print("GradingProblem: correct=", correct, "correct2=", correct2)

    position = float(d["idx_line"])/len(d["text_lines"]) # used for making positional histograms

    if correct:
        if args.verbose:
            print("Correct")
        positions_correct.append(position)
        count_correct += 1
    else:
        if args.verbose:
            print("WRONG!")
            print("best_response=", best_response)

        # We need to do error analysis
        assert best_response == best_response.lower(), "Should already be lowercase"
        positions_wrong.append(position) # record the position of the error

        # prep work for the error analysis
        errors = None
        idx_line_errors = None # has index of most plausible line
        if d["texttype"] != "transcript": # here we get the part of a statute cite for analysis
            if "section_correct" in d:
                assert "sections" in d, "should be present whenever section_correct is"
                answer_sectionnum = d["section_correct"]
            else:
                assert d["text_lines"][0]["cite"].lower().startswith("section ")
                answer_sectionnum = d["text_lines"][0]["cite"][len("section "):]
            assert d["text_lines"][d["idx_line"]]["cite"].lower().startswith("section " + answer_sectionnum.lower())
            answer_subdiv = d["text_lines"][d["idx_line"]]["cite"][len("section " + answer_sectionnum):]

        # ERROR ANALYSIS CODE:
        if d["task"] in ['cite2text', 'cite2amendedtext']: # analyzing errors for text lines is trickier, and we do it here
            if "unamended_answer" in d:
                assert d["task"] == 'cite2amendedtext'
                unamended_answer = d["unamended_answer"].lower()
                unamended_answer_stripped = call_utils.strip_line_to_text(unamended_answer).lower()
                if is_match(response_raw, unamended_answer, unamended_answer_stripped, header) or \
                   is_match(best_response, unamended_answer, unamended_answer_stripped, header) or \
                   unamended_answer in best_response:
                    errors = [call_utils.OMITTED_DUMMY_AMENDMENT]

            if errors is None:
                answer_tokens = tokens_to_stripped_text(text_to_tokens(answer))
                answer_stripped_tokens = tokens_to_stripped_text(text_to_tokens(answer_stripped))
                best_response_tokens = tokens_to_stripped_text(text_to_tokens(best_response))

                if  answer_tokens     in      best_response_tokens or \
                    answer_stripped_tokens in best_response_tokens:
                    errors = [call_utils.SUPERSET]
                elif best_response_tokens in    answer_tokens or \
                     best_response_tokens in    answer_stripped_tokens:
                    errors = [call_utils.SUBSET]
                else:
                    # In this case we need to run thru all the lines looking for matches
                    # (including across multiple lines)
                    whole_text = ""
                    whole_text_stripped = ""
                    for idx_line, line in enumerate(d["text_lines"]):
                        line_text = line["line_text"].lower()
                        whole_text += line_text + " "
                        line_text_stripped = call_utils.strip_line_to_text(line_text)
                        whole_text_stripped += line_text_stripped + " "
                        header = line.get("header", None)
                        if header is not None:
                            header = header.lower()

                        if is_match(best_response,
                                    line_text,
                                    line_text_stripped,
                                    header):

                            if d["texttype"] == "transcript":
                                errors = [call_utils.WRONG_LINE]
                                # if there are multiple lines that are matches for what's returned, the most
                                # plausible is the one that is closest
                                if idx_line_errors is None or \
                                        abs(idx_line_errors-d["idx_line"]) > abs(idx_line-d["idx_line"]):
                                    idx_line_errors = idx_line
                            else: # then we are handling statutes
                                if not line["cite"].lower().startswith("section " + answer_sectionnum):
                                    current_errors = [call_utils.WRONG_SECTION]
                                else:
                                    assert line["cite"].lower().startswith("section " + answer_sectionnum)
                                    current_errors = call_utils.analyze_error(answer_subdiv,
                                                                              line["cite"][len("section " + answer_sectionnum):])

                                if errors is None or \
                                    call_utils.seconderrors_more_plausible(errors, current_errors):
                                    errors = current_errors
                                    idx_line_errors = idx_line
                        elif best_response in line_text or \
                             best_response in line_text_stripped or \
                            best_response_tokens in " ".join(text_to_tokens(line_text)) or \
                            best_response_tokens in " ".join(text_to_tokens(line_text_stripped)):

                            # if a whole wrong line was returned, that's more plausible as the error the LLM made
                            # than just a subset of a wrong line
                            if errors != [call_utils.WRONG_LINE]:
                                errors = [call_utils.WRONG_LINE_SUBSET]
                                idx_line_errors = idx_line # used to measure how far off

                    if errors is None: # then we did NOT find a line with the errors
                        if best_response in whole_text or \
                                best_response in whole_text_stripped or \
                                best_response_tokens in " ".join(text_to_tokens(whole_text)) or \
                                best_response_tokens in " ".join(text_to_tokens(whole_text_stripped)):
                            errors = [call_utils.WRONG_LINE_MULTIPLE]
                        else:
                            errors = [call_utils.NOT_FOUND] # If we are here, we simply did not find a match
        elif d["task"] == 'cite2defined':  # Here is how we handle when we are looking for a term being defined
            idx_line_errors = None
            for idx_line, line in enumerate(d["text_lines"]):
                if d["idx_line"] !=  idx_line: # don't use the current correct line
                    found_in_line = False
                    for terms in line.get("defined_terms",[]):
                        if terms.lower() == best_response:
                            found_in_line = True
                    if found_in_line: # figure out the exact nature of the error
                        if not line["cite"].lower().startswith("section " + answer_sectionnum):
                            current_errors = [call_utils.WRONG_SECTION]
                        else:
                            assert line["cite"].lower().startswith("section " + answer_sectionnum)
                            current_errors = \
                                call_utils.analyze_error(answer_subdiv,
                                                         line["cite"][len("section " + answer_sectionnum):])

                        if errors is None or \
                                call_utils.seconderrors_more_plausible(errors, current_errors):
                            errors = current_errors
                            idx_line_errors = idx_line
                    elif errors is None and best_response in line["line_text"].lower():
                        errors = [call_utils.CHILD_OF_WRONG]
                        idx_line_errors = idx_line
            if errors is None:
                if best_response in d["text_lines"][d["idx_line"]]["line_text"].lower():
                    # then it returned a term that is part of the definition of the sought term
                    errors = [call_utils.CHILD_OF_CORRECT]
                else:
                    errors = [call_utils.NOT_FOUND] # we did not find the line containing the wrong term
        else:
            assert False, "not implemented"

        # if we have a relative error, record that in the histogram
        if idx_line_errors is not None:
            line_relative_error = idx_line_errors - d["idx_line"]
            assert line_relative_error != 0, "Wrong answer equal to right answer?"
            if args.verbose:
                print("Incorrect answer returned was from", d["text_lines"][idx_line_errors]["cite"])
                print("Adding a line_relative_error of", line_relative_error)
                d_copy["line_relative_error"] = line_relative_error
            errors_line_relative.update([line_relative_error])  # add to histogram

        # finally, record the type of error for the histogram
        errors_text = ",".join(errors)
        if args.verbose:
            print("errors_text=", errors_text)
        errors_qualitative.update([errors_text])
        if args.verbose:
            d_copy["errors_qualitative"] = errors_text

    if args.verbose:
        d_copy["correct"] = correct
        print(name_detailed_array + ".append(" + str(d_copy) + ")")

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
    errors_line_relative_list.sort(key=lambda x: x[0]) # sort by numbered relative line errors, NOT count
    for x in errors_line_relative_list:
        print("diff:{:3d}".format(x[0]), "   count:", x[1])

print("\nFINAL Accuracy={:.3f}".format(count_correct/float(count_called)),
      "(", count_correct, "/", count_called, ")",
      d["texttype"],d["task"])
print("above was for args=", args)
print(datetime.datetime.now())
