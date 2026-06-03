from __future__ import annotations

import json
import itertools
import time
from dataclasses import asdict, dataclass
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np
import pandas as pd
import torch
torch.backends.mkldnn.enabled = False
torch.set_num_threads(1)
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.model_selection import train_test_split
from torch import nn
from torch.nn.utils.rnn import pad_sequence, pack_padded_sequence
from torch.utils.data import DataLoader, Dataset

# ─────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────
ACTIONS = ["search", "view", "click", "add_to_cart", "wishlist", "coupon_view", "checkout", "purchase"]
PERSONAS = ["new_explorer", "category_browser", "deal_hunter", "loyal_member", "high_intent_buyer"]
NEXT_ACTIONS = ["recommend_entry_products", "push_coupon", "bundle_related_products", "upsell_membership", "reengage_catalog"]
ACTION_TO_ID = {name: idx + 1 for idx, name in enumerate(ACTIONS)}
PERSONA_TO_ID = {name: idx for idx, name in enumerate(PERSONAS)}
NBA_TO_ID = {name: idx for idx, name in enumerate(NEXT_ACTIONS)}
DEVICE = torch.device('cpu')

DATASETS = [
    ("dataset1_baseline",   "Dataset 1 — Baseline (Balanced)"),
    ("dataset2_flash_sale", "Dataset 2 — Flash Sale Season"),
    ("dataset3_cold_start", "Dataset 3 — Cold Start / New User Heavy"),
]

MODEL_NAMES = ["mlp", "rnn", "lstm", "bilstm"]

# Hyperparameter grid (3×3×3 = 27 configs)
HYPERPARAM_GRID = {
    "epochs":     [10, 30, 50],
    "batch_size": [32, 64, 128],
    "lr":         [0.001, 0.003, 0.01],
}


# ─────────────────────────────────────────────
# Dataset
# ─────────────────────────────────────────────
class BehaviorSequenceDataset(Dataset):
    def __init__(self, sequences: list[dict]):
        self.sequences = sequences

    def __len__(self) -> int:
        return len(self.sequences)

    def __getitem__(self, idx: int):
        row = self.sequences[idx]
        return (
            torch.tensor(row['sequence'], dtype=torch.long),
            len(row['sequence']),
            torch.tensor(row['persona_id'], dtype=torch.long),
            torch.tensor(row['nba_id'], dtype=torch.long),
        )


def collate_batch(batch):
    sequences, lengths, persona_ids, nba_ids = zip(*batch)
    padded = pad_sequence(sequences, batch_first=True, padding_value=0)
    return padded, torch.tensor(lengths, dtype=torch.long), torch.stack(persona_ids), torch.stack(nba_ids)


def build_sequences(csv_path: Path) -> list[dict]:
    df = pd.read_csv(csv_path).sort_values(['user_id', 'timestamp', 'step']).reset_index(drop=True)
    return [{
        'user_id': int(user_id),
        'sequence': [ACTION_TO_ID.get(action, 0) for action in group['action'].tolist()],
        'persona_id': PERSONA_TO_ID[group['persona_label'].iloc[-1]],
        'nba_id': NBA_TO_ID[group['next_best_action'].iloc[-1]],
    } for user_id, group in df.groupby('user_id')]


# ─────────────────────────────────────────────
# Models
# ─────────────────────────────────────────────
class MLPClassifier(nn.Module):
    """Baseline MLP: flatten sequence via mean pooling then classify."""
    def __init__(self, vocab_size: int, emb_dim: int = 24, hidden_dim: int = 32):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, emb_dim, padding_idx=0)
        self.net = nn.Sequential(
            nn.Linear(emb_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.2),
        )
        self.persona_head = nn.Linear(hidden_dim, len(PERSONAS))
        self.nba_head = nn.Linear(hidden_dim, len(NEXT_ACTIONS))

    def forward(self, sequences: torch.Tensor, lengths: torch.Tensor):
        embedded = self.embedding(sequences)          # (B, T, emb_dim)
        # Mean pooling over non-padding tokens
        mask = (sequences != 0).float().unsqueeze(-1) # (B, T, 1)
        pooled = (embedded * mask).sum(1) / mask.sum(1).clamp(min=1)  # (B, emb_dim)
        features = self.net(pooled)
        return self.persona_head(features), self.nba_head(features)


