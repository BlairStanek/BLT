# Given a directory, count the GPT-4-style tokens in all the calls and answers
import sys, os, os.path, tiktoken, json

assert len(sys.argv) == 3, "Expected directory then either 'test' or 'train' as argument"
assert os.path.isdir(sys.argv[1]), "Expected directory as argument"

tokenizer = tiktoken.encoding_for_model("gpt-4")

total_prompt_tokens = 0
total_answer_tokens = 0

for filename in sorted(os.listdir(sys.argv[1])):
    thisfile_prompt_tokens = 0
    thisfile_answer_tokens = 0

    if filename.endswith(".jsonl") and sys.argv[2] in filename:
        print("{:25s}".format(filename), end="\t")
        jsonl_in = open(os.path.join(sys.argv[1], filename), "r")
        for line_num, s in enumerate(jsonl_in.readlines()):
            d = json.loads(s)
            thisfile_prompt_tokens += len(tokenizer.encode(d["prompt"]))
            thisfile_answer_tokens += len(tokenizer.encode(d["answer"]))
        # assert line_num == 99 or line_num == 999, "expected values"
        print("{:8d}  {:8d}".format(thisfile_prompt_tokens, thisfile_answer_tokens))

        total_prompt_tokens += thisfile_prompt_tokens
        total_answer_tokens += thisfile_answer_tokens

print("total_prompt_tokens=", total_prompt_tokens)
print("total_answer_tokens=", total_answer_tokens)
print("For GPT-4-Preview = ${:7.2f}".format((total_prompt_tokens * 0.01 / 1000) +(total_answer_tokens * 0.03 / 1000)))
print("For GPT-4 = ${:7.2f}".format((total_prompt_tokens * 0.03 / 1000) +(total_answer_tokens * 0.06 / 1000)))