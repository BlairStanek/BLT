# This program generates fine-tuning datasets for OpenAI chat.  Unlike most other BLT programs,
# it does NOT run from the command line, since specifying how and what to use in
# fine tuning is fairly involved.
import json, random

random.seed(956)

source_jsonl_files = [
            "../Data/BLT4k/train4k_syn_t2c.jsonl",
            "../Data/BLT4k/train4k_usc_c2def.jsonl",
            "../Data/BLT4k/train4k_syn_c2def.jsonl",
            "../Data/BLT4k/train4k_trans_c2t.jsonl",
            "../Data/BLT4k/train4k_usc_c2t.jsonl",
            "../Data/BLT4k/train4k_syn_c2t.jsonl",
            "../Data/BLT4k/train4k_trans_t2c.jsonl",
            "../Data/BLT4k/train4k_usc_def2c.jsonl",
            "../Data/BLT4k/train4k_syn_def2c.jsonl",
            "../Data/BLT4k/train4k_usc_c2amt.jsonl",
            "../Data/BLT4k/train4k_usc_t2c.jsonl"
        ]

# source_jsonl_files = [
# "/Users/andrew/Desktop/RESEARCH/BLT/CODE/Data/OtherExamples/appliesto_50_blt4k.jsonl"
# ]

NUM_FROM_EACH_TO_USE = 30 # the remaining are left potentially as a dev set

output_jsonl = "../FineTuningData/blt4k_train_first30.jsonl"

finetuning_lines = []

for source_file in source_jsonl_files:
    jsonl_in =  open(source_file, 'r')
    for idx_s, s in enumerate(jsonl_in.readlines()):
        if idx_s >= NUM_FROM_EACH_TO_USE:
            continue
        d = json.loads(s)
        messages = []
        # Example output from openAI website
        # {"messages": [{"role": "system", "content": "Marv is a factual chatbot that is also sarcastic."},
        #               {"role": "user", "content": "What's the capital of France?"},
        #               {"role": "assistant", "content": "Paris, as if everyone doesn't know that already."}]}
        messages.append({"role": "user", "content": d["prompt"]}) # prompt is easy; how to phrase answer is harder

        assistant_content = d["answer"]
        # if d["task"] == "cite2text" and d["texttype"] == "transcript":
        #     # gpt-3.5-turbo's modal answer is the answer with the line number
        #     assistant_content = d["answer"]
        # else:
        #     assert False, "Not implemented; find modal current answer format and add"
        messages.append({"role": "assistant", "content": assistant_content})

        finetuning_lines.append(json.dumps({"messages": messages}))

random.shuffle(finetuning_lines)

jsonl_out = open(output_jsonl, "w")
for line in finetuning_lines:
    jsonl_out.write(line + "\n")
jsonl_out.close()
