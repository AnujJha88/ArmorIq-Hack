---
description: ML research workflow for paper implementation, experimentation, and reproducibility
---

# ML Research Workflow

## Phase 1: Paper Reading & Understanding

### 1.1 Reading Strategy
```markdown
1. **First Pass (10 min)**
   - Read title, abstract, introduction, conclusion
   - Look at figures and tables
   - Identify: What problem? What approach? What results?

2. **Second Pass (1 hour)**
   - Read entire paper, skip proofs/derivations
   - Note key equations, algorithms, architecture diagrams
   - Identify what you don't understand

3. **Third Pass (Deep dive)**
   - Understand every equation and design choice
   - Re-derive key results yourself
   - Think about limitations and extensions
```

### 1.2 Paper Notes Template
```markdown
# Paper: [Title]
**Authors:** 
**Venue/Year:** 
**Link:** 

## Problem Statement
- What problem does this solve?
- Why is it important?

## Key Contributions
1. 
2. 
3. 

## Method Summary
- Core idea in 2-3 sentences
- Key equations (LaTeX)

## Architecture/Algorithm
[Diagram or pseudocode]

## Experiments
- Datasets used:
- Baselines compared:
- Key metrics:
- Main results:

## Strengths
- 

## Weaknesses/Limitations
- 

## Questions/Ideas
- Things to try
- Extensions
- What's unclear

## Code/Resources
- Official repo:
- Other implementations:
```

---

## Phase 2: Environment Setup

### 2.1 Reproducible Research Structure
```
research_project/
├── configs/
│   ├── base.yaml
│   └── experiment_1.yaml
├── data/
│   ├── raw/
│   └── processed/
├── notebooks/
│   ├── 01_exploration.ipynb
│   └── 02_analysis.ipynb
├── src/
│   ├── data/
│   ├── models/
│   ├── training/
│   └── evaluation/
├── experiments/
│   └── exp_001/
│       ├── checkpoints/
│       ├── logs/
│       └── config.yaml
├── scripts/
│   ├── train.py
│   └── evaluate.py
├── requirements.txt
└── README.md
```

### 2.2 Experiment Tracking Setup
```python
# Using Weights & Biases
import wandb

wandb.init(
    project="project-name",
    name="experiment-001",
    config={
        "learning_rate": 1e-4,
        "batch_size": 32,
        "architecture": "transformer",
        "dataset": "custom",
    }
)

# Log metrics
wandb.log({"loss": loss, "accuracy": acc, "epoch": epoch})

# Log artifacts
wandb.save("model.pt")
```

```python
# Using MLflow
import mlflow

mlflow.set_experiment("experiment-name")

with mlflow.start_run():
    mlflow.log_params(config)
    mlflow.log_metric("accuracy", accuracy)
    mlflow.pytorch.log_model(model, "model")
```

---

## Phase 3: Paper Implementation

### 3.1 Implementation Checklist
```markdown
- [ ] Understand the architecture completely
- [ ] Identify which components need custom implementation
- [ ] Find existing implementations of sub-components
- [ ] Start with simplest version (no bells and whistles)
- [ ] Add features incrementally
- [ ] Verify against paper's reported numbers
```

### 3.2 Common PyTorch Patterns

```python
# Custom Model
import torch
import torch.nn as nn

class ResearchModel(nn.Module):
    def __init__(self, config):
        super().__init__()
        self.config = config
        
        # Build layers from config
        self.encoder = self._build_encoder()
        self.decoder = self._build_decoder()
        
        # Initialize weights
        self.apply(self._init_weights)
    
    def _init_weights(self, module):
        if isinstance(module, nn.Linear):
            nn.init.xavier_uniform_(module.weight)
            if module.bias is not None:
                nn.init.zeros_(module.bias)
    
    def forward(self, x, **kwargs):
        encoded = self.encoder(x)
        decoded = self.decoder(encoded)
        return decoded
```

```python
# Training Loop with Best Practices
def train_epoch(model, loader, optimizer, scheduler, device):
    model.train()
    total_loss = 0
    
    for batch_idx, batch in enumerate(tqdm(loader)):
        # Move to device
        batch = {k: v.to(device) for k, v in batch.items()}
        
        # Forward
        optimizer.zero_grad()
        outputs = model(**batch)
        loss = outputs.loss
        
        # Backward
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()
        scheduler.step()
        
        total_loss += loss.item()
        
        # Logging
        if batch_idx % 100 == 0:
            wandb.log({"train_loss": loss.item(), "lr": scheduler.get_last_lr()[0]})
    
    return total_loss / len(loader)
```

