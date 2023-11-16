import os, re, random, generate_utils, copy
from generate_utils import TYPE_LEAF, TYPE_DEFINITIONS, definition_re, get_num_tokens
import xml.etree.ElementTree as ET
# import spacy
# nlp = spacy.load("en_core_web_sm")

usc_ns_str = "http://xml.house.gov/schemas/uslm/1.0"
usc_ns_str_curly = "{" + usc_ns_str + "}"
ns = {"usc" : usc_ns_str}

FLUSH_LANGUAGE = "flush"

subdivision_types = [usc_ns_str_curly + "subsection",
                usc_ns_str_curly + "paragraph",
                usc_ns_str_curly + "subparagraph",
                usc_ns_str_curly + "clause",
                usc_ns_str_curly + "subclause",
                usc_ns_str_curly + "item",
                usc_ns_str_curly + "subitem",
                usc_ns_str_curly + "subsubitem"]

class Section:
    def __init__(self,  fullid:str):
        self.statlines = []
        self.fullid = fullid
        raw_sectnum = convert_identifier_to_prettycite(fullid)
        assert raw_sectnum.lower().startswith("section ")
        self.sectnum = raw_sectnum[len("section "):].strip() # remove the "section " from the start
        self.numtokens = None
        self.fulltext = None

    def clear(self):
        self.numtokens = None
        self.fulltext = None

    def postprocess(self):
        for sl in self.statlines:
            assert type(sl) == dict
            assert "cite" in sl and "line_text" in sl
            # There are a variety of whitespace characters other than spaces in the XML US Code,
            # and we want to replace them all with standard spaces, except that we want to retain
            # the initial whitespaces that give the indenting.
            num_start_spaces = len(sl["line_text"]) - len(sl["line_text"].lstrip())
            sl["line_text"] = sl["line_text"][:num_start_spaces] + \
                              re.sub("\s+", " ", sl["line_text"][num_start_spaces:]).rstrip()
        self.get_num_tokens() # gets text and token counts

    def get_num_tokens(self):
        if self.numtokens == None:
            self.numtokens = get_num_tokens(self.full_text())
        return self.numtokens

    # This function is used in deciding how to weight the size of the statute in selection
    def get_weight(self):
        return self.get_num_tokens() ** 2

    def full_text(self) -> str:
        if self.fulltext is not None:
            return self.fulltext
        else:
            rv = ""
            for l in self.statlines:
                assert not l["line_text"][-1].isspace()
                if "\n" in l["line_text"]:
                    assert "repealed" in l["line_text"].split("\n")[1].lower() or \
                        "reserved" in l["line_text"].split("\n")[1].lower(), \
                        "only repealed or reserved sections should have newlines"
                rv += l["line_text"] + "\n"
            self.fulltext = rv
            return rv

class Leaf:
    def __init__(self, section, linenum, level):
        assert type(section) == Section
        self.section = section
        assert linenum < len(section.statlines)
        self.linenum = linenum
        self.level = level
        self.percentile = None # This will be used to analyze how far the leaf is into the statute


# This converts XML-style identifiers like /us/usc/t22/s4133/d/2 to 4133(d)(2)
def convert_identifier_to_prettycite(identifier:str) -> str:
    START = "/us/usc/t"
    assert identifier.startswith(START)
    idx_start_non_title_info = identifier.find("/s", len(START))
    assert idx_start_non_title_info > 0

    non_title_info = identifier[idx_start_non_title_info+len("/s"):]
    cite_components = non_title_info.split("/")
    rv = "section " + cite_components[0]
    for component in cite_components[1:]:
        rv += "(" + component + ")"
    return rv


