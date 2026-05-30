"""
train_model.py
==============
Mongolian Sentiment Analysis Model — Fine-tuning Pipeline

Llama-3 (8B) загварыг Facebook группуудаас цуглуулсан
Монгол хэлний өгөгдөл дээр тусгайлан сургаж (fine-tune via QLoRA) sentiment
classification загвар бүтээнэ.

Загварын архитектур:
  - Base: meta-llama/Meta-Llama-3-8B-Instruct
  - Method: Parameter-Efficient Fine-Tuning (PEFT) with QLoRA (4-bit quantization)
  - Labels: negative(0), neutral(1), positive(2)

Hyperparameters (GridSearch-ээр сонгосон):
  - Learning rate: 2e-5
  - Epochs: 3
  - Batch size: 16
  - Warmup steps: 100
  - Weight decay: 0.01

Ашиглах:
  python train_model.py --data data/processed/ --output models/mongolian_sentiment_v1/

Шаардлагатай сангууд:
  pip install torch transformers datasets scikit-learn
"""

import os
import json
import time
import logging
import argparse
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/training/training.log", encoding="utf-8"),
    ]
)
logger = logging.getLogger(__name__)

try:
    import torch
    import torch.nn as nn
    from torch.utils.data import DataLoader, Dataset
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

try:
    from transformers import (
        AutoTokenizer,
        AutoModelForSequenceClassification,
        AdamW,
        get_linear_schedule_with_warmup,
        BitsAndBytesConfig
    )
    from peft import LoraConfig, get_peft_model, TaskType
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False

try:
    from sklearn.metrics import (
        accuracy_score,
        f1_score,
        precision_score,
        recall_score,
        classification_report,
        confusion_matrix,
    )
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

from config import TRAINING_CONFIG


# ─── Dataset Class ────────────────────────────────────────────────────────────

class SentimentDataset(Dataset if HAS_TORCH else object):
    """Mongolian sentiment dataset for PyTorch DataLoader."""

    def __init__(self, file_path: str, tokenizer, max_length: int = 256):
        self.samples = []
        self.tokenizer = tokenizer
        self.max_length = max_length

        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                item = json.loads(line.strip())
                if "text" in item and "label" in item:
                    self.samples.append(item)

        logger.info(f"  Dataset loaded: {len(self.samples)} samples from {file_path}")

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        item = self.samples[idx]
        encoding = self.tokenizer(
            item["text"],
            padding="max_length",
            truncation=True,
            max_length=self.max_length,
            return_tensors="pt",
        )
        return {
            "input_ids": encoding["input_ids"].squeeze(),
            "attention_mask": encoding["attention_mask"].squeeze(),
            "labels": torch.tensor(item["label"], dtype=torch.long),
        }


# ─── Training Loop ────────────────────────────────────────────────────────────

def train_epoch(model, dataloader, optimizer, scheduler, device):
    """Нэг epoch-ийн сургалт."""
    model.train()
    total_loss = 0
    correct = 0
    total = 0

    for batch_idx, batch in enumerate(dataloader):
        input_ids = batch["input_ids"].to(device)
        attention_mask = batch["attention_mask"].to(device)
        labels = batch["labels"].to(device)

        optimizer.zero_grad()
        outputs = model(input_ids=input_ids, attention_mask=attention_mask, labels=labels)

        loss = outputs.loss
        logits = outputs.logits

        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()
        scheduler.step()

        total_loss += loss.item()
        preds = torch.argmax(logits, dim=1)
        correct += (preds == labels).sum().item()
        total += labels.size(0)

        if (batch_idx + 1) % 10 == 0:
            logger.info(
                f"    Batch {batch_idx+1}: loss={loss.item():.4f}, "
                f"acc={correct/total:.4f}"
            )

    avg_loss = total_loss / len(dataloader)
    accuracy = correct / total
    return avg_loss, accuracy


def evaluate(model, dataloader, device):
    """Validation / Test evaluation."""
    model.eval()
    all_preds = []
    all_labels = []
    total_loss = 0

    with torch.no_grad():
        for batch in dataloader:
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["labels"].to(device)

            outputs = model(input_ids=input_ids, attention_mask=attention_mask, labels=labels)
            total_loss += outputs.loss.item()

            preds = torch.argmax(outputs.logits, dim=1)
            all_preds.extend(preds.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())

    avg_loss = total_loss / len(dataloader)
    accuracy = accuracy_score(all_labels, all_preds)
    f1_macro = f1_score(all_labels, all_preds, average="macro")
    f1_weighted = f1_score(all_labels, all_preds, average="weighted")
    precision = precision_score(all_labels, all_preds, average="macro")
    recall = recall_score(all_labels, all_preds, average="macro")

    return {
        "loss": avg_loss,
        "accuracy": accuracy,
        "f1_macro": f1_macro,
        "f1_weighted": f1_weighted,
        "precision": precision,
        "recall": recall,
        "predictions": all_preds,
        "labels": all_labels,
    }


