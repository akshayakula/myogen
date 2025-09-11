from fastapi import FastAPI
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

# Replace with your HF repo
MODEL_NAME = "myogen/myogen-gpt-oss-20b"

print(f"Loading model {MODEL_NAME}...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    device_map="auto",
    torch_dtype=torch.float16
)

app = FastAPI()

class Prompt(BaseModel):
    prompt: str
    max_new_tokens: int = 200
    temperature: float = 0.7
    top_p: float = 0.9

@app.post("/generate")
def generate_text(req: Prompt):
    inputs = tokenizer(req.prompt, return_tensors="pt").to("cuda")

    outputs = model.generate(
        **inputs,
        max_new_tokens=req.max_new_tokens,
        do_sample=True,
        temperature=req.temperature,
        top_p=req.top_p,
        eos_token_id=tokenizer.eos_token_id
    )

    # Strip the prompt from the generated sequence
    generated = outputs[0][inputs["input_ids"].shape[1]:]
    text = tokenizer.decode(generated, skip_special_tokens=True)

    return {"response": text.strip()}
