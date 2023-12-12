import json, os, copy, argparse

parser = argparse.ArgumentParser(description='Convert prompts to other forms')
parser.add_argument('--infile', required=True)
parser.add_argument('--outfile', required=False)
parser.add_argument('--variation', required=True, type=int, help="one of the variation numbers used")
args = parser.parse_args()
print("args=", args)

assert args.infile != args.outfile

jsonl_in = open(args.infile, "r")
if args.outfile is None:
    # create new file with name based on variation:
    assert args.infile.endswith(".jsonl")
    outfile = args.infile[: -1 * len(".jsonl")] + "_var" + str(args.variation) + ".jsonl"
    jsonl_out = open(outfile, "w")
else:
    jsonl_out = open(args.outfile, "w")


for s in jsonl_in.readlines():
    d = json.loads(s)

    answer_lines = d["prompt"].split("\n")
    assert len(answer_lines[-2]) == 0, "Expected newline before the question"

    out_answer_lines = None
    if args.variation == 1: # turn end-of-text question into start-of-text question
        subject_lines = copy.deepcopy(answer_lines[:-2])
        assert " above" in answer_lines[-1]
        out_answer_lines = [answer_lines[-1].replace(" above", " below"), ""]
        out_answer_lines.extend(subject_lines)
    elif args.variation == 2: # Tell it to "Return" the relevant data rather than just asking.
        assert d["task"] in ['cite2text', 'cite2defined', 'cite2amendedtext'], "only tasl supported by this file"
        out_answer_lines = copy.deepcopy(answer_lines)
        assert out_answer_lines[-1].startswith("What is the exact")
        out_answer_lines[-1] = out_answer_lines[-1].replace("What is the exact",
                                                            "Return the exact")
    elif args.variation == 3:  # Change "exact" to "precise"
        assert d["task"] in ['cite2text', 'cite2defined', 'cite2amendedtext'], "only tasl supported by this file"
        out_answer_lines = copy.deepcopy(answer_lines)
        assert " exact " in out_answer_lines[-1]
        out_answer_lines[-1] = out_answer_lines[-1].replace(" exact ",
                                                            " precise ")
    elif args.variation == 4:  # add further explanation to the request
        assert d["task"] in ['cite2text', 'cite2defined', 'cite2amendedtext'], "only tasl supported by this file"
        assert d["texttype"] == "transcript", "only transcripts supported by this variation_num"
        out_answer_lines = copy.deepcopy(answer_lines)
        out_answer_lines[-1] = out_answer_lines[-1].rstrip() + \
            " Return just the text on that line and return none of the text "+\
            "on the line before or after, even if necessary for a full sentence."
    elif args.variation == 5: # add suffix explaining that this is a transcript
        assert d["texttype"] == "transcript", "only transcripts supported by this variation_num"
        out_answer_lines = ["Below is a portion of a transcript, with each line starting with a number " +
                            "that is important for referring to that line.", ""]
        out_answer_lines.extend(answer_lines)
    elif args.variation == 6:  # add word "exact" (perhaps twice) (used to be variation 3)
        assert d["texttype"] == "transcript", "only transcripts supported by this variation_num"
        assert d["task"] in ['text2cite', 'defined2cite'], "only tasl supported by this file"
        out_answer_lines = copy.deepcopy(answer_lines)
        if "the page number and line number" in out_answer_lines[-1]:
            out_answer_lines[-1] = out_answer_lines[-1].replace("the page number and line number",
                                                                "the exact page number and the exact line number")
        elif "the line number" in out_answer_lines[-1]:
            out_answer_lines[-1] = out_answer_lines[-1].replace("the line number",
                                                                "the exact line number")
        else:
            assert False, "not supported"
    elif args.variation == 7:  # add word "precise" (perhaps twice) (used to be variation 4)
        assert d["texttype"] == "transcript", "only transcripts supported by this variation_num"
        assert d["task"] in ['text2cite', 'defined2cite'], "only tasl supported by this file"
        out_answer_lines = copy.deepcopy(answer_lines)
        if "the page number and line number" in out_answer_lines[-1]:
            out_answer_lines[-1] = out_answer_lines[-1].replace("the page number and line number",
                                                                "the precise page number and the precise line number")
        elif "the line number" in out_answer_lines[-1]:
            out_answer_lines[-1] = out_answer_lines[-1].replace("the line number",
                                                                "the precise line number")
        else:
            assert False, "not supported"
    else:
        assert False, "not supported"

    d["prompt"] = "\n".join(out_answer_lines)
    jsonl_out.write(json.dumps(d) + "\n")


