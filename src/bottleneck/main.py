"""株ボトルネック地図 - エントリーポイント。

AI Bubble Dashboard の後に GitHub Actions から1日1回実行される:
1. 層ごとの代表銘柄・逃げ場ETFの終値を Yahoo から取得
2. 詰まり度・逃げ場の強さを計算
3. AIBubble の history.json から「逃げる度」を読む
4. docs/bottleneck/data.json (図が読む) と data/bottleneck/history.json を保存
"""
from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from ..ai_dashboard.config import HISTORY_FILE as AI_HISTORY_FILE
from ..ai_dashboard.fetchers import yahoo
from .compute import escape_level, score_havens, score_layers
from .layers import AI_REFERENCE, HAVENS_V1, LAYERS_V1, LAYERS_VERSION

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

JST = timezone(timedelta(hours=9))
ROOT = Path(__file__).resolve().parent.parent.parent
HISTORY_FILE = ROOT / "data" / "bottleneck" / "history.json"
DATA_FILE = ROOT / "docs" / "bottleneck" / "data.json"
HISTORY_DAYS_IN_PAGE = 60


def _load(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def _backfill(history: dict, prices: dict, today: str) -> None:
    """履歴が無い過去の営業日を、その日までの株価で計算し直して埋める (逃げる度は不明)"""
    ref = prices.get(AI_REFERENCE) or next(iter(prices.values()))
    for date, _ in ref[-HISTORY_DAYS_IN_PAGE:]:
        if date >= today or date in history["daily"]:
            continue
        cut = {t: [x for x in s if x[0] <= date] for t, s in prices.items()}
        history["daily"][date] = {
            "layers": {r["key"]: r["tightness"] for r in score_layers(LAYERS_V1, cut)},
            "escape": None,
        }


def run() -> None:
    today = datetime.now(JST).date().isoformat()
    tickers = [t for _, ts in LAYERS_V1.values() for t in ts]
    tickers += [t for _, t in HAVENS_V1.values()] + [AI_REFERENCE]
    prices = yahoo.fetch_basket_prices(tickers)
    if len(prices) < len(tickers) * 0.5:
        logger.error("株価の取得が半分未満 (%d/%d)。更新しない", len(prices), len(tickers))
        sys.exit(1)

    layers = score_layers(LAYERS_V1, prices)
    havens = score_havens(HAVENS_V1, prices, prices.get(AI_REFERENCE))
    escape = escape_level(_load(AI_HISTORY_FILE, {}))

    history = _load(HISTORY_FILE, {"version": LAYERS_VERSION, "daily": {}})
    _backfill(history, prices, today)
    history["daily"][today] = {
        "layers": {r["key"]: r["tightness"] for r in layers},
        "escape": escape["level"],
    }
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    HISTORY_FILE.write_text(
        json.dumps(history, ensure_ascii=False, indent=1, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    recent = sorted(history["daily"])[-HISTORY_DAYS_IN_PAGE:]
    data = {
        "date": today,
        "version": LAYERS_VERSION,
        "layers": layers,
        "havens": havens,
        "escape": escape,
        "history": [{"date": d, **history["daily"][d]} for d in recent],
    }
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(json.dumps(data, ensure_ascii=False) + "\n", encoding="utf-8")
    top = max((r for r in layers if r["tightness"] is not None), key=lambda r: r["tightness"])
    logger.info("保存: 一番詰まっている層=%s (%s) / 逃げる度=%d",
                top["name"], top["tightness"], escape["level"])
