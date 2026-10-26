"""AIサプライチェーンの層と代表銘柄 (V1)。

重要: AI_BASKET_V1 と同じく、後から都合よく銘柄を入れ替えないこと。
構成を変える時は LAYERS_V2 を新設し、history も別キーにする。
"""
from __future__ import annotations

LAYERS_VERSION = "v1"

# key -> (表示名, 銘柄)。並びは図の上流→下流
LAYERS_V1: dict[str, tuple[str, list[str]]] = {
    "demand": ("AI需要", ["MSFT", "AMZN", "GOOGL", "META", "ORCL"]),
    "gpu": ("GPU・AI半導体", ["NVDA", "AMD", "AVGO", "MRVL"]),
    "memory": ("メモリ(HBM)", ["MU", "000660.KS", "005930.KS", "285A.T"]),
    "fab": ("製造・パッケージ", ["TSM", "ASML", "AMAT", "LRCX", "AMKR"]),
    "optics": ("光・ネットワーク", ["ANET", "COHR", "LITE", "CRDO"]),
    "dc": ("データセンター", ["CRWV", "NBIS", "DLR", "EQIX", "APLD"]),
    "grid": ("電力・冷却設備", ["VRT", "ETN", "GEV", "PWR"]),
    "power": ("発電", ["CEG", "VST", "NRG", "TLN"]),
}

# 逃げ場 (AIから資金が逃げる時の行き先候補)
HAVENS_V1: dict[str, tuple[str, str]] = {
    "cash": ("現金(短期米国債)", "SGOV"),
    "gold": ("金", "GLD"),
    "bond": ("長期米国債", "TLT"),
    "util": ("公益株", "XLU"),
    "staples": ("生活必需品株", "XLP"),
}

# 比較用: AI全体の代わりに使う指数
AI_REFERENCE = "SMH"
