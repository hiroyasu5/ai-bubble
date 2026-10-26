"""詰まり度と逃げ場の計算 (純粋関数のみ。取得は main.py)。

詰まり度 (0-100): 供給が詰まった層は値上げ力を持ち、株価がAI全体より強くなる、
という前提の近似。次の2つの平均:
  - 相対強さ: 層の63営業日リターン中央値の、全層の中での順位 (0-100)
  - トレンド: 層の銘柄のうち50日線を上回る割合 (0-100)
株価だけで測っているので「市場がどこを詰まりと見ているか」であって、
リードタイムや価格などの実需データではない。
"""
from __future__ import annotations

from statistics import median

Series = list[tuple[str, float]]


def ret(series: Series, days: int) -> float | None:
    """days営業日前からのリターン(%)"""
    if len(series) <= days:
        return None
    old, new = series[-days - 1][1], series[-1][1]
    return (new / old - 1) * 100 if old else None


def above_ma(series: Series, days: int = 50) -> bool | None:
    if len(series) < days:
        return None
    closes = [c for _, c in series[-days:]]
    return series[-1][1] > sum(closes) / days


def _rank_pct(values: dict[str, float]) -> dict[str, float]:
    """値の順位を0(最下位)〜100(最上位)に"""
    keys = sorted(values, key=values.get)
    n = len(keys)
    if n == 1:
        return {keys[0]: 50.0}
    return {k: i / (n - 1) * 100 for i, k in enumerate(keys)}


def score_layers(
    layers: dict[str, tuple[str, list[str]]], prices: dict[str, Series]
) -> list[dict]:
    rows: dict[str, dict] = {}
    for key, (name, tickers) in layers.items():
        stocks = []
        for t in tickers:
            s = prices.get(t)
            if not s:
                continue
            stocks.append({
                "ticker": t,
                "r1m": ret(s, 21),
                "r3m": ret(s, 63),
                "above50": above_ma(s, 50),
            })
        r3 = [x["r3m"] for x in stocks if x["r3m"] is not None]
        ab = [x["above50"] for x in stocks if x["above50"] is not None]
        rows[key] = {
            "key": key,
            "name": name,
            "stocks": stocks,
            "coverage": f"{len(stocks)}/{len(tickers)}",
            "r3m": median(r3) if r3 else None,
            "r1m": median([x["r1m"] for x in stocks if x["r1m"] is not None] or [0]),
            "trend": sum(ab) / len(ab) * 100 if ab else None,
        }
    ranked = _rank_pct({k: r["r3m"] for k, r in rows.items() if r["r3m"] is not None})
    for k, r in rows.items():
        parts = [p for p in (ranked.get(k), r["trend"]) if p is not None]
        r["tightness"] = round(sum(parts) / len(parts)) if parts else None
    return list(rows.values())


def score_havens(
    havens: dict[str, tuple[str, str]], prices: dict[str, Series], ai_ref: Series | None
) -> dict:
    ai1 = ret(ai_ref, 21) if ai_ref else None
    out = []
    for key, (name, ticker) in havens.items():
        s = prices.get(ticker)
        r1 = ret(s, 21) if s else None
        out.append({
            "key": key, "name": name, "ticker": ticker,
            "r1m": r1,
            # AIより強いか: AI(SMH)の1か月リターンとの差
            "vs_ai": (r1 - ai1) if (r1 is not None and ai1 is not None) else None,
        })
    return {"ai_r1m": ai1, "havens": out}


# AIBubble の判定 → 逃げる度 (0:まだ 1:出口確認 2:荷造り 3:逃げる)
_LEVEL_RANK = {"green": 0, "yellow": 1, "orange": 2, "red": 3}


def escape_level(ai_history: dict) -> dict:
    composite = ai_history.get("composite_level", "")
    market = ai_history.get("market_level", "")
    stage = int(ai_history.get("stage") or 0)
    lv = _LEVEL_RANK.get(composite, 0)
    # 先行警報(market)は単独ではEXITに使わない設計なので、1段階だけ前倒しに効かせる
    if _LEVEL_RANK.get(market, 0) >= 2:
        lv = max(lv, 1)
    if stage >= 5:
        lv = max(lv, 3)
    elif stage >= 4:
        lv = max(lv, 2)
    return {
        "level": lv,
        "stage": stage,
        "composite": composite,
        "market": market,
        "updated": ai_history.get("last_updated", ""),
    }
