# Myogen AI Model Runner

A lightweight, memory-efficient AI model runner optimized for Mac systems. This project provides an easy way to run AI text generation models locally without overwhelming your system's memory.

## 🚀 Quick Start

### 1. Setup Environment
```bash
cd /Users/akshayakula/Developer/myogen/software
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Run the Model
```bash
# Quick test
python run_ai_model.py --prompt "Hello, how are you?"

# Interactive chat
python run_ai_model.py --interactive

# Try different models
python run_ai_model.py --model "microsoft/DialoGPT-medium" --prompt "Tell me a joke"
```

## 📁 Project Structure

```
software/
├── run_ai_model.py          # Main AI model runner
├── yolo_webcam.py          # YOLO webcam scene description generator
├── test_yolo_setup.py      # Test YOLO and webcam setup
├── run_yolo_example.py     # Example usage for YOLO webcam
├── requirements.txt         # Python dependencies
├── README.md               # This documentation
├── Myogentrain.ipynb       # Original ORPO training notebook
├── orpo_pairs_best_contact.jsonl  # Training data
└── venv/                   # Virtual environment
```

## 🤖 Available Models

The script supports various lightweight models optimized for Mac:

- **microsoft/DialoGPT-small** (124M parameters) - Fastest, good for testing
- **microsoft/DialoGPT-medium** (355M parameters) - Balanced performance
- **microsoft/Phi-3-mini-4k-instruct** (3.8B parameters) - More capable, still efficient

## 🔧 Usage Options

### Command Line Arguments
```bash
python run_ai_model.py [options]

Options:
  --model TEXT           Model name (default: microsoft/Phi-3-mini-4k-instruct)
  --prompt TEXT          Single prompt to generate response for
  --interactive          Run in interactive chat mode
  --max-length INTEGER   Maximum length of generated text (default: 100)
  --temperature FLOAT    Sampling temperature (default: 0.7)
```

### Examples

**Single Prompt:**
```bash
python run_ai_model.py --prompt "Explain quantum computing in simple terms"
```

**Interactive Chat:**
```bash
python run_ai_model.py --interactive
```

**Custom Model:**
```bash
python run_ai_model.py --model "microsoft/DialoGPT-small" --prompt "Hello"
```

**Adjust Parameters:**
```bash
python run_ai_model.py --prompt "Write a story" --max-length 200 --temperature 0.8
```

## 💡 Performance Tips

- **Start with DialoGPT-small** for fastest performance
- **Use CPU mode** if you experience memory issues
- **Keep max-length under 200** for best performance
- **Temperature 0.7-0.8** gives good balance of creativity and coherence

## 🛠️ Troubleshooting

### Common Issues

1. **Model loading slowly:**
   - Try a smaller model: `--model microsoft/DialoGPT-small`
   - Ensure good internet connection for model download

2. **Memory issues:**
   - The script automatically uses CPU mode to avoid memory pressure
   - Close other applications if needed

3. **Poor responses:**
   - Try different temperature settings (0.3-0.9)
   - Use more specific prompts
   - Try a different model

### System Requirements

- **macOS** (tested on Apple Silicon)
- **Python 3.8+**
- **8GB+ RAM** (16GB+ recommended)
- **Internet connection** for model downloads

## 📚 Background

This project started with ORPO (Odds Ratio Preference Optimization) training experiments using the `Myogentrain.ipynb` notebook. The original goal was to fine-tune large language models, but we discovered that smaller, more efficient models work better for local deployment on Mac systems.

The training data in `orpo_pairs_best_contact.jsonl` contains preference pairs used for ORPO training, demonstrating the preference optimization approach.

## 🔄 Model Comparison

| Model | Parameters | Load Time | Memory Usage | Best For |
|-------|------------|-----------|--------------|----------|
| DialoGPT-small | 124M | ~5s | Low | Testing, quick responses |
| DialoGPT-medium | 355M | ~10s | Moderate | Balanced performance |
| Phi-3-mini | 3.8B | ~15s | Higher | More capable responses |

## 🎥 YOLO Webcam Scene Description

The project now includes a YOLO webcam detector that captures frames every 5 seconds and generates scene descriptions in a specific format for AI training data.

### Quick Start with YOLO

```bash
# Test setup
python test_yolo_setup.py

# Run YOLO webcam detection
python yolo_webcam.py

# Run with examples
python run_yolo_example.py
```

### YOLO Features

- **Continuous real-time detection**: Processes every frame (~10 FPS)
- **Object-focused**: Excludes 'person' by default to focus on everyday objects
- **Mathematical analysis**: Uses proper math for size, position, and orientation calculations
- **Scene descriptions**: Outputs in the format:
  ```
  Scene: A single everyday object is visible.
  Object identity: {object_name}.
  Object size: {size}. Object position: {distance}, {horizontal}, {vertical} relative to the camera.
  Object orientation: {orientation} around the {axis}.
  ```
- **Live preview**: Shows webcam feed with detection boxes and frame counter
- **Save options**: Save detected frames and scene descriptions to files
- **Configurable**: Adjust confidence threshold, excluded classes, and camera

### YOLO Usage Examples

```bash
# Basic continuous detection (excludes 'person' by default)
python yolo_webcam.py

# Include person detection
python yolo_webcam.py --include-person

# Exclude multiple classes
python yolo_webcam.py --exclude person car bicycle

# Save images and output to file
python yolo_webcam.py --save-images --output scene_descriptions.txt

# Higher confidence threshold
python yolo_webcam.py --confidence 0.7
```

## 🎯 Next Steps

- Try different AI models to find your preferred balance of speed vs capability
- Use the YOLO webcam to generate training data for scene descriptions
- Experiment with temperature and max-length parameters
- Use interactive mode for conversations
- Check out the original training notebook for ORPO experiments

## 📝 Notes

- Models are downloaded and cached locally after first use
- The script automatically handles device selection (CPU/MPS)
- All models use efficient quantization when possible
- Memory usage is optimized for Mac systems