class SequenceClassifier(nn.Module):
    """RNN / LSTM / biLSTM classifier."""
    def __init__(self, cell_type: str, vocab_size: int, emb_dim: int = 24, hidden_dim: int = 32):
        super().__init__()
        self.cell_type = cell_type
        self.embedding = nn.Embedding(vocab_size, emb_dim, padding_idx=0)
        bidirectional = cell_type == 'bilstm'
        if cell_type == 'rnn':
            self.encoder = nn.RNN(emb_dim, hidden_dim, batch_first=True, nonlinearity='tanh')
        else:
            self.encoder = nn.LSTM(emb_dim, hidden_dim, batch_first=True, bidirectional=bidirectional)
        out_dim = hidden_dim * (2 if bidirectional else 1)
        self.dropout = nn.Dropout(0.2)
        self.persona_head = nn.Linear(out_dim, len(PERSONAS))
        self.nba_head = nn.Linear(out_dim, len(NEXT_ACTIONS))

    def forward(self, sequences: torch.Tensor, lengths: torch.Tensor):
        embedded = self.embedding(sequences)
        packed = pack_padded_sequence(embedded, lengths.cpu(), batch_first=True, enforce_sorted=False)
        _, hidden = self.encoder(packed)
        if isinstance(hidden, tuple):
            hidden = hidden[0]
        if self.cell_type == 'bilstm':
            features = torch.cat([hidden[-2], hidden[-1]], dim=1)
        else:
            features = hidden[-1]
        features = self.dropout(features)
        return self.persona_head(features), self.nba_head(features)


def build_model(model_name: str) -> nn.Module:
    vocab_size = len(ACTION_TO_ID) + 1
    if model_name == 'mlp':
        return MLPClassifier(vocab_size).to(DEVICE)
    return SequenceClassifier(model_name, vocab_size).to(DEVICE)


# ─────────────────────────────────────────────
# Training & Evaluation
# ─────────────────────────────────────────────
def evaluate(model: nn.Module, loader: DataLoader) -> dict:
    model.eval()
    loss_fn = nn.CrossEntropyLoss()
    losses, pt, pp, nt, npred = [], [], [], [], []
    with torch.no_grad():
        for sequences, lengths, persona_ids, nba_ids in loader:
            persona_logits, nba_logits = model(sequences, lengths)
            loss = loss_fn(persona_logits, persona_ids) + loss_fn(nba_logits, nba_ids)
            losses.append(loss.item())
            pp.extend(torch.argmax(persona_logits, dim=1).cpu().tolist())
            npred.extend(torch.argmax(nba_logits, dim=1).cpu().tolist())
            pt.extend(persona_ids.cpu().tolist())
            nt.extend(nba_ids.cpu().tolist())
    return {
        'loss': sum(losses) / max(1, len(losses)),
        'persona_true': pt, 'persona_pred': pp,
        'nba_true': nt, 'nba_pred': npred,
    }


def run_training(
    model_name: str,
    train_data: list[dict],
    valid_data: list[dict],
    epochs: int,
    batch_size: int,
    lr: float,
) -> dict:
    model = build_model(model_name)
    train_loader = DataLoader(BehaviorSequenceDataset(train_data), batch_size=batch_size, shuffle=True, collate_fn=collate_batch)
    valid_loader = DataLoader(BehaviorSequenceDataset(valid_data), batch_size=batch_size, shuffle=False, collate_fn=collate_batch)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    loss_fn = nn.CrossEntropyLoss()
    train_hist, valid_hist = [], []
    best_state, best_valid = None, float('inf')

    for _ in range(epochs):
        model.train()
        batch_losses = []
        for sequences, lengths, persona_ids, nba_ids in train_loader:
            optimizer.zero_grad()
            persona_logits, nba_logits = model(sequences, lengths)
            loss = loss_fn(persona_logits, persona_ids) + loss_fn(nba_logits, nba_ids)
            loss.backward()
            optimizer.step()
            batch_losses.append(loss.item())
        train_loss = sum(batch_losses) / max(1, len(batch_losses))
        valid = evaluate(model, valid_loader)
        train_hist.append(round(train_loss, 6))
        valid_hist.append(round(valid['loss'], 6))
        if valid['loss'] < best_valid:
            best_valid = valid['loss']
            best_state = {k: v.detach().cpu() for k, v in model.state_dict().items()}

    model.load_state_dict(best_state)
    valid = evaluate(model, valid_loader)
    persona_acc = accuracy_score(valid['persona_true'], valid['persona_pred'])
    persona_f1  = f1_score(valid['persona_true'], valid['persona_pred'], average='weighted', zero_division=0)
    nba_acc     = accuracy_score(valid['nba_true'], valid['nba_pred'])
    nba_f1      = f1_score(valid['nba_true'], valid['nba_pred'], average='weighted', zero_division=0)
    score = (persona_f1 + nba_f1) / 2

    return {
        'model': model,
        'persona_accuracy':    round(float(persona_acc), 4),
        'persona_f1':          round(float(persona_f1),  4),
        'next_action_accuracy':round(float(nba_acc),     4),
        'next_action_f1':      round(float(nba_f1),      4),
        'score':               round(float(score),        4),
        'train_loss_history':  train_hist,
        'valid_loss_history':  valid_hist,
        'persona_report':      classification_report(valid['persona_true'], valid['persona_pred'], target_names=PERSONAS, output_dict=True, zero_division=0),
        'next_action_report':  classification_report(valid['nba_true'], valid['nba_pred'], target_names=NEXT_ACTIONS, output_dict=True, zero_division=0),
        'persona_cm':          confusion_matrix(valid['persona_true'], valid['persona_pred'], labels=list(range(len(PERSONAS)))).tolist(),
        'nba_cm':              confusion_matrix(valid['nba_true'], valid['nba_pred'], labels=list(range(len(NEXT_ACTIONS)))).tolist(),
    }