# This builds up the text in the WESTLAW format (i.e. more compact, and using idents
# that make the most sense).
# The text is built up within the list of statlines
# Then it returns true if x is a leaf (a bool).
# Then it returns a list of all Leaf (a list) under x, IF x was not itself a leaf.
def parse_xml_statute(x:ET.Element, section:Section, assert_no_subdivisions = False, level = 1):
    x_is_leaf = False
    leaves = [] # this will be used to return a set of leaves UNDER x that can be used

    # We ignore repealed, historical, notes, etc. and focus on just the statute as it is
    if "status" in x.attrib:
        assert x.attrib["status"] in ['repealed', 'transferred']
        return x_is_leaf, leaves
    if "sourceCredit" in x.tag or "notes" in x.tag:
        return x_is_leaf, leaves

    if x.tag in subdivision_types:
        # if x.tag == (usc_ns_str_curly + "subsubitem"):
        #     print("Found subsubitem!")
        assert not assert_no_subdivisions, "an assumption about no subdivisions under chapeaus, continuations, etc. failed"
        section.statlines.append({"cite": convert_identifier_to_prettycite(x.attrib.get("identifier", "")),
                                  "line_text": "  " * max(0, level-2),
                                  "level": level})
        x_is_leaf = True # default is True, but negated immediately below if contains subdivision
        for subdiv_type in subdivision_types:
            if x.tag != subdiv_type and len(list(x.iter(subdiv_type))) > 0:
                x_is_leaf = False # contains a subdivision, so cannot be leaf

    if len(section.statlines) == 0:
        section.statlines.append({"cite": convert_identifier_to_prettycite(x.attrib.get("identifier", "")),
                                  "line_text": "",
                                  "level": level})

    # this is the main mechanism for building up the text
    if x.text is not None:
        section.statlines[-1]["line_text"] += x.text

    for sub in x:
        if sub.tag == (usc_ns_str_curly + "heading"):
            sub_isleaf, _ = parse_xml_statute(sub, section, True)
            assert not sub_isleaf
            if len(section.statlines[-1]["line_text"]) > 0 and \
                    section.statlines[-1]["line_text"].strip()[-1] in ".-——–:": # some headers already end in punctuation; don't add more
                if not section.statlines[-1]["line_text"][-1].isspace():
                    section.statlines[-1]["line_text"] += " " # ensure at least one space
            else:
                section.statlines[-1]["line_text"] += ". " # like with Westlaw, have a heading ended with a period, not a newline
            # We need to store the text of the header since an LLM might return the text without that
            section.statlines[-1]["header"] = section.statlines[-1]["line_text"]
        elif sub.tag == (usc_ns_str_curly + "chapeau"):
            if len(section.statlines) == 1: # if chapeau starts the section, start a new line
                section.statlines.append({"cite": section.statlines[0]["cite"],
                                          "line_text": "",
                                          "level": level})
            sub_isleaf, _ = parse_xml_statute(sub, section, True)
            assert not sub_isleaf
        elif sub.tag == (usc_ns_str_curly + "continuation"): # aka "flush language", since flush to header
            section.statlines.append({"cite": FLUSH_LANGUAGE,
                                      "line_text": "  " * max(0, level - 2),
                                      "level": level}) # like with Westlaw have flush language flush
            sub_isleaf, _ = parse_xml_statute(sub, section, True, 0)
            assert not sub_isleaf
            # This is crucial: we cannot test for a leaf followed immediately by flush language,
            # since that is an ill-defined question.  (Should the answer include the flush text or not?)
            if len(leaves) > 0:
                leaves.pop() # removes last leaf
        elif (sub.tag == usc_ns_str_curly + "ref" and (sub.attrib.get("class","").startswith("footnote") or
                                                      sub.attrib.get("class","").startswith("endnote"))) or \
             (sub.tag == usc_ns_str_curly + "note" and (sub.attrib.get("type","") == "footnote" or
                                                          sub.attrib.get("type", "") == "endnote")):
            # for ref's and note's, do not include text and children; at most, include the tail
            assert not sub.attrib.get("type","") == "inline", "not expected"
            if sub.tail is not None:
                section.statlines[-1]["line_text"] += sub.tail.replace("\n", "") + " "  # we handle line-keeping via statlines, not newlines
        else:
            sub_isleaf, sub_leaves = \
                parse_xml_statute(sub, section, assert_no_subdivisions, level + 1) # recursively build up
            if sub_isleaf:
                assert len(sub_leaves) == 0
                leaves.append(Leaf(section, len(section.statlines)-1, level))
            elif len(sub_leaves) > 0:
                assert not sub_isleaf
                leaves.extend(sub_leaves)

    if x.tail is not None:
        section.statlines[-1]["line_text"] += x.tail.replace("\n","") + " " # we handle line-keeping via statlines, not newlines

    if level == 0 and not assert_no_subdivisions: # here we are at the top level
        for idx_line, line in enumerate(section.statlines):
            assert "\n" not in line.text or len(section.statlines) == 1 or \
                   "repealed" in line.text.lower() or \
                   "omitted" in line.text.lower() or\
                   "reserved" in line.text.lower(), \
                "The only newlines should be when there are no subdivisions or item repealed, etc."
            if "\n" in line.text:
                line.text = line.text.replace("\n"," ").replace("  ", " ")
            if line.text.strip().startswith("“"): # e.g. 5 USCA § 9507(b)(1).  Don't even load these sections.
                section.statlines.clear() # remove everything
                return False, [] # do nothing

    if section.statlines[-1]["line_text"].strip().startswith("["): # unusual circumstance, e.g., 26 USC 56(c)
        assert (x.tag not in subdivision_types) or \
               section.statlines[-1]["line_text"].strip().strip(".").strip().endswith("]") or \
               section.statlines[-1]["cite"] == 'section 1396r–8(e)(4)' # handles odd case
        assert (x.tag not in subdivision_types) or \
               "repealed" in section.statlines[-1]["line_text"].lower() or \
                "transferred" in section.statlines[-1]["line_text"].lower() or \
                "redesignated" in section.statlines[-1]["line_text"].lower() or \
                section.statlines[-1]["cite"] == 'section 1396r–8(e)(4)'  # handles odd case
        x_is_leaf = False # repealed/transferred/redesignated portions disallowed from being tested as leaves or containing leaves
        leaves = []

    if "\n" in section.statlines[-1]["line_text"]:
        assert (x.tag not in subdivision_types) or \
               "repealed" in section.statlines[-1]["line_text"].lower() or \
               "omitted" in section.statlines[-1]["line_text"].lower() or \
               "reserved" in section.statlines[-1]["line_text"].lower() or \
               section.statlines[-1]["cite"] == 'section 1396r–8(e)(4)'  # handles odd case
        x_is_leaf = False # repealed, etc. portions disallowed from being tested as leaves or containing leaves
        leaves = []

    return x_is_leaf, leaves

