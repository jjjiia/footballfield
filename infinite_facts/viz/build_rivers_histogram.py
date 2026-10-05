"""Build the binned data payload for rivers.html (log-scale histogram of river length)."""
import json
import math

NBINS = 40


def main():
    raw = json.load(open("rivers_data.json"))
    kms = [it["km"] for it in raw]
    lo, hi = min(kms), max(kms)
    log_lo, log_hi = math.log10(lo), math.log10(hi)

    edges = [10 ** (log_lo + (log_hi - log_lo) * i / NBINS) for i in range(NBINS + 1)]
    counts = [0] * NBINS
    for k in kms:
        idx = min(NBINS - 1, int((math.log10(k) - log_lo) / (log_hi - log_lo) * NBINS))
        counts[idx] += 1

    bins = [
        {"lo": round(edges[i], 4), "hi": round(edges[i + 1], 4), "count": counts[i]}
        for i in range(NBINS)
    ]

    payload = {
        "bins": bins,
        "min_km": lo,
        "max_km": hi,
        "total": len(kms),
    }

    with open("rivers_hist_data.json", "w") as f:
        json.dump(payload, f)
    print("wrote rivers_hist_data.json:", len(bins), "bins, total", len(kms), "rivers")


if __name__ == "__main__":
    main()