# ─────────────────────────────────────────────
# Plotting helpers
# ─────────────────────────────────────────────
def plot_loss_curve(train_hist: list, valid_hist: list, model_name: str, ds_label: str, out_path: Path):
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(train_hist, label='Train Loss', marker='o', markersize=3)
    ax.plot(valid_hist, label='Valid Loss', marker='s', markersize=3)
    ax.set_xlabel('Epoch')
    ax.set_ylabel('Loss')
    ax.set_title(f'{model_name.upper()} — Loss Curve\n{ds_label}')
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def plot_model_comparison(results: list[dict], ds_label: str, out_path: Path):
    models = [r['model_name'] for r in results]
    persona_f1 = [r['best']['persona_f1'] for r in results]
    nba_f1     = [r['best']['next_action_f1'] for r in results]
    scores     = [r['best']['score'] for r in results]

    x = np.arange(len(models))
    width = 0.25
    fig, ax = plt.subplots(figsize=(9, 5))
    b1 = ax.bar(x - width, persona_f1, width, label='Persona F1')
    b2 = ax.bar(x,         nba_f1,     width, label='Next Action F1')
    b3 = ax.bar(x + width, scores,     width, label='Avg Score', color='gold')
    ax.set_xticks(x)
    ax.set_xticklabels([m.upper() for m in models])
    ax.set_ylim(0, 1.15)
    ax.set_ylabel('Score')
    ax.set_title(f'Model Comparison — {ds_label}')
    ax.legend()
    for bars in [b1, b2, b3]:
        for bar in bars:
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.02,
                    f'{bar.get_height():.3f}', ha='center', va='bottom', fontsize=8)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def plot_hyperparam_heatmap(tuning_rows: list[dict], model_name: str, ds_label: str, out_path: Path):
    """Plot score heatmap: lr (rows) × batch_size (cols), one subplot per epoch setting."""
    epochs_vals = sorted(set(r['epochs'] for r in tuning_rows))
    lr_vals     = sorted(set(r['lr'] for r in tuning_rows))
    bs_vals     = sorted(set(r['batch_size'] for r in tuning_rows))

    fig, axes = plt.subplots(1, len(epochs_vals), figsize=(5 * len(epochs_vals), 4), squeeze=False)
    for col, ep in enumerate(epochs_vals):
        ax = axes[0][col]
        matrix = np.zeros((len(lr_vals), len(bs_vals)))
        for r in tuning_rows:
            if r['epochs'] == ep:
                i = lr_vals.index(r['lr'])
                j = bs_vals.index(r['batch_size'])
                matrix[i][j] = r['score']
        im = ax.imshow(matrix, vmin=0, vmax=1, cmap='YlGn')
        ax.set_xticks(range(len(bs_vals)))
        ax.set_xticklabels([f'bs={b}' for b in bs_vals])
        ax.set_yticks(range(len(lr_vals)))
        ax.set_yticklabels([f'lr={l}' for l in lr_vals])
        ax.set_title(f'epochs={ep}')
        for i in range(len(lr_vals)):
            for j in range(len(bs_vals)):
                ax.text(j, i, f'{matrix[i][j]:.3f}', ha='center', va='center', fontsize=9)
        plt.colorbar(im, ax=ax)
    fig.suptitle(f'Hyperparam Tuning — {model_name.upper()} | {ds_label}', fontsize=11)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def plot_cross_dataset_comparison(cross_data: list[dict], out_path: Path):
    """Bar chart: each model's best score across 3 datasets."""
    ds_labels  = [d['ds_label'] for d in cross_data]
    model_names = MODEL_NAMES
    x = np.arange(len(ds_labels))
    width = 0.18
    colors = ['#4C72B0', '#DD8452', '#55A868', '#C44E52']

    fig, ax = plt.subplots(figsize=(11, 5))
    for i, model in enumerate(model_names):
        scores = [d['model_scores'].get(model, 0) for d in cross_data]
        offset = (i - 1.5) * width
        bars = ax.bar(x + offset, scores, width, label=model.upper(), color=colors[i])
        for bar in bars:
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.01,
                    f'{bar.get_height():.3f}', ha='center', va='bottom', fontsize=7.5)

    ax.set_xticks(x)
    ax.set_xticklabels(ds_labels, fontsize=9)
    ax.set_ylim(0, 1.15)
    ax.set_ylabel('Avg F1 Score')
    ax.set_title('Cross-Dataset Model Comparison')
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def plot_confusion_matrix(cm: list[list[int]], labels: list[str], title: str, out_path: Path):
    fig, ax = plt.subplots(figsize=(7, 5))
    cm_arr = np.array(cm)
    im = ax.imshow(cm_arr, cmap='Blues')
    ax.set_xticks(range(len(labels)))
    ax.set_yticks(range(len(labels)))
    ax.set_xticklabels([l.replace('_', '\n') for l in labels], fontsize=7)
    ax.set_yticklabels([l.replace('_', '\n') for l in labels], fontsize=7)
    ax.set_xlabel('Predicted')
    ax.set_ylabel('Actual')
    ax.set_title(title)
    for i in range(len(labels)):
        for j in range(len(labels)):
            ax.text(j, i, str(cm_arr[i, j]), ha='center', va='center', fontsize=8,
                    color='white' if cm_arr[i, j] > cm_arr.max() * 0.5 else 'black')
    plt.colorbar(im, ax=ax)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────
