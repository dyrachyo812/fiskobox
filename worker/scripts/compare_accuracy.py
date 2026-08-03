import argparse
import sys
import time
from datetime import date
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "worker" / "src"), str(ROOT / "shared" / "src")]

from worker.pipeline.parsing.receipt import (  # noqa: E402
    parse_receipt_hybrid,
    parse_receipt_llm,
    parse_receipt_regex,
)

FIXTURES_DIR = ROOT / "tests" / "fixtures" / "receipts"
TODAY = date(2026, 8, 2)

EXPECTED = {
    "autocafeCafe.txt": {
        "label": "Автокафе",
        "merchant_aliases": ["автокафе", "autocafe"],
        "amount": Decimal("785.00"),
        "purchase_date": date(2025, 7, 29),
    },
    "dnsAcquiring.txt": {
        "label": "DNS",
        "merchant_aliases": ["dns"],
        "amount": Decimal("4199.00"),
        "purchase_date": date(2023, 5, 2),
    },
    "ukraineSuma.txt": {
        "label": "Украина/McDonald's",
        "merchant_aliases": ["mcdonald", "макдоналд", "макдональдз"],
        "amount": Decimal("274.00"),
        "purchase_date": date(2025, 3, 15),
    },
    "diorLuxury.txt": {
        "label": "Dior",
        "merchant_aliases": ["dior"],
        "amount": Decimal("225900.00"),
        "purchase_date": date(2025, 6, 10),
    },
}


def normalize_merchant(value: str | None) -> str:
    if not value:
        return ""
    return (
        value.lower()
        .replace("ё", "е")
        .replace('"', "")
        .replace("«", "")
        .replace("»", "")
        .strip()
    )


def merchant_ok(actual: str | None, aliases: list[str]) -> bool:
    haystack = normalize_merchant(actual)
    if not haystack:
        return False
    return any(alias in haystack for alias in aliases)


def field_score(expected: dict, parsed: dict) -> dict[str, bool]:
    amount = parsed.get("amount")
    if isinstance(amount, Decimal):
        amount_match = amount == expected["amount"]
    elif amount is None:
        amount_match = False
    else:
        amount_match = Decimal(str(amount)) == expected["amount"]

    return {
        "merchant": merchant_ok(parsed.get("merchant_name"), expected["merchant_aliases"]),
        "amount": amount_match,
        "date": parsed.get("purchase_date") == expected["purchase_date"],
    }


def fmt(value) -> str:
    if value is None:
        return "—"
    return str(value)


def run_mode(mode: str, text: str) -> tuple[dict, float]:
    started = time.perf_counter()
    if mode == "regex":
        parsed = parse_receipt_regex(text, [])
    elif mode == "llm":
        parsed = parse_receipt_llm(text, [])
    elif mode == "hybrid":
        parsed = parse_receipt_hybrid(text, [])
    else:
        raise ValueError(mode)
    elapsed = time.perf_counter() - started
    parsed["_elapsed_seconds"] = elapsed
    return parsed, elapsed


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare regex vs Ollama LLM accuracy")
    parser.add_argument(
        "--modes",
        default="regex,llm,hybrid",
        help="comma-separated: regex,llm,hybrid",
    )
    args = parser.parse_args()
    modes = [item.strip() for item in args.modes.split(",") if item.strip()]

    rows = []
    totals = {mode: {"merchant": 0, "amount": 0, "date": 0, "all": 0} for mode in modes}
    timings = {mode: [] for mode in modes}

    print(f"Fixtures: {FIXTURES_DIR}")
    print(f"Modes: {', '.join(modes)}")
    print()

    for filename, expected in EXPECTED.items():
        text = (FIXTURES_DIR / filename).read_text(encoding="utf-8")
        print(f"=== {expected['label']} ({filename}) ===")
        for mode in modes:
            parsed, elapsed = run_mode(mode, text)
            scores = field_score(expected, parsed)
            timings[mode].append(elapsed)
            for key, ok in scores.items():
                totals[mode][key] += int(ok)
            totals[mode]["all"] += int(all(scores.values()))

            mark = {True: "OK", False: "MISS"}
            print(
                f"  [{mode}] "
                f"merchant={mark[scores['merchant']]}({fmt(parsed.get('merchant_name'))}) "
                f"amount={mark[scores['amount']]}({fmt(parsed.get('amount'))}) "
                f"date={mark[scores['date']]}({fmt(parsed.get('purchase_date'))}) "
                f"review={parsed.get('needs_manual_review')} "
                f"time={elapsed:.2f}s"
            )
            rows.append((expected["label"], mode, scores, parsed, elapsed))
        print()

    fixture_count = len(EXPECTED)
    print("=== SUMMARY ===")
    print(
        f"{'mode':<8} {'merchant':>10} {'amount':>10} {'date':>10} "
        f"{'all3':>8} {'avg_time':>10}"
    )
    for mode in modes:
        avg = sum(timings[mode]) / len(timings[mode]) if timings[mode] else 0
        print(
            f"{mode:<8} "
            f"{totals[mode]['merchant']}/{fixture_count:>2}{'':>5} "
            f"{totals[mode]['amount']}/{fixture_count:>2}{'':>5} "
            f"{totals[mode]['date']}/{fixture_count:>2}{'':>5} "
            f"{totals[mode]['all']}/{fixture_count:>2}{'':>3} "
            f"{avg:>8.2f}s"
        )

    if timings.get("llm"):
        max_llm = max(timings["llm"])
        avg_llm = sum(timings["llm"]) / len(timings["llm"])
        print()
        print(
            f"Ollama timing on this machine: avg={avg_llm:.2f}s, "
            f"max={max_llm:.2f}s (per receipt, model warm/cold varies)"
        )
        print(
            f"Bot UX suggestion: warn users up to ~{max(30, int(max_llm) + 10)}s "
            f"when PARSER_MODE=llm|hybrid"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
