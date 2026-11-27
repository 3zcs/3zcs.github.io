---
title: Does the engine matter for local LLM speed on a Mac?
description: >-
  The same model in Ollama, mlx-lm and LM Studio on an M5 MacBook: why writing speeds are so close,
  why MLX reads long prompts about 70% faster, and how speculative decoding beats the memory limit.
author: 3zcs
date: 2026-11-27 16:45:00 +0300
categories: [AI]
tags: [llm, local llm, mlx, ollama, lm studio, mac, benchmark]
pin: true
---

In an attempt to use LLMs on my own computer (a Mac) without sharing files on the internet, I tried
a number of engines with a number of models. In this post I share some of the numbers I got, even
though the results haven't reached the level I hoped for yet, in either speed or quality.

I ran the same model in three engines on the same Mac. For writing speed, the engines were close:
the two MLX engines were about 12% faster than Ollama, and most of that gap comes from a smaller
file, not better code. For reading a long prompt, mlx-lm was about 70% faster than Ollama. This
post shows the numbers, explains why they come out that way, and lists two mistakes I made while
measuring.

## The setup

| item | details |
|---|---|
| Machine | MacBook with Apple M5, 10-core GPU, 32 GB of memory |
| Model | Qwen3-4B Thinking (2507), compressed to 4 bits per weight |

| engine | version | format | file size |
|---|---|---|---|
| Ollama | 0.40.16 | GGUF (llama.cpp underneath) | 2.5 GB |
| mlx-lm | 0.32.2 (MLX 0.32.5) | Apple's MLX | 2.26 GB |
| LM Studio | 0.4.28 (MLX engine 1.15.2) | MLX (the same file as mlx-lm) | 2.26 GB |

A local model does two different jobs, and I measured them separately:

- **Reading** the prompt (often called prefill)
- **Writing** the answer, one token at a time (often called decode)

Speeds are in tokens per second. A token is roughly a word or part of a word. Every number is the
median of 5 runs, after one warm-up run that I threw away.

## Test 1: a short prompt

> - **Prompt:** "Explain what a GPU is in two sentences."
> - **Answer length:** exactly 300 tokens in every engine
> - **Temperature:** 0 (no randomness in picking tokens)
>
> So all three engines did the same amount of work.

| engine | writing speed | range of 5 runs |
|---|---|---|
| mlx-lm (MLX) | 49.8 tok/s | 49.7–50.0 |
| LM Studio (MLX) | 49.1 tok/s | 48.6–49.4 |
| Ollama (GGUF) | 44.0 tok/s | 43.7–44.7 |

The two MLX engines are level, and both are 12–13% faster than Ollama. With each engine's default
settings the order is the same (LM Studio 48.4, Ollama 43.0), but the answers then run anywhere
from 135 to 1,118 tokens, and longer answers write a little slower, so I fixed the length.

## Why writing speeds are so close

This model is dense: to write one token, it reads all of its weights from memory once. The weights are far too
big to stay in the GPU's own cache, so they are streamed from memory again for every token. That
makes memory speed the limit, not the engine's code.

You can estimate the limit with one division:

```
max tokens/s = memory bandwidth (GB/s) ÷ GB of weights read per token
```

The M5 moves 153 GB per second. The two formats compress the model a little differently: GGUF
keeps some parts, such as the embedding table, at 6 bits, so Ollama's file is 2.5 GB, while the
MLX file is 2.26 GB:

```
Ollama:  153 ÷ 2.5  = 61 tokens/s at most
MLX:     153 ÷ 2.26 = 68 tokens/s at most
```

Each engine reaches 72–74% of its own limit: Ollama writes 44 tokens/s out of a possible 61, and the MLX engines about 50 out of 68. So the MLX engines write faster mainly
because they read about 9% fewer bytes per token, not because their code is better. No engine can
pass the limit for a single conversation, so they all end up close together. A few tricks change
the maths, though: see "Can you beat the memory limit?" below.

**Why don't they reach 100% of the limit?** Part of the gap is the spec sheet: a simple copy test on this Mac moved 134 GB/s,
about 87% of the 153 GB/s Apple quotes. Measured against that, the engines reach about 82–84%. The
rest goes to reading the conversation cache, launching GPU work for every token, and choosing the
next token.

**What about mixture-of-experts (MoE) models?** A MoE model reads only part of its weights for each
token: the shared layers, plus the few experts its router picks. So the division uses the active
weights, not the total:

```
max tokens/s = memory bandwidth (GB/s) ÷ GB of active weights read per token
```

For a dense model, active means all of them. `qwen3.6:35b-a3b`, also on this Mac, has 35 billion
weights but only about 3 billion active. `ollama show` lists 256 experts with 8 picked per token,
plus one shared expert. Adding up its tensors, each token reads about 2.0 GB: 1.34 GB of shared
layers and 0.67 GB of experts. Its ceiling is about 153 ÷ 2.0 = 76 tokens/s, in the same range as
the 4B model, even though all 23 GB still has to fit in memory, because the next token may pick
different experts.

