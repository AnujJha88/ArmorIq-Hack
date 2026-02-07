---
description: Fine-tuning LLMs with LoRA, QLoRA, and full fine-tuning techniques
---

# LLM Fine-Tuning Workflow

## Setup

// turbo
```powershell
pip install transformers datasets peft accelerate bitsandbytes trl
```

---

## Data Preparation

### Instruction Format
```python
def format_instruction(example):
    return f"""### Instruction:
{example['instruction']}

### Input:
{example['input']}

### Response:
{example['output']}"""

# Or chat format
def format_chat(example):
    return {
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": example['instruction']},
            {"role": "assistant", "content": example['output']}
        ]
    }
```

---

## LoRA Fine-Tuning (Recommended)

```python
from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments
from peft import LoraConfig, get_peft_model, TaskType
from trl import SFTTrainer

# Load base model
model = AutoModelForCausalLM.from_pretrained(
    "mistralai/Mistral-7B-v0.1",
    torch_dtype=torch.float16,
    device_map="auto"
)
tokenizer = AutoTokenizer.from_pretrained("mistralai/Mistral-7B-v0.1")
tokenizer.pad_token = tokenizer.eos_token

# LoRA config
lora_config = LoraConfig(
    r=16,                      # Rank
    lora_alpha=32,             # Alpha scaling
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type=TaskType.CAUSAL_LM
)

model = get_peft_model(model, lora_config)
model.print_trainable_parameters()  # Should be ~0.1-1% of total

# Training
training_args = TrainingArguments(
    output_dir="./lora-output",
    num_train_epochs=3,
    per_device_train_batch_size=4,
    gradient_accumulation_steps=4,
    learning_rate=2e-4,
    warmup_ratio=0.03,
    logging_steps=10,
    save_strategy="epoch",
    fp16=True,
)

trainer = SFTTrainer(
    model=model,
    train_dataset=dataset,
    args=training_args,
    tokenizer=tokenizer,
    max_seq_length=2048,
)

trainer.train()
model.save_pretrained("./lora-adapter")
```

---

## QLoRA (4-bit Quantized)

```python
from transformers import BitsAndBytesConfig

# Quantization config
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_use_double_quant=True,
)

model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-2-7b-hf",
    quantization_config=bnb_config,
    device_map="auto"
)

# Apply LoRA on quantized model
model = get_peft_model(model, lora_config)
```

---

## Inference with Fine-Tuned Model

```python
from peft import PeftModel

# Load base + adapter
base_model = AutoModelForCausalLM.from_pretrained("base-model")
model = PeftModel.from_pretrained(base_model, "./lora-adapter")

# Merge for faster inference (optional)
model = model.merge_and_unload()

# Generate
inputs = tokenizer("Your prompt here", return_tensors="pt")
outputs = model.generate(**inputs, max_new_tokens=256)
print(tokenizer.decode(outputs[0]))
```

---

## Tips

1. **Start small**: Test on subset first
2. **Monitor loss**: Should decrease smoothly  
3. **Check outputs**: Sample generations during training
4. **LoRA rank**: Start with r=8-16, increase if needed
5. **Learning rate**: 1e-4 to 5e-4 typical for LoRA
