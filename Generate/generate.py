# This generates most of the prompts
import argparse, generate_utils, generate_synstat, load_realstatutes, load_transcripts, json, os, sys, datetime
from generate_utils import TYPE_LEAF, TYPE_DEFINITIONS, TYPE_APPLIES_TO, definition_re

# print("argv=", sys.argv)

parser = argparse.ArgumentParser(description='Generate all non-SARA prompts')
parser.add_argument('--texttype', required=True, choices=['uscode', 'synthetic', 'transcript'],
                    help='What type of text to prompt for')
parser.add_argument('--task', required=True, choices=['text2cite', 'cite2text',
                                                      'defined2cite', 'cite2defined',
                                                      'appliesto', 'cite2amendedtext'],
                    help='What task to run')
parser.add_argument('--output', required=True, type=str,
                    help='takes format "name1(num1);name2(num2)" where nameN is both the id field\'s base and ' +
                         'filename, and numN is the number of items to write to it. ' +
                         'Handles as many as necessary')
parser.add_argument('--widthdepth', type=str,
                    help='Used only with synthetic; ' +
                         'semicolon delimited list of width,depth that are acceptable; ' +
                         'for example 3,3;3,4;4,3')
parser.add_argument('--mintokens', type=int, default=0,
                    help='Used only with uscode; min number of gpt3.5 tokens')
parser.add_argument('--maxtokens', type=int, required=True,
                    help='Max number of gpt3.5 tokens; ' +
                         'recommend 25% less since other LLMs may have less efficient tokenization')
parser.add_argument('--numlines', type=int, default=25,
                    help='Used only with transcript; number of lines to use')
parser.add_argument('--numpages', type=str, default="",
                    help='Used only with transcript; comma delimited list of page lengths to use like "1,5,9"')
parser.add_argument('--seed', type=int, default=42,
                    help='Used to change generation and selection of possibilities')
parser.add_argument('--allow_data_dupes', action='store_true',
                    help='Normally we bar identical prompts anywhere in Data/* but we relax if this is passed')
parser.add_argument('--synthetic_nouns', default='nonces', choices=['nonces', 'ids'],
                    help='Whether to use nonces or IDs')

args = parser.parse_args()
print("args=", args)
assert args.task != 'appliesto' or args.texttype == 'synthetic', "appliesto only works on synthetic statutes"

OUTPUT_DIRECTORY = "../Data/"

# Parse the string with the output we are supposed to have
num_prompts = 0
splits = [] # will be list of tuples of (fullname, idname, num)
for s in args.output.split(";"):
    s = s.strip()
    assert s.endswith(")"), "expected format like \"name(num)\"" # --output should look like "testfoo(100);trainfoo(200);devfoo(50)"
    assert len(s.split("(")) == 2, "expected format like \"name(num)\"" # --output should look like "testfoo(100);trainfoo(200);devfoo(50)"
    fullname = s.split("(")[0]
    idname = fullname.split(os.path.sep)[-1]
    num = int(s[:-1].split("(")[1])
    splits.append((fullname, idname, num))
    num_prompts += num

if not args.allow_data_dupes:
    dict_existing_prompts = dict() # keys are the text prompts (may be long!), keys are the filenames
    print("Checking for duplicates everywhere in", OUTPUT_DIRECTORY)
    set_files_with_dupes = set()
    num_existing_duplicates = 0
    for dirpath, dirs, files in os.walk(OUTPUT_DIRECTORY):
        if "OtherExamples" not in dirpath:
            for filename in files:
                if filename.endswith(".jsonl"):
                    jsonl_existing = open(os.path.join(dirpath, filename), "r")
                    for line in jsonl_existing.readlines():
                        line_dict = json.loads(line)
                        if line_dict["prompt"] in dict_existing_prompts:
                            set_files_with_dupes.add(os.path.join(dirpath, filename))
                            set_files_with_dupes.add(os.path.join(dirpath, dict_existing_prompts[line_dict["prompt"]]))
                            num_existing_duplicates += 1
                        dict_existing_prompts[line_dict["prompt"]] = filename
    print("Number of already-existing prompts", len(dict_existing_prompts))
    if num_existing_duplicates > 0:
        print("WARNING: Found", num_existing_duplicates, "existing duplicates prompts, in files", set_files_with_dupes)

QUESTION_TOKEN_BUFFER = 100 # tokens reserved for the question

