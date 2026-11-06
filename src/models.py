"""Stage 1 detector zoo: every standalone (non-hybrid) deep model the IDS literature uses.

All supervised models map a cleaned per-packet / per-flow feature vector x (B, F) to 2 logits.
The public datasets have no usable per-device time order (stage 0 audit), so the sequence models
read the F features as a length-F sequence -- the usual convention in tabular IDS papers; true
time windows per device come with the emulated testbed (stage 4). The Transformer uses a feature
tokenizer (one learned embedding per feature, scaled by its value, plus a [CLS] token), the
standard way to apply attention to tabular rows.

The autoencoder is trained on benign rows only and flags rows whose reconstruction error exceeds
a threshold set on the validation split (unsupervised; can catch attack types never seen).
"""
from __future__ import annotations

import torch
import torch.nn as nn

SUPERVISED = ["mlp", "cnn", "lstm", "gru", "bilstm", "tcn", "transformer"]
MODEL_NAMES = SUPERVISED + ["autoencoder"]


class MLP(nn.Module):
    def __init__(self, f: int):
        super().__init__()
        self.net = nn.Sequential(nn.Linear(f, 128), nn.ReLU(), nn.Dropout(0.1),
                                 nn.Linear(128, 64), nn.ReLU(), nn.Linear(64, 2))

    def forward(self, x):
        return self.net(x)


class CNN1D(nn.Module):
    def __init__(self, f: int):
        super().__init__()
        self.net = nn.Sequential(nn.Conv1d(1, 32, 3, padding=1), nn.ReLU(),
                                 nn.Conv1d(32, 64, 3, padding=1), nn.ReLU(),
                                 nn.AdaptiveMaxPool1d(1))
        self.fc = nn.Linear(64, 2)

    def forward(self, x):
        return self.fc(self.net(x.unsqueeze(1)).squeeze(-1))


class Recurrent(nn.Module):
    """LSTM / GRU / BiLSTM over the feature sequence; the last hidden state(s) feed the head."""

    def __init__(self, f: int, cell: str, hidden: int = 64):
        super().__init__()
        bidir = cell == "bilstm"
        rnn = nn.GRU if cell == "gru" else nn.LSTM
        self.rnn = rnn(1, hidden, batch_first=True, bidirectional=bidir)
        self.fc = nn.Linear(hidden * (2 if bidir else 1), 2)

    def forward(self, x):
        _, h = self.rnn(x.unsqueeze(-1))
        h = h[0] if isinstance(h, tuple) else h  # LSTM returns (h, c)
        return self.fc(torch.cat(list(h), dim=1))


class TCNBlock(nn.Module):
    def __init__(self, c_in: int, c_out: int, dilation: int, k: int = 3):
        super().__init__()
        pad = (k - 1) * dilation
        self.conv1 = nn.Conv1d(c_in, c_out, k, padding=pad, dilation=dilation)
        self.conv2 = nn.Conv1d(c_out, c_out, k, padding=pad, dilation=dilation)
        self.skip = nn.Conv1d(c_in, c_out, 1) if c_in != c_out else nn.Identity()
        self.crop = pad

    def forward(self, x):
        y = torch.relu(self.conv1(x)[..., : -self.crop])  # causal: drop the right padding
        y = torch.relu(self.conv2(y)[..., : -self.crop])
        return torch.relu(y + self.skip(x))


class TCN(nn.Module):
    def __init__(self, f: int, channels: int = 32):
        super().__init__()
        self.blocks = nn.Sequential(TCNBlock(1, channels, 1), TCNBlock(channels, channels, 2),
                                    TCNBlock(channels, channels, 4))
        self.fc = nn.Linear(channels, 2)

    def forward(self, x):
        return self.fc(self.blocks(x.unsqueeze(1)).mean(dim=-1))


class TabTransformer(nn.Module):
    def __init__(self, f: int, d: int = 32, layers: int = 2, heads: int = 4):
        super().__init__()
        self.weight = nn.Parameter(torch.randn(f, d) * 0.02)
        self.bias = nn.Parameter(torch.zeros(f, d))
        self.cls = nn.Parameter(torch.zeros(1, 1, d))
        layer = nn.TransformerEncoderLayer(d, heads, dim_feedforward=2 * d, dropout=0.1,
                                           batch_first=True, norm_first=True)
        self.encoder = nn.TransformerEncoder(layer, layers, enable_nested_tensor=False)
        self.norm = nn.LayerNorm(d)
        self.fc = nn.Linear(d, 2)

    def forward(self, x):
        tokens = x.unsqueeze(-1) * self.weight + self.bias            # (B, F, d)
        tokens = torch.cat([self.cls.expand(len(x), -1, -1), tokens], dim=1)
        return self.fc(self.norm(self.encoder(tokens)[:, 0]))


class Autoencoder(nn.Module):
    def __init__(self, f: int, bottleneck: int = 16):
        super().__init__()
        self.encoder = nn.Sequential(nn.Linear(f, 64), nn.ReLU(), nn.Linear(64, bottleneck), nn.ReLU())
        self.decoder = nn.Sequential(nn.Linear(bottleneck, 64), nn.ReLU(), nn.Linear(64, f))

    def forward(self, x):
        return self.decoder(self.encoder(x))

    def score(self, x):
        """Per-row reconstruction error (higher = more anomalous)."""
        return ((self.forward(x) - x) ** 2).mean(dim=1)


def build_model(name: str, f: int) -> nn.Module:
    if name == "mlp":
        return MLP(f)
    if name == "cnn":
        return CNN1D(f)
    if name in ("lstm", "gru", "bilstm"):
        return Recurrent(f, name)
    if name == "tcn":
        return TCN(f)
    if name == "transformer":
        return TabTransformer(f)
    if name == "autoencoder":
        return Autoencoder(f)
    raise ValueError(f"unknown model {name!r}; choose from {MODEL_NAMES}")


def n_params(model: nn.Module) -> int:
    return sum(p.numel() for p in model.parameters() if p.requires_grad)