# returns a 2-tuple:  a list of leaves, and a list of lists of StatLines
def load_statutes(min_depth:int):
    list_leaves = []  # list of Leaf
    list_sections = [] # list of Section
    count_sections_with_tables = 0
    print("Loading Titles ", end="")
    for title in range(1, 55):
    # for title in range(26, 27):  # for debug
        print(title, end=" ", flush=True)
        prefix = ""
        if title < 10:
            prefix = "0"
        USC_XMLFILE_ROOT = "../RawData/xml_uscAll@117-327not263not286"
        filename = USC_XMLFILE_ROOT + "/usc" + prefix + str(title) + ".xml"
        if not os.path.exists(filename):
            continue
        title_tree = ET.parse(filename)
        title_root = title_tree.getroot()
        for s in title_root.iter('{' + usc_ns_str + '}section'):  # this loop builds up the list of possibilities
            num = s.find('{' + usc_ns_str + '}num')
            if num is not None and \
                    num.text is not None and \
                    len(s.attrib.get("status", "")) == 0 and \
                    s.attrib.get("identifier", "").startswith("/us/usc/t"):
                tables = s.iter("{http://www.w3.org/1999/xhtml}table") # HTML-style tables within US Code XML
                layouttables = s.iter(usc_ns_str+"layout") # XML-style tables wtihin US Code XML, called <layout>
                # skip ALL sections with tables; they make queries ill-defined
                if len(list(tables)) > 0 or len(list(layouttables)) > 0:
                    count_sections_with_tables += 1 # we don't use these sections, but keep count of those excluded
                else:
                    # The two lines below are useful for debugging:
                    # if not (title == 7 and s.attrib["identifier"].endswith("s1516")):
                    #     continue
                    section = Section(s.attrib.get("identifier", ""))
                    _, leaves_raw = parse_xml_statute(s, section)
                    # We skip sections not following standard identifier numbering
                    if len(section.statlines) <= 1 or \
                        section.statlines[1]["cite"].startswith(section.statlines[0]["cite"]):
                        list_sections.append(section) # save the statute
                        if len(leaves_raw) > 1: # ignore leaves from sections with just one valid leaf
                            # first filter by min-depth
                            filtered_leaves = []
                            for leaf in leaves_raw:
                                assert leaf.section == section
                                if leaf.level >= min_depth:
                                    filtered_leaves.append(leaf)
                            # ignore leaves from sections with zero or one leaf sufficiently deep
                            if len(filtered_leaves) > 1:
                                # calculate leaf percentiles
                                for idx_leaf, leaf in enumerate(filtered_leaves):
                                    leaf.percentile = float(idx_leaf) / (len(filtered_leaves) - 1)
                                list_leaves.extend(filtered_leaves) # actually add to the list we return

    print("\nstart postprocessing")

    for section in list_sections:
        section.postprocess()

    # print("len(list_leaves)=", len(list_leaves))
    # print("len(list_sections)=", len(list_sections))
    print("count_sections_with_tables=", count_sections_with_tables)
    return list_leaves, list_sections