# Here, we load or generate the appropriate text
print("Now generating...")
if args.texttype == 'synthetic':
    assert args.widthdepth is not None, "--widthdepth is required with synthetic"
    filter_type = TYPE_LEAF
    if args.task in ['defined2cite', 'cite2defined']:
        filter_type = TYPE_DEFINITIONS
    elif args.task == 'appliesto':
        filter_type = TYPE_APPLIES_TO
    raw_text = generate_synstat.generate_items(args.seed,
                                               args.widthdepth,
                                               num_prompts,
                                               filter_type,
                                               args.synthetic_nouns)
elif args.texttype == 'uscode':
    only_unique_text = (args.task in ['text2cite', 'defined2cite'])
    add_dummy_amendment = (args.task == 'cite2amendedtext')
    filter_type = TYPE_LEAF
    if args.task in ['defined2cite', 'cite2defined']:
        filter_type = TYPE_DEFINITIONS
    raw_text = load_realstatutes.load_items(args.seed,
                                            num_prompts,
                                            filter_type,
                                            args.mintokens,
                                            args.maxtokens - QUESTION_TOKEN_BUFFER,
                                            only_unique_text,
                                            add_dummy_amendment)
elif args.texttype == 'transcript':
    assert args.task in ['text2cite', 'cite2text'], "transcripts have no definitions; only text<->cite allowed"
    assert args.numlines < 100, "assumption is that no more than 99 lines in page (default is 25)"
    only_unique_text = (args.task == 'text2cite')
    raw_text = load_transcripts.load_items(args.seed,
                                           num_prompts,
                                           args.numlines,
                                           only_unique_text,
                                           args.maxtokens - QUESTION_TOKEN_BUFFER,
                                           args.numpages)
else:
    assert False, "not implemented"

EXAMPLE_FORMAT = ' (Use standard legal formatting like section 1001(b)(2)).' # used to specify normal legal format for cite
num_written = 0
idx_raw_text = 0 # indexes into raw_text.

