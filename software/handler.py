import os
from typing import Any, Dict, List, Optional

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

import runpod


# Model repository can be overridden at deploy time via environment variable.
REPO_ID: str = os.getenv("REPO_ID", "myogen/myogen-gpt-oss-20b")


def _select_torch_dtype() -> torch.dtype:
    if torch.cuda.is_available():
        compute_capability = torch.cuda.get_device_capability()
        # Prefer bfloat16 on Ampere (sm_80) and newer; else float16 on older CUDA GPUs
        return torch.bfloat16 if compute_capability[0] >= 8 else torch.float16
    return torch.float32


# Load tokenizer and model at import time for warm start and performance.
DTYPE: torch.dtype = _select_torch_dtype()
TOKENIZER = AutoTokenizer.from_pretrained(REPO_ID, use_fast=True)
if TOKENIZER.pad_token is None:
    TOKENIZER.pad_token = TOKENIZER.eos_token

MODEL = AutoModelForCausalLM.from_pretrained(
    REPO_ID,
    device_map="auto",
    torch_dtype=DTYPE,
).eval()


def _generate(
    prompt: str,
    *,
    max_new_tokens: int = 256,
    temperature: float = 0.7,
    top_p: float = 0.9,
    top_k: int = 50,
    repetition_penalty: float = 1.05,
    do_sample: bool = True,
    stop: Optional[List[str]] = None,
    return_full_text: bool = False,
) -> Dict[str, Any]:
    inputs = TOKENIZER(prompt, return_tensors="pt")
    inputs = {k: v.to(MODEL.device) for k, v in inputs.items()}

    gen_kwargs: Dict[str, Any] = {
        "max_new_tokens": int(max_new_tokens),
        "temperature": float(temperature),
        "top_p": float(top_p),
        "top_k": int(top_k),
        "repetition_penalty": float(repetition_penalty),
        "do_sample": bool(do_sample),
        "eos_token_id": TOKENIZER.eos_token_id,
        "pad_token_id": TOKENIZER.pad_token_id,
    }

    with torch.inference_mode():
        output_ids = MODEL.generate(**inputs, **gen_kwargs)[0]

    decoded: str = TOKENIZER.decode(output_ids, skip_special_tokens=True)
    if not return_full_text and decoded.startswith(prompt):
        completion = decoded[len(prompt) :]
    else:
        completion = decoded

    if stop:
        # Truncate at the first occurrence of any stop sequence
        earliest: Optional[int] = None
        for s in stop:
            idx = completion.find(s)
            if idx != -1:
                earliest = idx if earliest is None else min(earliest, idx)
        if earliest is not None:
            completion = completion[:earliest]

    prompt_tokens = int(inputs["input_ids"].shape[-1])
    completion_tokens = int(output_ids.shape[-1]) - prompt_tokens

    return {
        "text": completion,
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": max(completion_tokens, 0),
            "total_tokens": max(prompt_tokens + completion_tokens, 0),
        },
    }


def handler(job: Dict[str, Any]) -> Dict[str, Any]:
    job_input: Dict[str, Any] = job.get("input", {}) or {}

    prompt: Optional[str] = (
        job_input.get("prompt")
        or job_input.get("text")
        or job_input.get("input")
    )
    if not prompt:
        return {"error": "Missing 'prompt' in input."}

    # Optional generation parameters
    max_new_tokens = job_input.get("max_new_tokens", 256)
    temperature = job_input.get("temperature", 0.7)
    top_p = job_input.get("top_p", 0.9)
    top_k = job_input.get("top_k", 50)
    repetition_penalty = job_input.get("repetition_penalty", 1.05)
    do_sample = job_input.get("do_sample", True)
    stop = job_input.get("stop")  # list[str] or None
    return_full_text = job_input.get("return_full_text", False)

    try:
        result = _generate(
            prompt,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            repetition_penalty=repetition_penalty,
            do_sample=do_sample,
            stop=stop,
            return_full_text=return_full_text,
        )
        return {"output": result}
    except RuntimeError as e:
        # Commonly OOM; try to provide a helpful message
        return {"error": str(e)}


runpod.serverless.start({"handler": handler})