I measured it with the same 300-token test: 46.8 tok/s, slightly faster than the 4B model in
Ollama (44.0), while using 23.4 GB of memory instead of 7.6 GB. That is 61% of its ceiling, lower
than the dense model's 72%, probably because picking experts and reading eight small ones per layer
uses memory less efficiently than reading a few large matrices.

## Test 2: a long prompt

Next I used a prompt of about 1,900 tokens and asked for a 100-token answer. This is closer to
real work such as answering questions about a document.

| | Ollama (GGUF) | mlx-lm (MLX) | LM Studio (MLX) | mlx-lm vs Ollama |
|---|---|---|---|---|
| reading speed | 964 tok/s | 1,627 tok/s | 1,348 tok/s | about 70% faster |
| writing speed | 40.7 tok/s | 44.4 tok/s | 44.4 tok/s | about 9% faster |

> **About the table:**
>
> - Each number is the median of 5 runs, after a warm-up run that doesn't count.
> - The prompt was 1,892 tokens in all three engines.
> - LM Studio doesn't report reading speed directly, so I divided the prompt length by its time to
>   the first token. That includes some of its own overhead, so its real reading speed may be a
>   little higher.

Reading is a different kind of work. When writing, the whole model is read from memory for every
single token. When reading, all the prompt's tokens enter the model at once, so each weight is read
from memory only once and used for all 1,892 tokens. It's like fetching the toolbox once for all the
screws, instead of walking to the shed for every screw. So memory stops being the problem: the limit
is how fast the GPU can calculate, and how well the engine's code (its matrix-multiplication
kernels) uses it. Here MLX, Apple's own framework, did clearly better.

All three engines also wrote more slowly than in Test 1. For every new token, the model looks back
over the whole conversation so far, so a longer prompt means more work per token. The writing gap,
9%, is again about the size difference between the two files.

## Memory is the other difference

| | Ollama | mlx-lm |
|---|---|---|
| short prompt | 7.6 GB loaded | 2.4 GB peak |
| long prompt | 7.6 GB loaded | 3.2 GB peak |

The two tools report memory differently, so the exact gap is approximate. The main cause is clear,
though. Ollama reserved space for a 32,768-token conversation as soon as the model loaded. mlx-lm
grows its memory as the conversation grows.

## Can you beat the memory limit?

The limit (61 tok/s for Ollama, 68 for MLX) holds for one conversation, with these weights, on this Mac. It assumes one token per
read of the weights, and 2.5 GB per read (2.26 GB for MLX). Change either and the number changes:

| trick | how it gets past the limit | the cost |
|---|---|---|
| Speculative decoding | A tiny draft model guesses the next few tokens, and the big model checks them all in one read of its weights. When the guesses are right, you get several tokens per read. | Needs a small model from the same family. The gain depends on how often the guesses are right: more on predictable text, less on creative text. |
| Smaller weights | 3-bit or 2-bit compression means fewer GB per token, so a higher ceiling. | Quality drops, especially below 4 bits. |
| MoE models | Only the active experts are read (see above). | All the weights still have to fit in memory. |
| Batching | Several conversations share one read of the weights, so total throughput goes up. | One conversation gets no faster. It helps servers, not a single user. |
| Faster memory | A chip with more memory bandwidth raises the ceiling. | Different hardware. |

Speculative decoding is the one to try on a laptop: mlx-lm has a `--draft-model` option, and LM
Studio has it built in. I tried it with Qwen3-0.6B as the draft model (MLX, 4-bit, 335 MB), on two
kinds of prompt:

> - **Explanation:** "Explain what a GPU is in two sentences."
> - **Counting** (predictable text): "Count from 1 to 100, separated by commas."

| setting | explanation (tok/s) | counting (tok/s) |
|---|---|---|
| no draft model | 49.6 | 49.8 |
| 2 draft tokens | 57.3 | 87.6 |
| 3 draft tokens | 58.1 | 92.2 |
| 4 draft tokens | 53.2 | **97.7** |

*(mlx-lm, median of 5 runs each.)*

What I noticed in the numbers:

- On counting, the speed reached 97.7 tok/s with 4 draft tokens, almost twice the speed without
  one and well past MLX's 68 tok/s limit, because 74% of the tokens came from the draft model.
- On the explanation the gain was smaller: the best was 58.1 tok/s, only 17% faster, because the
  draft guessed right about half the time.
- More draft tokens don't always mean more speed: on the explanation, 4 was slower than 3, because a
  wrong guess wastes some of the work.