### 3.3 Debugging Model Issues
```python
# Check gradients
for name, param in model.named_parameters():
    if param.grad is not None:
        print(f"{name}: grad_norm = {param.grad.norm():.4f}")

# Check for NaN/Inf
def check_tensor(x, name="tensor"):
    if torch.isnan(x).any():
        print(f"NaN detected in {name}")
    if torch.isinf(x).any():
        print(f"Inf detected in {name}")

# Overfit on single batch first
single_batch = next(iter(train_loader))
for i in range(1000):
    loss = train_step(model, single_batch)
    if i % 100 == 0:
        print(f"Step {i}: loss = {loss:.4f}")
# Loss should go to near-zero
```

---

## Phase 4: Experiment Management

### 4.1 Config-Driven Experiments
```yaml
# configs/base.yaml
model:
  name: transformer
  hidden_dim: 512
  num_layers: 6
  num_heads: 8
  dropout: 0.1

training:
  batch_size: 32
  learning_rate: 1e-4
  weight_decay: 0.01
  epochs: 100
  warmup_steps: 1000

data:
  train_path: data/train.csv
  val_path: data/val.csv
  max_length: 512
```

```python
# Load config with Hydra
import hydra
from omegaconf import DictConfig

@hydra.main(config_path="configs", config_name="base")
def main(cfg: DictConfig):
    model = build_model(cfg.model)
    train(model, cfg.training, cfg.data)

# Run experiments
# python train.py model.hidden_dim=768 training.lr=5e-5
```

### 4.2 Ablation Studies
```python
# Systematic ablation
ablations = [
    {"name": "baseline", "config": {}},
    {"name": "no_dropout", "config": {"model.dropout": 0}},
    {"name": "small_model", "config": {"model.hidden_dim": 256}},
    {"name": "large_lr", "config": {"training.lr": 1e-3}},
]

for ablation in ablations:
    config = merge_configs(base_config, ablation["config"])
    result = run_experiment(config)
    save_result(ablation["name"], result)
```

---

## Phase 5: Analysis & Visualization

### 5.1 Learning Curves
```python
import matplotlib.pyplot as plt

fig, axes = plt.subplots(1, 2, figsize=(12, 4))

axes[0].plot(train_losses, label='Train')
axes[0].plot(val_losses, label='Val')
axes[0].set_xlabel('Epoch')
axes[0].set_ylabel('Loss')
axes[0].legend()

axes[1].plot(train_accs, label='Train')
axes[1].plot(val_accs, label='Val')
axes[1].set_xlabel('Epoch')
axes[1].set_ylabel('Accuracy')
axes[1].legend()

plt.tight_layout()
plt.savefig('learning_curves.png', dpi=150)
```

### 5.2 Attention Visualization
```python
import seaborn as sns

def visualize_attention(attention_weights, tokens):
    plt.figure(figsize=(10, 8))
    sns.heatmap(
        attention_weights.cpu().numpy(),
        xticklabels=tokens,
        yticklabels=tokens,
        cmap='viridis'
    )
    plt.title('Attention Weights')
    plt.savefig('attention.png', dpi=150)
```

---

## Phase 6: Writing & Reproducibility

### 6.1 Reproducibility Checklist
```markdown
- [ ] Fixed random seeds (torch, numpy, python)
- [ ] Documented all hyperparameters
- [ ] Saved model checkpoints
- [ ] Logged training metrics
- [ ] requirements.txt with versions
- [ ] README with exact commands to reproduce
- [ ] Data preprocessing scripts included
```

### 6.2 Set All Seeds
```python
import random
import numpy as np
import torch

def set_seed(seed=42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
```

---

## Quick Reference: Research Tools

```python
# Essential imports
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, Dataset

# Experiment tracking
import wandb  # or mlflow

# Config management  
from omegaconf import OmegaConf
import hydra

# Progress & logging
from tqdm import tqdm
import logging

# Analysis
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
```
