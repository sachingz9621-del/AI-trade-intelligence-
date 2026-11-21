"""V10 educational ML direction model and chronological backtest.

Uses only past/current OHLCV features to predict the next candle direction.
The final candle is excluded because its forward return is unknown.
A chronological holdout is used; scaling is fitted on training data only.
"""
from __future__ import annotations
import numpy as np
import pandas as pd

FEATURES = [
    "ret_1", "ret_3", "ret_5", "range_pct", "ema20_gap", "ema50_gap",
    "ema20_50", "rsi_scaled", "volatility_20", "volume_ratio",
    "macd_pct", "atr_pct",
]


def build_dataset(ohlcv: pd.DataFrame, neutral_band: float = 0.0):
    required = {"Open", "High", "Low", "Close", "Volume"}
    if not required.issubset(ohlcv.columns):
        raise ValueError(f"OHLCV data must contain: {', '.join(sorted(required))}")
    d = ohlcv.copy().sort_index()
    for c in required:
        d[c] = pd.to_numeric(d[c], errors="coerce")
    close = d["Close"].replace(0, np.nan)
    ema20 = close.ewm(span=20, adjust=False).mean()
    ema50 = close.ewm(span=50, adjust=False).mean()
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    delta = close.diff()
    gain = delta.clip(lower=0).ewm(alpha=1/14, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1/14, adjust=False).mean()
    rs = gain / loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    true_range = pd.concat([
        d["High"] - d["Low"],
        (d["High"] - close.shift()).abs(),
        (d["Low"] - close.shift()).abs(),
    ], axis=1).max(axis=1)
    atr = true_range.ewm(alpha=1/14, adjust=False).mean()
    vol_avg = d["Volume"].rolling(20, min_periods=10).mean()

    x = pd.DataFrame(index=d.index)
    x["ret_1"] = close.pct_change(1)
    x["ret_3"] = close.pct_change(3)
    x["ret_5"] = close.pct_change(5)
    x["range_pct"] = (d["High"] - d["Low"]) / close
    x["ema20_gap"] = close / ema20 - 1
    x["ema50_gap"] = close / ema50 - 1
    x["ema20_50"] = ema20 / ema50 - 1
    x["rsi_scaled"] = (rsi - 50) / 50
    x["volatility_20"] = x["ret_1"].rolling(20, min_periods=10).std()
    x["volume_ratio"] = (d["Volume"] / vol_avg.replace(0, np.nan)).clip(0, 10)
    x["macd_pct"] = (ema12 - ema26) / close
    x["atr_pct"] = atr / close
    forward_return = close.shift(-1) / close - 1
    y = (forward_return > float(neutral_band)).astype(float).rename("target_up")
    frame = x.replace([np.inf, -np.inf], np.nan).join(y).join(forward_return.rename("forward_return"))
    frame = frame.dropna(subset=FEATURES + ["forward_return"])
    return frame[FEATURES], frame["target_up"].astype(int), frame["forward_return"]


def _sigmoid(z):
    z = np.clip(z, -35, 35)
    return 1.0 / (1.0 + np.exp(-z))


def _fit_logistic(x: np.ndarray, y: np.ndarray, epochs: int = 1800, learning_rate: float = 0.08, l2: float = 0.01):
    # Deterministic batch gradient descent; intercept is not regularized.
    weights = np.zeros(x.shape[1], dtype=float)
    bias = 0.0
    n = max(len(y), 1)
    for _ in range(epochs):
        p = _sigmoid(x @ weights + bias)
        error = p - y
        weights -= learning_rate * ((x.T @ error) / n + l2 * weights)
        bias -= learning_rate * float(error.mean())
    return weights, bias