- LM Studio gave similar numbers (57.0 on the explanation, 86.4 on counting), but it only accepted
  the draft model after I loaded the model with `--parallel 1`: its default of 4 parallel requests
  doesn't support a draft model with MLX.

## Two mistakes I made

**1. I measured the cache instead of the model.** My first script sent the same prompt twice. The
second run showed a reading speed of 14,183 tok/s, when the real figure is about 1,050. Ollama had
kept its work from the first run and reused it. I fixed it by starting each prompt with a unique
line. The same effect is useful in a real app: keep the start of your prompt identical between
requests and the engine can reuse its work.

Two related effects also make the speed change from run to run, so compare like with like:

- **The first run is slower.** It loads the model and prepares the GPU code, and the GPU needs a
  moment to speed up: in a memory test, the first operation after a few idle seconds ran at about a
  third of full speed. That's why I drop the first run and take the median of the rest.
- **Later turns of a chat do more calculation per token.** The cache saves re-reading the part of
  the conversation the engine has already seen, but every new token still looks back over the
  whole conversation. As the chat grows, each token costs more work, so writing speed slowly falls,
  even during one long answer.

**2. I ran two benchmarks at once.** My first long-prompt run in mlx-lm showed 848 tok/s reading
and 25 tok/s writing. Another benchmark was using the GPU at the same time. Run alone, mlx-lm gave
1,627 and 44.4. Benchmark one thing at a time.

A third lesson: one run is not enough. My first LM Studio result was 40 tok/s, which made it look
12% slower than the others. Over five runs its median was 49 tok/s, level with mlx-lm and ahead of
Ollama. Even five runs only hold for one sitting: an hour later all three engines ran 3–4% faster,
in the same order, so I compare engines measured back to back.

## What I'd choose

- **Short chat messages:** any of the three. The MLX engines write about 12% faster, mostly thanks
  to a smaller file. Pick by features and convenience.
- **Long prompts with short answers** (document Q&A, RAG, agents): MLX saves real time on a Mac.
- **Predictable output** (lists, code edits, filling a template): try a draft model. On free-form
  text the gain is small.
- **Tight on memory:** check how much the engine reserves for the conversation window, and lower
  it if you don't need it.

This was a small test: one model, one machine, one afternoon, five runs per setting. Try it on
yours.

## Commands to reproduce

**Short prompt**

```
# Ollama: read "eval rate"
ollama run qwen3:4b-thinking --verbose "Explain what a GPU is in two sentences."

# mlx-lm: read "Generation: ... tokens-per-sec"
# (the model id downloads 2.3 GB the first time; if LM Studio already has the model, use
#  --model ~/.lmstudio/models/lmstudio-community/Qwen3-4B-Thinking-2507-MLX-4bit)
uvx --python 3.12 --from mlx-lm mlx_lm.generate \
  --model lmstudio-community/Qwen3-4B-Thinking-2507-MLX-4bit \
  --prompt "Explain what a GPU is in two sentences." --max-tokens 300

# LM Studio: load qwen/qwen3-4b-thinking-2507 (MLX 4bit) and start the local server
# (lms load qwen/qwen3-4b-thinking-2507 && lms server start),
# then read "tokens_per_second" in the reply
curl http://localhost:1234/api/v0/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen/qwen3-4b-thinking-2507","messages":[{"role":"user","content":"Explain what a GPU is in two sentences."}]}'
```

**Long prompt**

```
# Create the prompt (about 1,900 tokens)
python3 -c "
s = 'You are reviewing a production incident. Background: a web service that answers customer questions started timing out after a deploy. '
q = 'Write a short, numbered list of the first five things you would check, one sentence each.'
open('long_prompt.txt', 'w').write('Ticket #1\n' + s * 80 + '\n\n' + q)
"

# Ollama: read "prompt eval rate" and "eval rate"
# (thinking is on and the answer runs to its end, so "eval rate" covers a longer answer)
ollama run qwen3:4b-thinking --verbose "$(cat long_prompt.txt)"

# mlx-lm: read "Prompt: ... tokens-per-sec" and "Generation: ... tokens-per-sec"
uvx --python 3.12 --from mlx-lm mlx_lm.generate \
  --model lmstudio-community/Qwen3-4B-Thinking-2507-MLX-4bit \
  --prompt "$(cat long_prompt.txt)" --max-tokens 100
```

Change the first line of the prompt ("Ticket #1") between Ollama runs, or you will measure the
cache as I did.

**Speculative decoding**

```
# mlx-lm with a draft model (downloads the 335 MB draft the first time)
uvx --python 3.12 --from mlx-lm mlx_lm.generate \
  --model lmstudio-community/Qwen3-4B-Thinking-2507-MLX-4bit \
  --draft-model lmstudio-community/Qwen3-0.6B-MLX-4bit --num-draft-tokens 4 \
  --prompt "Count from 1 to 100, separated by commas." --max-tokens 500
```