def is_conflict(filter_type, candidate:str, target_section:Section, target_line_exclude:int) -> bool:
    for other_linenum in range(len(target_section.statlines)):
        if target_line_exclude is not None and target_line_exclude != other_linenum:
            if filter_type == TYPE_LEAF:
                other_text = \
                    generate_utils.strip_line_to_text(target_section.statlines[other_linenum]["line_text"])
                if generate_utils.text_too_similar(candidate, other_text):
                    return True
                    # An example of such a conflict is 15 USC § 80a-27 where the line
                    # 'the sales load on such certificate exceeds 9 per centum of the total payments to be made thereon;'
                    # appears twice in different places
            elif filter_type == TYPE_DEFINITIONS:
                # here, candidate means the defined term
                other_line_terms = target_section.statlines[other_linenum].get("defined_terms", [])
                for other_terms in other_line_terms:
                    if other_terms.strip().lower() == candidate.strip().lower():
                        return True
                        # An example of such a conflict is 16 USC § 1362 where "Secretary" is
                        # defined in two different ways depending on the usage.
    return False

def replace_last_instance(linetext, replace_this, with_this):
    return with_this.join(linetext.rsplit(replace_this, 1))

# This function makes the dummy amendment to implement cite2amended
def do_dummy_amendment(linetext:str, header:str):
    # DUMMY_AMENDMENT = "except as provided in section 101, "
    linetext_stripped = generate_utils.strip_line_to_text(linetext)

    # Our best bet is to replace a number
    if re.search("\d+", linetext_stripped):
        matches = re.findall("\d+", linetext_stripped)
        matches_not1 = [m for m in matches if m != "1"]
        if len(matches_not1) > 0: # going from 1 to 2 changes from singular to plural, creating grammar errors
            replace_this = matches_not1[-1]
            if replace_this.endswith("9"):
                with_this = str(int(replace_this)-1)
            else:
                with_this = str(int(replace_this)+1)
            return replace_last_instance(linetext, replace_this, with_this), "number"
    if re.search("\([a-z]\)", linetext_stripped):
        matches = re.findall("\([a-z]\)", linetext_stripped)
        replace_this = matches[-1]
        if replace_this == "(a)":
            with_this = "(b)"
        else:
            with_this = "(a)"
        return replace_last_instance(linetext, replace_this, with_this), "(lowercase)"
    if re.search("\([A-Z]\)", linetext_stripped):
        matches = re.findall("\([A-Z]\)", linetext_stripped)
        replace_this = matches[-1]
        if replace_this == "(A)":
            with_this = "(B)"
        else:
            with_this = "(A)"
        return replace_last_instance(linetext, replace_this, with_this), "(UPPERCASE)"
    if " or " in linetext_stripped:
        return replace_last_instance(linetext, " or ", " and "), "or->and"
    if " and " in linetext_stripped:
        return replace_last_instance(linetext, " and ", " or "), "and->or"
    if " may " in linetext_stripped:
        return replace_last_instance(linetext, " may ", " shall "), "may->shall"
    if " shall " in linetext_stripped:
        return replace_last_instance(linetext, " shall ", " may "), "shall->may"

    # If all else fails, insert a long string at the beginning
    amendment = "unless otherwise provided by section 101, "
    if len(header) > 0:
        header_idx = linetext.find(header)
        insert_idx = header_idx + len(header)
    else:
        insert_idx = linetext.find(linetext_stripped)
    if linetext[insert_idx:insert_idx+1].isupper(): # match case
        amendment = amendment[0:1].upper() + amendment[1:]
    return linetext[:insert_idx] + \
           amendment + \
           linetext[insert_idx:insert_idx+1].lower() + \
           linetext[insert_idx+1:],  "huge amendment" # bookmark