def run_ml_backtest(ohlcv: pd.DataFrame, train_fraction: float = 0.70,
                    long_threshold: float = 0.55, short_threshold: float = 0.45,
                    allow_short: bool = False, cost_bps: float = 10.0,
                    neutral_band: float = 0.0):
    """Return metrics, test predictions and equity curve for a strict time split."""
    if not 0.60 <= train_fraction <= 0.85:
        raise ValueError("Training fraction must be between 0.60 and 0.85")
    if not 0.50 < long_threshold < 1 or not 0 < short_threshold < 0.50:
        raise ValueError("Use a long threshold > 0.50 and short threshold < 0.50")
    if cost_bps < 0:
        raise ValueError("Trading cost cannot be negative")
    X, y, fwd = build_dataset(ohlcv, neutral_band=neutral_band)
    if len(X) < 160:
        raise ValueError(f"Need at least 160 usable candles; only {len(X)} available")
    split = int(len(X) * train_fraction)
    if split < 100 or len(X) - split < 30:
        raise ValueError("Not enough observations in train/test partitions")
    x_train, x_test = X.iloc[:split], X.iloc[split:]
    y_train, y_test = y.iloc[:split], y.iloc[split:]
    # Fit standardization only on training observations.
    means = x_train.mean()
    scales = x_train.std().replace(0, 1).fillna(1)
    a = ((x_train - means) / scales).to_numpy(dtype=float)
    b = ((x_test - means) / scales).to_numpy(dtype=float)
    weights, bias = _fit_logistic(a, y_train.to_numpy(dtype=float))
    probabilities = _sigmoid(b @ weights + bias)
    predicted = (probabilities >= 0.5).astype(int)

    positions = np.where(probabilities >= long_threshold, 1.0, 0.0)
    if allow_short:
        positions = np.where(probabilities <= short_threshold, -1.0, positions)
    raw_returns = fwd.iloc[split:].to_numpy(dtype=float)
    # Charge costs on each change in exposure; opening/closing a position each incurs cost.
    turnover = np.abs(np.diff(np.r_[0.0, positions]))
    net_returns = positions * raw_returns - turnover * (cost_bps / 10000.0)
    equity = np.cumprod(1.0 + net_returns)
    buy_hold = np.cumprod(1.0 + raw_returns)
    active = positions != 0
    wins = int(((net_returns > 0) & active).sum())
    trades = int(active.sum())
    total_return = float(equity[-1] - 1) if len(equity) else 0.0
    bh_return = float(buy_hold[-1] - 1) if len(buy_hold) else 0.0
    daily_std = float(np.std(net_returns, ddof=1)) if len(net_returns) > 1 else 0.0
    sharpe = float(np.mean(net_returns) / daily_std * np.sqrt(252)) if daily_std > 0 else 0.0
    peak = np.maximum.accumulate(equity)
    drawdown = equity / peak - 1
    accuracy = float((predicted == y_test.to_numpy()).mean())
    precision = float(((predicted == 1) & (y_test.to_numpy() == 1)).sum() / max((predicted == 1).sum(), 1))

    out = pd.DataFrame({
        "Actual next direction": np.where(y_test.to_numpy() == 1, "Up", "Down"),
        "Model probability Up": probabilities,
        "Signal": np.where(positions > 0, "LONG", np.where(positions < 0, "SHORT", "FLAT")),
        "Next candle return %": raw_returns * 100,
        "Strategy return %": net_returns * 100,
        "Equity": equity,
    }, index=x_test.index)
    metrics = {
        "samples": int(len(X)), "train_samples": int(split), "test_samples": int(len(x_test)),
        "accuracy": accuracy, "precision_up": precision, "strategy_return": total_return,
        "buy_hold_return": bh_return, "max_drawdown": float(drawdown.min()),
        "sharpe_annualized_approx": sharpe, "trades": trades,
        "win_rate_active": float(wins / trades) if trades else 0.0,
        "exposure": float(active.mean()), "cost_bps": float(cost_bps),
        "allow_short": bool(allow_short), "last_probability_up": float(probabilities[-1]),
    }
    return metrics, out
