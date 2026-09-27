"""LoRA SFT (Unsloth + TRL) na zbiorze z train/build_sft.py, z uczeniem tylko na odpowiedziach asystenta.

    python train/sft_lora.py --model Qwen/Qwen3.5-4B --out /workspace/runs/q35-4b-lora --epochs 2 --rank 32
    python train/sft_lora.py --model google/gemma-4-12B --out ... --load-4bit     # QLoRA dla 12B
Wynik: <out>/adapter (PEFT) + <out>/train_log.json. Konwersja do GGUF: llama.cpp convert_lora_to_gguf.py.
"""

import argparse
import json
import time
from pathlib import Path


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
    p.add_argument("--load-4bit", action="store_true")
    p.add_argument("--no-think", action="store_true", help="szablon czatu z enable_thinking=False (Qwen3.5)")
    p.add_argument("--max-steps", type=int, default=-1)
    p.add_argument("--template-from", help="repo HF, z którego wziąć szablon czatu (modele -Base go nie mają)")
    p.add_argument("--mask-think", action="store_true",
                   help="modele myślące (Qwen3.5): strata dopiero od '</think>\\n\\n', inaczej model uczy się pomijać myślenie")
    a = p.parse_args()

    from unsloth import FastModel
    from unsloth.chat_templates import train_on_responses_only
    from datasets import load_dataset
    from trl import SFTConfig, SFTTrainer

    t0 = time.time()
    model, tok = FastModel.from_pretrained(a.model, max_seq_length=a.max_len, load_in_4bit=a.load_4bit,
                                           full_finetuning=False)
    model = FastModel.get_peft_model(model, r=a.rank, lora_alpha=a.rank, lora_dropout=0.0,
                                     finetune_vision_layers=False, finetune_language_layers=True,
                                     finetune_attention_modules=True, finetune_mlp_modules=True, random_state=0)
    proc = getattr(tok, "tokenizer", tok)  # procesory VLM mają tokenizer w środku
    if a.template_from:
        from transformers import AutoTokenizer
        proc.chat_template = AutoTokenizer.from_pretrained(a.template_from).chat_template
        if tok is not proc:
            tok.chat_template = proc.chat_template

    def fmt(batch):
        texts = []
        for msgs in batch["messages"]:
            kw = {"enable_thinking": False} if a.no_think else {}
            texts.append(proc.apply_chat_template(msgs, tokenize=False, add_generation_prompt=False, **kw))
        return {"text": texts}

    ds = load_dataset("json", data_files={"train": a.train, "val": a.val})
    # train_on_responses_only liczy stratę na każdej odpowiedzi asystenta, więc rozmowy wieloturowe (v2) pomijamy
    ds = ds.filter(lambda r: sum(m["role"] == "assistant" for m in r["messages"]) == 1)
    ds = ds.map(fmt, batched=True, remove_columns=ds["train"].column_names)
    cfg = SFTConfig(output_dir=a.out, dataset_text_field="text", max_length=a.max_len, per_device_train_batch_size=a.batch,
                    gradient_accumulation_steps=a.grad_acc, num_train_epochs=a.epochs, max_steps=a.max_steps,
                    learning_rate=a.lr, lr_scheduler_type="cosine", warmup_ratio=0.03, logging_steps=10,
                    eval_strategy="steps", eval_steps=100, save_strategy="no", bf16=True, report_to="none",
                    optim="adamw_8bit", weight_decay=0.0, seed=0, packing=False)
    trainer = SFTTrainer(model=model, tokenizer=proc, train_dataset=ds["train"], eval_dataset=ds["val"], args=cfg)
    sample = ds["train"][0]["text"]
    # znaczniki tur zależą od rodziny modelu: Qwen (ChatML), Gemma (<start_of_turn> / <|turn>)
    markers = [("<|im_start|>user\n", "<|im_start|>assistant\n"), ("<start_of_turn>user\n", "<start_of_turn>model\n"),
               ("<|turn>user\n", "<|turn>model\n"), ("[INST]", "[/INST]")]
    if a.mask_think:
        markers.insert(0, ("<|im_start|>user\n", "</think>\n\n"))
    for inst, resp in markers:
        if inst in sample and resp in sample:
            trainer = train_on_responses_only(trainer, instruction_part=inst, response_part=resp)
            break
    labels = trainer.train_dataset[0]["labels"]
    n_train = sum(1 for x in labels if x != -100)
    print(f"markers={inst!r}/{resp!r} trained_tokens={n_train}/{len(labels)}", flush=True)
    assert 0 < n_train < len(labels), "maskowanie odpowiedzi nie zadziałało"
    stats = trainer.train()
    out = Path(a.out)
    model.save_pretrained(out / "adapter")
    proc.save_pretrained(out / "adapter")
    # ponowne evaluate() po treningu w Unsloth daje zawyżony loss (np. 5.1 zamiast 0.96), więc bierzemy ostatni pomiar z treningu
    metrics = next((h for h in reversed(trainer.state.log_history) if "eval_loss" in h), {})
    (out / "train_log.json").write_text(json.dumps({"args": vars(a), "train": stats.metrics, "eval": metrics,
                                                    "minutes": round((time.time() - t0) / 60, 1)}, indent=1))
    print(json.dumps({"train_loss": stats.metrics.get("train_loss"), "eval": metrics}, indent=1))


if __name__ == "__main__":
    main()