# max_tokens is measured in gpt-3.5-turbo tokens, since the filtering by size must work
# for all possible LLMs.  The tokens measures are the statute plus the text that will be asked
# about.  One should give a large buffer (e.g. 20% off, minus 200 tokens for the answer) to account
# for other LLMs having sometimes-less-efficient tokenization than gpt-3.5. So, for 4000 total tokens,
# one might pass 3000 as max_tokens to account for different tokenization.
def load_items(rand_seed:int,
                   num:int,
                   filter_type:str,
                   min_tokens:int,
                   max_tokens:int,
                   only_unique_text:bool,
                   add_dummy_amendment:bool) -> list:
    assert filter_type == TYPE_LEAF or filter_type == TYPE_DEFINITIONS
    rand_gen = random.Random(rand_seed)

    rv = []
    set_fulltexts_used = set() # used to count unique statutes actually returned
    amendment_type = ""

    raw_list_leaves, raw_list_sections = load_statutes(0)
    list_sections = [S for S in raw_list_sections if min_tokens <= S.get_num_tokens() <= max_tokens]

    # Create a histogram of token sizes
    histogram_section_numtokens = dict()
    for s in raw_list_sections:
        toknum_range = "{:6d}-{:6d}".format(1000 * int(s.get_num_tokens() / 1000),
                                     1000 * int(s.get_num_tokens() / 1000) + 999)
        histogram_section_numtokens[toknum_range] = 1 + histogram_section_numtokens.get(toknum_range, 0)
    histogram_section_numtokens_list = list(histogram_section_numtokens.items())
    histogram_section_numtokens_list.sort(key=lambda x:x[0])
    # for k, v in histogram_section_numtokens_list:
    #     print(k, "{:10d}".format(v))



    if filter_type == TYPE_LEAF:  # used for tasks like text2cite and cite2text
        num_shall = 0
        num_may = 0

        list_leaves = []
        set_leaf_cites = set() # used to avoid duplicates
        for L in raw_list_leaves:
            leaf_cite = L.section.statlines[L.linenum]["cite"]
            unique_id = L.section.fullid + "+" + leaf_cite
            # if unique_id in set_leaf_cites:
            #     print("Found duplicate leaves:", unique_id)
            if min_tokens <= (L.section.get_num_tokens()) <= max_tokens and \
                   leaf_cite != FLUSH_LANGUAGE and \
                   unique_id not in set_leaf_cites:
                list_leaves.append(L)
                set_leaf_cites.add(unique_id)

                if " may " in L.section.statlines[L.linenum]["line_text"]:
                    num_may += 1
                if " shall " in L.section.statlines[L.linenum]["line_text"]:
                    num_shall += 1
        list_leaves_weights = [L.section.get_weight() for L in list_leaves]

        # print("num_may=", num_may, "({:5.3f} percent of all)".format(float(num_may)/len(list_leaves)))
        # print("num_shall=", num_shall, "({:5.3f} percent of all)".format(float(num_shall)/len(list_leaves)))

    elif filter_type == TYPE_DEFINITIONS:  # used for tasks like defined2cite and cite2defined
        assert not add_dummy_amendment, "no adding amendments to definitions, only to leaves"

        # iterate over all statutes looking for defined lines
        defined_lines = []
        set_cites = set() # used to avoid duplicates
        for section in list_sections:
            for idx_line, line in enumerate(section.statlines):
                if line["cite"] != FLUSH_LANGUAGE and \
                        line["level"] > 1:  # cannot use definitions in flush language or at top level
                    matches = definition_re.findall(line["line_text"])
                    line["defined_terms"] = matches  # record these for the future
                    if matches is not None and len(matches) == 1:
                        unique_id = section.fullid + "+" + line["cite"]
                        # if unique_id in set_cites:
                        #     print("Found dupliate defined line:", unique_id)
                        if unique_id not in set_cites:
                            defined_lines.append({"section": section,
                                                  "idx_line": idx_line,
                                                  "defined_term": matches[0]})
                            set_cites.add(unique_id)
        print("After paring down with criteria, len(defined_lines)=", len(defined_lines))
        defined_lines_weights = [L["section"].get_weight() for L in defined_lines]

    while len(rv) < num:

        # pick a potential leaf or defined-line randomly
        if filter_type == TYPE_LEAF:
            if len(list_leaves) == 0:
                print("WARNING: Not enough data to generate", num, "uscode.  Generated only", len(rv))
                break

            leaf_idx = rand_gen.choices(range(len(list_leaves_weights)), weights=list_leaves_weights)[0]
            leaf = list_leaves.pop(leaf_idx) # pop() both retrieves and removes
            list_leaves_weights.pop(leaf_idx) # pop() both retrieves and removes
            cur_section = copy.deepcopy(leaf.section) # deepcopy allows us to edit
        elif filter_type == TYPE_DEFINITIONS:
            if len(defined_lines) == 0:
                print("WARNING: Not enough data to generate", num, "uscode.  Generated only", len(rv))
                break

            defined_line_idx = rand_gen.choices(range(len(defined_lines)), weights=defined_lines_weights)[0]
            defined_line = defined_lines.pop(defined_line_idx)
            defined_lines_weights.pop(defined_line_idx)
            cur_section = copy.deepcopy(defined_line["section"])

        list_sections_this_run = [cur_section]
        tokens_so_far = cur_section.get_num_tokens()
        assert not (add_dummy_amendment and only_unique_text), "unique text needed for a cite2amendedtext"

        if filter_type == TYPE_LEAF:
            linetext = cur_section.statlines[leaf.linenum]["line_text"]
            linetext_stripped = generate_utils.strip_line_to_text(linetext)
            cur_text = linetext_stripped
            tokens_so_far += get_num_tokens(linetext_stripped) # it will be part of the prompt

            if len(linetext_stripped.split()) < generate_utils.MIN_NUM_WORDS: # don't use super-short leaves
                continue

            # We always see whether the token count with a dummy amendment would exclude this
            # section due to slight increases in tokens.  (Or whether having the amendment would
            # bring us under the tokens.)  This ensures cite2text and cite2amended have the exact
            # same prompts, except for the amendment.
            amended_linetext, amendment_type = do_dummy_amendment(linetext,
                                                         cur_section.statlines[leaf.linenum].get("header",""))
            amended_cur_text = generate_utils.strip_line_to_text(amended_linetext)
            token_change_from_amendment = get_num_tokens(amended_linetext) - get_num_tokens(linetext)
            tokens_so_far += 3 * max(0, token_change_from_amendment) # may increase tokens in text, in question, and in answer

            # Do actual amendment now -- bookmark
            if add_dummy_amendment:
                unamended_answer = linetext # store for finding the error of an LLM using it
                cur_section.statlines[leaf.linenum]["line_text"] = amended_linetext
                cur_section.clear()  # clear the cached information so the change above propagates
                cur_section.postprocess() # re-postprocess it

            cur_linenum = leaf.linenum
        elif filter_type == TYPE_DEFINITIONS:
            assert not add_dummy_amendment, "no amendments relate to definition tasks"
            cur_text = defined_line["defined_term"]
            amended_cur_text = cur_text # same
            cur_linenum = defined_line["idx_line"]
            tokens_so_far += get_num_tokens(cur_text)  # definition will be part of the prompt, so its tokens count

        # if unique text is needed on the line, make sure it is indeed unique
        if only_unique_text:
            if is_conflict(filter_type, cur_text,         cur_section, cur_linenum) or \
               is_conflict(filter_type, amended_cur_text, cur_section, cur_linenum):
                continue

        # sometimes the line text or defined term or the dummy amendment will put us over max tokens
        # and so we cannot use this section/line combination
        if tokens_so_far > max_tokens :
            continue

        # We have a good section; now we add other sections to bulk up towards the maximum number of tokens
        while (max_tokens - tokens_so_far) > min_tokens:
            list_candidate_sections = \
                [S for S in list_sections if S.get_num_tokens() < (max_tokens - tokens_so_far - 5)] # leave 5 extra tokens

            if len(list_candidate_sections) == 0:
                break

            list_candidate_sections_weight = [S.get_weight() for S in list_candidate_sections]
            idx_candidate = rand_gen.choices(range(len(list_candidate_sections)), list_candidate_sections_weight)[0]
            candidate_section = list_candidate_sections[idx_candidate]

            if ((not only_unique_text) or
                (not is_conflict(filter_type, cur_text, candidate_section, -1))) and \
                    (candidate_section.sectnum.lower() not in cur_section.sectnum.lower()) and \
                    (cur_section.sectnum.lower() not in candidate_section.sectnum.lower()):
                list_sections_this_run.append(candidate_section)
                tokens_so_far += candidate_section.get_num_tokens()

        # Now actually put together the prompt information that we will return
        # print("---------")
        rand_gen.shuffle(list_sections_this_run)
        section_nums_this_run = []
        full_text = ""
        text_lines = []
        idx_line_final = None
        for s in list_sections_this_run:
            if len(full_text) > 0:
                full_text += "\n"

            if s == cur_section:
                idx_line_final = len(text_lines) + cur_linenum
                # print("Adding TARGET", s.fullid,"with #tokens=",s.get_num_tokens(), "with text:", cur_text)
            # else:
                # print("Adding distractor", s.fullid,"with #tokens=",s.get_num_tokens())

            full_text += s.full_text()
            set_fulltexts_used.add(s.fullid)
            text_lines.extend(s.statlines)
            section_nums_this_run.append(s.fullid)

        rv.append({"full_text": full_text,
                   "text_lines": text_lines,
                   "sections": section_nums_this_run,
                   "idx_line": idx_line_final,
                   "section_correct": cur_section.sectnum})
        if add_dummy_amendment:
            rv[-1]["unamended_answer"] = unamended_answer
            rv[-1]["amendment_type"] = amendment_type

        assert min_tokens <= get_num_tokens(full_text) <= max_tokens

    print("len(set_fulltexts_used)=", len(set_fulltexts_used))
    print("len(rv)=", len(rv))

    # The list in rv has been built up via a process that prefers larger statutes first,
    # meaning it will be -- on average -- weighted towards larger ones.  Thus, we need
    # to do one more shuffle to ensure even distribution on average.
    rand_gen.shuffle(rv)

    return rv

if __name__ == "__main__":
    stats = load_items(223, 400, TYPE_LEAF,  1000 , 3000, False, True)
    # exit(1)
    for d in stats:
        print("SECTIONS = ", d["sections"])
        print("section_correct = ", d["section_correct"])
        print(d["full_text"])
        print("-----")
        for idx, line in enumerate(d["text_lines"]):
            if idx == d["idx_line"]:
                print("*", end="")
            else:
                print(" ", end="")
            print("{:30s}|".format(line["cite"])+line["line_text"])

        print("++++++++++")

    for d in stats:
    #     print("Old: ", d["unamended_answer"])
        line = d["text_lines"][d["idx_line"]]
        print("{:30s}|".format(line["cite"]) + line["line_text"])
        if "amendment_type" in d:
            print(d["amendment_type"])
        # if "unamended_answer" in d:
        #     print(" " * 30 + "|" + d["unamended_answer"])
        # stripped_line = generate_utils.strip_line_to_text(line)
        # parse = nlp(stripped_line)
        # for token in parse:
        #     print(token.text + "[" + token.pos_ + "," + token.tag_ + "]", end=" ")
        # print("\n")