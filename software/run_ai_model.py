#!/usr/bin/env python3
"""
Efficient model runner using modern, lightweight models optimized for Mac.
Uses models that are fast, memory-efficient, and give good results.
"""

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import argparse
import warnings

def setup_efficient_model(model_name="microsoft/Phi-3-mini-4k-instruct"):
    """
    Load an efficient model optimized for Mac performance.
    
    Args:
        model_name: Hugging Face model identifier
    
    Returns:
        pipe: Hugging Face pipeline for text generation
    """
    print(f"Loading efficient model: {model_name}")
    
    # Use pipeline for easier management
    pipe = pipeline(
        "text-generation",
        model=model_name,
        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
        device_map="auto" if torch.cuda.is_available() else None,
        trust_remote_code=True
    )
    
    print(f"Model loaded successfully!")
    return pipe

def generate_response(pipe, prompt, max_length=100, temperature=0.7):
    """
    Generate a response using the efficient model.
    """
    try:
        # Generate response
        result = pipe(
            prompt,
            max_new_tokens=max_length,
            temperature=temperature,
            do_sample=True,
            pad_token_id=pipe.tokenizer.eos_token_id,
            truncation=True
        )
        
        # Extract the generated text
        response = result[0]['generated_text']
        
        # Remove the input prompt from the response
        if response.startswith(prompt):
            response = response[len(prompt):].strip()
        
        return response
    except Exception as e:
        return f"Error generating response: {e}"

def interactive_chat(pipe):
    """
    Run an interactive chat session with the efficient model.
    """
    print("\n" + "="*50)
    print("Efficient Model Interactive Chat")
    print("Type 'quit' to exit, 'clear' to clear conversation")
    print("="*50)
    
    while True:
        user_input = input("\nYou: ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("Goodbye!")
            break
        elif user_input.lower() == 'clear':
            print("Conversation cleared.")
            continue
        elif not user_input:
            continue
        
        print("Assistant: ", end="", flush=True)
        
        try:
            response = generate_response(pipe, user_input, max_length=150)
            print(response)
                
        except Exception as e:
            print(f"Error generating response: {e}")

def main():
    parser = argparse.ArgumentParser(description="Run efficient model inference")
    parser.add_argument("--model", default="microsoft/Phi-3-mini-4k-instruct", 
                       help="Hugging Face model name")
    parser.add_argument("--prompt", type=str, help="Single prompt to generate response for")
    parser.add_argument("--interactive", action="store_true", 
                       help="Run in interactive chat mode")
    parser.add_argument("--max-length", type=int, default=100, 
                       help="Maximum length of generated text")
    parser.add_argument("--temperature", type=float, default=0.7, 
                       help="Sampling temperature")
    
    args = parser.parse_args()
    
    # Suppress warnings for cleaner output
    warnings.filterwarnings("ignore")
    
    try:
        # Load model
        pipe = setup_efficient_model(model_name=args.model)
        
        if args.interactive:
            # Interactive chat mode
            interactive_chat(pipe)
        elif args.prompt:
            # Single prompt mode
            print(f"Prompt: {args.prompt}")
            print("Generating response...")
            response = generate_response(
                pipe, args.prompt, 
                max_length=args.max_length,
                temperature=args.temperature
            )
            print(f"Response: {response}")
        else:
            # Default: show some example prompts
            example_prompts = [
                "Hello, how are you?",
                "What is artificial intelligence?",
                "Write a short poem about coding.",
            ]
            
            print("Running example prompts...\n")
            for i, prompt in enumerate(example_prompts, 1):
                print(f"Example {i}:")
                print(f"Prompt: {prompt}")
                response = generate_response(pipe, prompt, max_length=80)
                print(f"Response: {response}\n")
                print("-" * 50)
    
    except Exception as e:
        print(f"Error: {e}")
        print("\nTroubleshooting tips:")
        print("1. Try a different model: --model microsoft/DialoGPT-small")
        print("2. Check your internet connection")
        print("3. Ensure you have enough disk space")

if __name__ == "__main__":
    main()