# Below we take the relevant text and create the prompts and other JSON elements,
# writing them all into however many JSONL files there are
for split in splits:
    outfilename = OUTPUT_DIRECTORY + split[0] + ".jsonl"
    print("Writing out", outfilename)
    jsonl_out = open(outfilename, "w")
    for idx_in_current_split in range(split[2]):
        if idx_raw_text == len(raw_text):
            print("WARNING: Could not fill all requested splits due to only", len(raw_text), "available data")
            idx_raw_text += 1
            continue # prevents us from crashing
        if idx_raw_text > len(raw_text):
            continue

        d = raw_text[idx_raw_text]
        idx_raw_text += 1
        line_dict = dict()
        line_dict["id"] = split[1] + "_" + str(idx_in_current_split)
        line_dict["task"] = args.task
        line_dict["texttype"] = args.texttype
        if "idx_line" in d: # we might need to derive some more helpful info
            line_text = d["text_lines"][d["idx_line"]]["line_text"]
            stripped_line_text = generate_utils.strip_line_to_text(line_text)
            terms_defined_in_line = definition_re.findall(stripped_line_text)

        if args.task in ['cite2text', 'cite2amendedtext']:
            line_dict["prompt"] = d["full_text"].rstrip() + \
                                  "\n\nWhat is the exact text of just " + \
                                  d["text_lines"][d["idx_line"]]["cite"] + " above?"
            line_dict["answer"] = line_text
        elif args.task == 'cite2defined':
            assert args.texttype in ['synthetic', 'uscode']
            line_dict["prompt"] = d["full_text"].rstrip() + \
                                  "\n\nWhat is the term defined at " + \
                                  d["text_lines"][d["idx_line"]]["cite"] + " above?"
            assert len(terms_defined_in_line) == 1, "expected exactly one match on this line"
            line_dict["answer"] = terms_defined_in_line[0]
        elif args.task == 'text2cite':
            example_format = ""
            if args.texttype == 'synthetic' or args.texttype == 'uscode':
                question = 'What is the exact citation above of the text "'
                example_format = EXAMPLE_FORMAT
            elif args.texttype == 'transcript':
                if d["num_pages"] == 1:
                    question = 'What is the line number of the line above with the text "'
                else:
                    question = 'What are the page number and line number of the line above with the text "'

            line_dict["prompt"] = d["full_text"].rstrip() + \
                                  "\n\n" + question + stripped_line_text + '"?' + \
                                  example_format
            line_dict["answer"] = d["text_lines"][d["idx_line"]]["cite"]
            line_dict["target_text"] = stripped_line_text # store the target text for reference in the calling API
        elif args.task == 'defined2cite':
            assert args.texttype in ['synthetic', 'uscode']
            assert len(terms_defined_in_line) == 1, "expected exactly one match on this line"
            term_defined = terms_defined_in_line[0]
            line_dict["prompt"] = d["full_text"].rstrip() + \
                                  "\n\nWhat is the exact citation above where the term \"" + \
                                  term_defined + "\" is defined?" + EXAMPLE_FORMAT
            line_dict["answer"] = d["text_lines"][d["idx_line"]]["cite"]
            line_dict["target_text"] = term_defined
            # There is potentially another correct answer, which is the parent of "answer" if certain
            # conditions are met, with the previous line containing a header stating it has the definition.
            if d["idx_line"] > 0:
                prev_idx = d["idx_line"]-1
                # check if idx_line is under previous line in hierarchy
                if (d["text_lines"][prev_idx]["cite"] + "(") in d["text_lines"][d["idx_line"]]["cite"]:
                    prev_line_stripped = \
                        generate_utils.strip_line_to_text(d["text_lines"][prev_idx]["line_text"])\
                            .strip().strip(".").strip().lower()
                    prev_line_header = None
                    if "header" in d["text_lines"][prev_idx]:
                        prev_line_header = \
                            generate_utils.strip_line_to_text(d["text_lines"][prev_idx]["header"]) \
                                .strip().strip(".").strip().lower()

                    # Any of the following indicate the previous line is also a valid answer
                    if term_defined.lower() == prev_line_stripped or \
                        "definition of " + term_defined == prev_line_stripped or \
                        term_defined + " defined" == prev_line_stripped or \
                            term_defined.lower() == prev_line_header or \
                            "definition of " + term_defined == prev_line_header or \
                            term_defined + " defined" == prev_line_header:
                        line_dict["alternative_answer"] = d["text_lines"][prev_idx]["cite"]
        elif args.task == 'appliesto': # for this, most work already done during generation
            assert args.texttype == 'synthetic'
            line_dict["prompt"] = d["full_text"].rstrip() + "\n\n" + d["question"]
            if d["answer"] == True:
                line_dict["answer"] = "Yes"
            else:
                line_dict["answer"] = "No"
        else:
            assert False, "not implemented"

        if "idx_line" in d:
            line_dict["idx_line"] = d["idx_line"]
        if args.texttype == 'synthetic':
            line_dict["width"] = d["width"]
            line_dict["depth"] = d["depth"]
        elif args.texttype == 'transcript':
            line_dict["num_pages"] = d["num_pages"]
            line_dict["lines_per_page"] = d["lines_per_page"]

        line_dict["text_lines"] = d["text_lines"] # copy over the line-by-line of the text
        if (not args.allow_data_dupes) and line_dict["prompt"] in dict_existing_prompts:
            print("WARNING:", line_dict["id"],
                  "is a duplicate prompt to one already in", dict_existing_prompts[line_dict["prompt"]])
            print("   Consider changing the --seed to something different.")

        if "sections" in d: # if present, copy over
            assert args.texttype == 'uscode'
            assert "section_correct" in d, "Should appear in same circumstances as sections"
            line_dict["sections"] = d["sections"]
            line_dict["section_correct"] = d["section_correct"]

        if "unamended_answer" in d: # if present, copy over
            assert args.texttype == 'uscode' and args.task == 'cite2amendedtext'
            line_dict["unamended_answer"] = d["unamended_answer"]
        else:
            assert args.task != 'cite2amendedtext'

        # Move the answer to the end, so that the answer is further from the prompt. This will help this
        # from being involved in model collapse.
        if "alternative_answer" in line_dict:
            popped_alt_answer = line_dict.pop("alternative_answer")
            line_dict["alternative_answer"] = popped_alt_answer
        popped_answer = line_dict.pop("answer")
        line_dict["answer"] = popped_answer

        if generate_utils.get_num_tokens(line_dict["prompt"]) > args.maxtokens:
            print("WARNING: prompt for", line_dict["id"], "ended up too long, length=",
                  generate_utils.get_num_tokens(line_dict["prompt"]),
                  "whereas max tokens=", args.maxtokens,". So, not writing out.")
            if args.texttype == 'synthetic':
                print("width=", d["width"], "depth=", d["depth"])
        else:
            jsonl_out.write(json.dumps(line_dict) + "\n") # do the actual writing out
            num_written += 1
    jsonl_out.close()

print("num_prompts=", num_prompts, " num_written=", num_written)
print("++++++++++++++++++++++++++++++++++++++++++++++++", datetime.datetime.now())

