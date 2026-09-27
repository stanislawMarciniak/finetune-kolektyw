"""LoRA BF16 bez Unsloth (transformers + PEFT + TRL) — dla modeli, których Unsloth jeszcze nie obsługuje (Gemma-4 pt).

    python train/sft_peft.py --model google/gemma-4-12B --template-from google/gemma-4-12B-it --out ~/train/gemma4-12b-pt
Dane jak w sft_lora.py (data/sft/train.jsonl, val.jsonl); strata tylko na odpowiedzi (format prompt/completion TRL).
Wynik: <out>/adapter (PEFT) + <out>/train_log.json.
"""

import argparse
import json
import time
from pathlib import Path

LORA_TARGETS = r"^(?!.*(vision|audio|multi_modal|embed_vision|embed_audio)).*\.(q_proj|k_proj|v_proj|o_proj|gate_proj|up_proj|down_proj)$"


def load_model(name):
    import torch
    from transformers import AutoModelForCausalLM, AutoModelForImageTextToText
    kw = dict(dtype=torch.bfloat16, attn_implementation="sdpa")
    try:
        return AutoModelForCausalLM.from_pretrained(name, **kw)
    except (ValueError, KeyError):
        return AutoModelForImageTextToText.from_pretrained(name, **kw)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--model", required=True)
    p.add_argument("--train", default="data/sft/train.jsonl")
    p.add_argument("--val", default="data/sft/val.jsonl")
    p.add_argument("--out", required=True)
    p.add_argument("--epochs", type=float, default=2)
    p.add_argument("--lr", type=float, default=1e-4)
    p.add_argument("--rank", type=int, default=32)
    p.add_argument("--max-len", type=int, default=4096)
    p.add_argument("--batch", type=int, default=4)
    p.add_argument("--grad-acc", type=int, default=4)
    p.add_argument("--max-steps", type=int, default=-1)
    p.add_argument("--template-from", help="repo HF, z którego wziąć szablon czatu (modele -Base / -pt go nie mają)")
    p.add_argument("--template-file", help="plik jinja z szablonem czatu; ten sam trzeba podać llama-server (--chat-template-file)")
    a = p.parse_args()

    from datasets import load_dataset
    from peft import LoraConfig
    from transformers import AutoTokenizer
    from trl import SFTConfig, SFTTrainer

    t0 = time.time()
    tok = AutoTokenizer.from_pretrained(a.model)
    if a.template_from:
        tok.chat_template = AutoTokenizer.from_pretrained(a.template_from).chat_template
    if a.template_file:
        tok.chat_template = Path(a.template_file).read_text(encoding="utf-8")
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    model = load_model(a.model)
    model.config.use_cache = False

    def split(row):
        msgs = row["messages"]
        return {"prompt": msgs[:-1], "completion": msgs[-1:]}

    ds = load_dataset("json", data_files={"train": a.train, "val": a.val})
    ds = ds.map(split, remove_columns=ds["train"].column_names)
    cfg = SFTConfig(output_dir=a.out, max_length=a.max_len, per_device_train_batch_size=a.batch,
                    per_device_eval_batch_size=a.batch, gradient_accumulation_steps=a.grad_acc, num_train_epochs=a.epochs,
                    max_steps=a.max_steps, learning_rate=a.lr, lr_scheduler_type="cosine", warmup_steps=10,
                    logging_steps=10, eval_strategy="steps", eval_steps=50, save_strategy="no", bf16=True,
                    report_to="none", gradient_checkpointing=True, completion_only_loss=True, seed=0)
    lora = LoraConfig(r=a.rank, lora_alpha=a.rank, lora_dropout=0.0, target_modules=LORA_TARGETS, task_type="CAUSAL_LM")
    trainer = SFTTrainer(model=model, args=cfg, train_dataset=ds["train"], eval_dataset=ds["val"],
                         processing_class=tok, peft_config=lora)
    row = trainer.train_dataset[0]
    if "labels" in row:  # TRL 1.x maskuje prompt w labels (-100)
        mask = [int(x != -100) for x in row["labels"]]
    else:
        keys = [k for k in row if k.endswith("mask") and k != "attention_mask"]
        mask = row[keys[0]] if keys else []
    print(f"tokens={len(row['input_ids'])} trained={sum(mask)}", flush=True)
    assert 0 < sum(mask) < len(row["input_ids"]), "maskowanie odpowiedzi nie zadziałało"
    trainer.model.print_trainable_parameters()
    stats = trainer.train()
    out = Path(a.out)
    trainer.model.save_pretrained(out / "adapter")
    tok.save_pretrained(out / "adapter")
    metrics = next((h for h in reversed(trainer.state.log_history) if "eval_loss" in h), {})
    (out / "train_log.json").write_text(json.dumps({"args": vars(a), "train": stats.metrics, "eval": metrics,
                                                    "minutes": round((time.time() - t0) / 60, 1)}, indent=1))
    print(json.dumps({"train_loss": stats.metrics.get("train_loss"), "eval": metrics}, indent=1))


if __name__ == "__main__":
    main()
