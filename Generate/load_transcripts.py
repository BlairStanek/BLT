# Used to load the transcript files and re-divide them into chunks of desired size
# with a single line chosen
import os, random, re, generate_utils

def remove_linenumber(linetext:str) -> str:
    assert not linetext.startswith("Page ")
    if linetext[1] == ":":
        assert linetext[0].isnumeric()
        return linetext[2:].strip()
    elif linetext[2] == ":":
        assert linetext[0].isnumeric() and linetext[1].isnumeric()
        return linetext[3:].strip()
    else:
        assert False, "expected colon"


def load_items(rand_seed:int,
               num:int,
               lines_per_page:int,
               only_unique_text:bool,
               max_tokens:int,
               numpages:str) -> list:

    assert len(numpages) > 0, "expected --numpages list of page lengths"
    assert re.fullmatch("[0-9,]+", numpages) is not None, \
        "expected --numpages to be comma-delimited list of page lengths (no spaces)"
    list_numpages = [int(num) for num in numpages.split(",")]

    # First, read in all the available transcripts
    transcripts = []
    total_lines = 0
    DEPOSITION_DIR = os.path.join("..", "RawData", "Transcripts")
    for deposition_file in sorted(os.listdir(DEPOSITION_DIR)):
        if deposition_file.endswith(".txt"):
            fullpath_deposition_file = os.path.join(DEPOSITION_DIR,deposition_file)
            # print("Reading from", fullpath_deposition_file)
            assert os.path.isfile(fullpath_deposition_file)
            max_chars = 0
            f_in = open(fullpath_deposition_file, "r")
            lines = []
            for line in f_in.readlines():
                line_stripped = line.strip()
                if len(line_stripped) > 1:
                    if len(line_stripped) > max_chars:
                        max_chars = len(line_stripped)
                    lines.append(line_stripped)
            # print("max_chars=", max_chars)
            # print("len(lines)=", len(lines))
            print(deposition_file, "has", len(lines),"lines, meaning", int(len(lines)/25), "pages")

            total_lines += len(lines)
            transcripts.append(lines)

    print("total_lines=", total_lines)
    rand_gen = random.Random(rand_seed)

    # We select randomly from all possible starting lines
    candidate_start_lines = [] # list of 2-tuples of (transcript index, line index within transcript)
    for idx_transcript, transcript in enumerate(transcripts):
        for idx_line, line in enumerate(transcript):
            if idx_line <= (len(transcript)-lines_per_page):
                candidate_start_lines.append((idx_transcript, idx_line))
    rand_gen.shuffle(candidate_start_lines)

    # Now run over possibilities, constructing tests
    rv = []
    for transcript_idx, start_idx in candidate_start_lines:
        text_lines = []
        full_text = ""
        candidate_indices = []
        num_pages = list_numpages[len(rv) % len(list_numpages)] # gets a uniform distribution

        if num_pages > 1: # then we have a multi-page multi-page
            if start_idx + num_pages * lines_per_page >= len(transcripts[transcript_idx]):
                continue
            # We never start on page 1, since we are working with chopped-up transcripts.
            # We start with a page number that is definitely higher than the highest line
            # number.  This simplifies parsing the response.
            start_page = rand_gen.randint(lines_per_page+1,lines_per_page+50)
            for page_idx in range(num_pages): # loop over the pages
                page_str = "Page " + str(start_page+page_idx) + ":"
                text_lines.append({"cite": "page " + str(start_page+page_idx),
                                   "line_text": page_str})
                full_text += page_str + "\n"

                for i in range(lines_per_page): # loop over the lines within each page
                    line = transcripts[transcript_idx][start_idx + page_idx * lines_per_page + i]
                    line = str(i+1) + ": " + line
                    text_lines.append({"cite": "line " + str(i+1) + " of page " + str(start_page+page_idx) ,
                                       "line_text": line})
                    candidate_indices.append(len(text_lines)-1) # obviously "Page _:" lines are not candidates
                    full_text += line + "\n" # line break between lines of same page
                full_text += "\n" # add an extra line break between pages
        else:  # then we do just one page
            if start_idx + lines_per_page >= len(transcripts[transcript_idx]):
                continue
            for i in range(lines_per_page): # loop over the lines within the page
                line = transcripts[transcript_idx][start_idx + i]
                line = str(i+1) + ": " + line
                text_lines.append({"cite": "line " + str(i+1),
                                   "line_text": line})
                candidate_indices.append(len(text_lines) - 1)
                full_text += line + "\n"

        if generate_utils.get_num_tokens(full_text) > max_tokens - 50: # assume 50 tokens for answer
            continue # we can't use

        # Now we need to choose the index that will be used
        rand_gen.shuffle(candidate_indices)
        candidate_idx = None
        if not only_unique_text:
            candidate_idx = candidate_indices[0]
            found_valid_line = True # since we don't care about uniqueness, anything will work
        else:
            # If here, we have to choose a line whose text is NOT too similar to any others
            found_valid_line = False
            for candidate_idx in candidate_indices:
                candidate_linetext = remove_linenumber(text_lines[candidate_idx]["line_text"])
                if len(candidate_linetext.split()) >= generate_utils.MIN_NUM_WORDS:
                    conflict = False
                    for other_idx in candidate_indices:
                        if other_idx != candidate_idx:
                            other_text = remove_linenumber(text_lines[other_idx]["line_text"])
                            if generate_utils.text_too_similar(candidate_linetext, other_text):
                                conflict = True
                    if not conflict:
                        found_valid_line = True
                        break
        if found_valid_line:
            rv.append({"full_text": full_text,
                        "text_lines": text_lines,
                        "idx_line": candidate_idx,
                        "num_pages": num_pages,
                        "lines_per_page": lines_per_page})
            if len(rv) == num:
                return rv

    print("WARNING: Not enough data to generate", num, "transcript prompts.  Generated only", len(rv))
    return rv

if __name__ == "__main__":
    returned = load_items(42, 10, 25, True, 102200, "2")

    tokens_per_page = []
    for d in returned:
        print("++++++++++++++++++++++")
        num_tokens = generate_utils.get_num_tokens(d["full_text"])
        print("Number of Tokens=", num_tokens)
        print("num_pages=", d["num_pages"])
        tokens_per_page.append(float(num_tokens)/float(d["num_pages"]))
        print("-----")
        print(d["full_text"])
        print("-----")
        for idx, line in enumerate(d["text_lines"]):
            if idx == d["idx_line"]:
                print("*", end="")
            else:
                print(" ", end="")
            print("{:30s}|".format(line["cite"])+line["line_text"])

    print("average number of tokens per page= {:.0f}".format(sum(tokens_per_page)/ len(tokens_per_page)))