def main():
    data_dir    = Path(__file__).resolve().parent / 'data'
    reports_dir = Path(__file__).resolve().parent / 'reports'
    models_dir  = Path(__file__).resolve().parent / 'models'
    models_dir.mkdir(parents=True, exist_ok=True)

    # Build hyperparam configs
    keys   = list(HYPERPARAM_GRID.keys())
    values = list(HYPERPARAM_GRID.values())
    configs = [dict(zip(keys, combo)) for combo in itertools.product(*values)]

    cross_data       = []   # for cross-dataset chart
    full_report      = {}

    total_runs = len(DATASETS) * len(MODEL_NAMES) * len(configs)
    run_idx = 0
    t_global_start = time.time()

    for ds_key, ds_label in DATASETS:
        print(f'\n{"="*60}')
        print(f'  DATASET: {ds_label}')
        print(f'{"="*60}')

        csv_path = data_dir / f'{ds_key}.csv'
        if not csv_path.exists():
            print(f'  [SKIP] {csv_path} not found.')
            continue

        ds_reports_dir = reports_dir / ds_key
        ds_reports_dir.mkdir(parents=True, exist_ok=True)

        sequences = build_sequences(csv_path)
        train_data, valid_data = train_test_split(
            sequences, test_size=0.2, random_state=42,
            stratify=[x['persona_id'] for x in sequences],
        )

        ds_results    = []   # best result per model for this dataset
        model_scores  = {}   # model_name → best score

        for model_name in MODEL_NAMES:
            print(f'\n  ┌─ Model: {model_name.upper()}')
            tuning_rows  = []
            best_result  = None
            best_score   = -1.0
            best_cfg     = None
            best_model_obj = None

            for cfg in configs:
                run_idx += 1
                elapsed = time.time() - t_global_start
                print(f'  │  [{run_idx:>3}/{total_runs}] epochs={cfg["epochs"]} bs={cfg["batch_size"]} lr={cfg["lr"]}', end=' ... ', flush=True)
                t0 = time.time()
                result = run_training(model_name, train_data, valid_data, **cfg)
                dt = time.time() - t0
                print(f'score={result["score"]:.4f}  ({dt:.1f}s)')

                tuning_rows.append({
                    'epochs':     cfg['epochs'],
                    'batch_size': cfg['batch_size'],
                    'lr':         cfg['lr'],
                    'score':      result['score'],
                    'persona_f1': result['persona_f1'],
                    'next_action_f1': result['next_action_f1'],
                })

                if result['score'] > best_score:
                    best_score    = result['score']
                    best_result   = result
                    best_cfg      = cfg
                    best_model_obj = result['model']

            # Save best model
            torch.save({
                'state_dict': best_model_obj.state_dict(),
                'model_name': model_name,
                'config': best_cfg,
                'actions': ACTIONS, 'personas': PERSONAS, 'next_actions': NEXT_ACTIONS,
            }, models_dir / f'{ds_key}_{model_name}_best.pt')

            # Plot loss curve for best config
            plot_loss_curve(
                best_result['train_loss_history'], best_result['valid_loss_history'],
                model_name, ds_label,
                ds_reports_dir / f'{model_name}_loss_curve.png',
            )

            # Plot hyperparam heatmap
            plot_hyperparam_heatmap(
                tuning_rows, model_name, ds_label,
                ds_reports_dir / f'{model_name}_hyperparam_heatmap.png',
            )

            # Plot confusion matrices
            plot_confusion_matrix(
                best_result['persona_cm'], PERSONAS,
                f'{model_name.upper()} — Persona Confusion Matrix\n{ds_label}',
                ds_reports_dir / f'{model_name}_persona_cm.png',
            )
            plot_confusion_matrix(
                best_result['nba_cm'], NEXT_ACTIONS,
                f'{model_name.upper()} — Next Action Confusion Matrix\n{ds_label}',
                ds_reports_dir / f'{model_name}_nba_cm.png',
            )

            model_scores[model_name] = best_score
            ds_results.append({
                'model_name':    model_name,
                'best_config':   best_cfg,
                'best':          {k: v for k, v in best_result.items() if k != 'model'},
                'tuning_detail': tuning_rows,
            })
            print(f'  └─ Best: epochs={best_cfg["epochs"]} bs={best_cfg["batch_size"]} lr={best_cfg["lr"]} → score={best_score:.4f}')

        # Best model overall for this dataset
        best_ds_result = max(ds_results, key=lambda r: r['best']['score'])
        best_overall_model = next(
            r['best']['model'] if 'model' in r['best'] else build_model(r['model_name'])
            for r in ds_results if r['model_name'] == best_ds_result['model_name']
        )

        # Save best-overall model for this dataset
        best_pt = torch.load(models_dir / f'{ds_key}_{best_ds_result["model_name"]}_best.pt', map_location='cpu')
        torch.save({**best_pt, 'dataset': ds_key}, models_dir / f'{ds_key}_model_best.pt')

        # Plot model comparison chart
        plot_model_comparison(ds_results, ds_label, ds_reports_dir / 'model_comparison.png')

        cross_data.append({'ds_label': ds_label[:20], 'model_scores': model_scores})
        full_report[ds_key] = {
            'dataset_label': ds_label,
            'train_size':    len(train_data),
            'valid_size':    len(valid_data),
            'best_model':    best_ds_result['model_name'],
            'results':       ds_results,
        }

        print(f'\n  ✓ Best model for {ds_label}: {best_ds_result["model_name"].upper()} (score={best_ds_result["best"]["score"]:.4f})')

    # Cross-dataset comparison chart
    if cross_data:
        plot_cross_dataset_comparison(cross_data, reports_dir / 'cross_dataset_comparison.png')

    # Save full JSON report
    (reports_dir / 'full_report.json').write_text(
        json.dumps(full_report, ensure_ascii=False, indent=2), encoding='utf-8'
    )

    total_time = time.time() - t_global_start
    print(f'\n{"="*60}')
    print(f'  TRAINING COMPLETE — {total_time/60:.1f} min')
    print(f'  Reports saved to: {reports_dir}')
    print(f'{"="*60}')


if __name__ == '__main__':
    main()