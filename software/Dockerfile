FROM pytorch/pytorch:2.3.1-cuda12.1-cudnn8-runtime

# Speed up HF model downloads and set cache locations
ENV HF_HOME=/root/.cache/huggingface \
    TRANSFORMERS_CACHE=/root/.cache/huggingface/hub \
    HF_HUB_ENABLE_HF_TRANSFER=1 \
    PYTHONUNBUFFERED=1

WORKDIR /workspace

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
 && rm -rf /var/lib/apt/lists/*

# Python dependencies (torch is provided by base image)
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir \
    runpod==1.7.6 \
    transformers==4.43.3 \
    accelerate==0.34.2 \
    sentencepiece==0.2.0 \
    safetensors==0.4.4 \
    hf_transfer==0.1.6

# Copy handler
COPY handler.py /handler.py

CMD ["python", "-u", "/handler.py"]