# ─── Main Training Pipeline ──────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Mongolian Sentiment Model Training")
    parser.add_argument("--data", type=str, default=TRAINING_CONFIG["processed_data_dir"])
    parser.add_argument("--output", type=str, default=TRAINING_CONFIG["model_output_dir"])
    parser.add_argument("--epochs", type=int, default=TRAINING_CONFIG["epochs"])
    parser.add_argument("--batch-size", type=int, default=TRAINING_CONFIG["batch_size"])
    parser.add_argument("--lr", type=float, default=TRAINING_CONFIG["learning_rate"])
    args = parser.parse_args()

    if not HAS_TORCH or not HAS_TRANSFORMERS:
        logger.error("PyTorch болон Transformers суулгах шаардлагатай")
        logger.error("  pip install torch transformers")
        return

    # ── Setup ──
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"Device: {device}")
    logger.info(f"Training config: epochs={args.epochs}, batch_size={args.batch_size}, lr={args.lr}")

    # ── Load tokenizer and model ──
    logger.info(f"Loading base LLM for QLoRA: {TRAINING_CONFIG['base_model']}")
    
    tokenizer = AutoTokenizer.from_pretrained(TRAINING_CONFIG["base_model"])
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
        
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16
    )

    base_model = AutoModelForSequenceClassification.from_pretrained(
        TRAINING_CONFIG["base_model"],
        num_labels=TRAINING_CONFIG["num_labels"],
        quantization_config=bnb_config,
        device_map="auto"
    )
    
    peft_config = LoraConfig(
        task_type=TaskType.SEQ_CLS,
        inference_mode=False,
        r=TRAINING_CONFIG["lora_r"],
        lora_alpha=TRAINING_CONFIG["lora_alpha"],
        lora_dropout=TRAINING_CONFIG["lora_dropout"],
        target_modules=TRAINING_CONFIG["target_modules"]
    )
    
    model = get_peft_model(base_model, peft_config)
    model.print_trainable_parameters()

    # ── Load datasets ──
    train_dataset = SentimentDataset(
        os.path.join(args.data, "train.jsonl"), tokenizer, TRAINING_CONFIG["max_seq_length"]
    )
    val_dataset = SentimentDataset(
        os.path.join(args.data, "val.jsonl"), tokenizer, TRAINING_CONFIG["max_seq_length"]
    )

    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=args.batch_size)

    # ── Optimizer & Scheduler ──
    optimizer = AdamW(model.parameters(), lr=args.lr, weight_decay=TRAINING_CONFIG["weight_decay"])
    total_steps = len(train_loader) * args.epochs
    scheduler = get_linear_schedule_with_warmup(
        optimizer,
        num_warmup_steps=TRAINING_CONFIG["warmup_steps"],
        num_training_steps=total_steps,
    )

    # ── Training ──
    logger.info("=" * 60)
    logger.info("СУРГАЛТ ЭХЭЛЛЭЭ")
    logger.info("=" * 60)

    best_val_f1 = 0.0
    training_history = []
    start_time = time.time()

    for epoch in range(1, args.epochs + 1):
        epoch_start = time.time()
        logger.info(f"\n{'='*40}")
        logger.info(f"Epoch {epoch}/{args.epochs}")
        logger.info(f"{'='*40}")

        # Train
        train_loss, train_acc = train_epoch(model, train_loader, optimizer, scheduler, device)
        logger.info(f"  Train — loss: {train_loss:.4f}, accuracy: {train_acc:.4f}")

        # Validate
        val_metrics = evaluate(model, val_loader, device)
        logger.info(
            f"  Val   — loss: {val_metrics['loss']:.4f}, "
            f"accuracy: {val_metrics['accuracy']:.4f}, "
            f"F1(macro): {val_metrics['f1_macro']:.4f}"
        )

        epoch_time = time.time() - epoch_start
        logger.info(f"  Epoch duration: {epoch_time:.1f}s")

        training_history.append({
            "epoch": epoch,
            "train_loss": train_loss,
            "train_accuracy": train_acc,
            "val_loss": val_metrics["loss"],
            "val_accuracy": val_metrics["accuracy"],
            "val_f1_macro": val_metrics["f1_macro"],
            "val_f1_weighted": val_metrics["f1_weighted"],
            "epoch_time_seconds": epoch_time,
        })

        # Save best model
        if val_metrics["f1_macro"] > best_val_f1:
            best_val_f1 = val_metrics["f1_macro"]
            os.makedirs(args.output, exist_ok=True)
            model.save_pretrained(args.output)
            tokenizer.save_pretrained(args.output)
            logger.info(f"  ✓ Best model saved (F1={best_val_f1:.4f})")

    total_time = time.time() - start_time
    logger.info(f"\nНийт сургалтын хугацаа: {total_time:.1f}s")

    # ── Save training history ──
    os.makedirs(args.output, exist_ok=True)
    history_path = os.path.join(args.output, "training_history.json")
    with open(history_path, "w", encoding="utf-8") as f:
        json.dump(training_history, f, indent=2, ensure_ascii=False)
    logger.info(f"Training history saved: {history_path}")

    logger.info("=" * 60)
    logger.info("СУРГАЛТ АМЖИЛТТАЙ ДУУСЛАА ✓")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
