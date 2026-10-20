from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


SAMPLE_COL = "Sample Number (10000 samples per second)"
TIMESTAMP_COL = "UNIX Timestamp (Milliseconds since 1970-01-01)"

SENSOR_COLS = [
    "thumb (g)", "index (g)", "middle (g)", "ring (g)", "pinky (g)",
    "roll (deg)", "pitch (deg)", "yaw (deg)",
    "magX (uT)", "magY (uT)", "magZ (uT)",
    "accelX (g)", "accelY (g)", "accelZ (g)",
    "gyroX (deg/s)", "gyroY (deg/s)", "gyroZ (deg/s)",
]
FINGER_COLS = ["thumb (g)", "index (g)", "middle (g)", "ring (g)", "pinky (g)"]


def process_file(input_path: Path, output_root: Path) -> dict:
    df = pd.read_csv(input_path)
    run_name = input_path.stem.replace(" ", "_")
    out_dir = output_root / run_name
    out_dir.mkdir(parents=True, exist_ok=True)

    required = [SAMPLE_COL, TIMESTAMP_COL, *SENSOR_COLS]
    missing_columns = [col for col in required if col not in df.columns]
    if missing_columns:
        raise ValueError(
            "CSV is missing expected columns: " + ", ".join(missing_columns)
        )

    # The original CSV is never edited to preserve raw input so as to not lose any information while reviewing the data. All processing is done on a copy of the original data.
    data = df.copy()
    for col in required:
        data[col] = pd.to_numeric(data[col], errors="coerce")

    flags = pd.DataFrame(index=data.index)
    flags["missing_or_non_numeric_values"] = data[required].isna().any(axis=1)
    flags["duplicate_sample_number"] = data[SAMPLE_COL].duplicated(keep=False)
    flags["duplicate_timestamp"] = data[TIMESTAMP_COL].duplicated(keep=False)
    flags["timestamp_not_increasing"] = data[TIMESTAMP_COL].diff().lt(0).fillna(False)

    positive_diffs = data[TIMESTAMP_COL].diff()
    positive_diffs = positive_diffs[positive_diffs > 0]
    median_interval_ms = float(positive_diffs.median()) if not positive_diffs.empty else None
    if median_interval_ms and median_interval_ms > 0:
        flags["large_timestamp_gap"] = positive_diffs.reindex(data.index).gt(
            median_interval_ms * 3
        ).fillna(False)
    else:
        flags["large_timestamp_gap"] = False

    #constant value smay also mean inactivity of sensor or finger. It is a review flag
    constant_channels = [
        col for col in SENSOR_COLS
        if data[col].nunique(dropna=True) <= 1
    ]

    data["timestamp_readable"] = pd.to_datetime(
        data[TIMESTAMP_COL], unit="ms", origin="unix", errors="coerce", utc=True
    )
    data["quality_flagged"] = flags.any(axis=1)
    data["quality_issues"] = flags.apply(
        lambda row: ";".join(row.index[row].tolist()), axis=1
    )
    data.to_csv(out_dir / "curated_sensor_data.csv", index=False)
    flagged = data.loc[data["quality_flagged"]].copy()
    flagged.to_csv(out_dir / "flagged_rows.csv", index=False)

    duration_seconds = None
    valid_ts = data[TIMESTAMP_COL].dropna()
    if len(valid_ts) >= 2:
        duration_seconds = round((valid_ts.max() - valid_ts.min()) / 1000, 3)

    observed_rate_hz = None
    if median_interval_ms and median_interval_ms > 0:
        observed_rate_hz = round(1000 / median_interval_ms, 2)

    report = {
        "source_file": input_path.name,
        "rows": int(len(data)),
        "columns": int(len(df.columns)),
        "missing_or_non_numeric_rows": int(flags["missing_or_non_numeric_values"].sum()),
        "duplicate_sample_number_rows": int(flags["duplicate_sample_number"].sum()),
        "duplicate_timestamp_rows": int(flags["duplicate_timestamp"].sum()),
        "non_increasing_timestamp_rows": int(flags["timestamp_not_increasing"].sum()),
        "large_timestamp_gap_rows": int(flags["large_timestamp_gap"].sum()),
        "flagged_rows": int(flags.any(axis=1).sum()),
        "constant_sensor_channels": constant_channels,
        "median_observed_interval_ms": median_interval_ms,
        "estimated_observed_rate_hz": observed_rate_hz,
        "recording_duration_seconds": duration_seconds,
        "notes": [
            "A quality flag indicates something to review, not necessarily a sensor failure.",
            "Constant sensor readings can be legitimate when a finger or sensor is inactive.",
            "The observed rate is estimated from timestamp differences and may be limited by millisecond timestamp precision.",
            "The sample-number column header is not treated as proof of the actual sampling rate.",
            "Raw input is preserved unchanged."
        ],
    }
    (out_dir / "quality_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )

    #Plots
    if data[TIMESTAMP_COL].notna().any():
        start_ms = data[TIMESTAMP_COL].dropna().min()
        elapsed = (data[TIMESTAMP_COL] - start_ms) / 1000
        fig, ax = plt.subplots(figsize=(10, 5))
        for col in FINGER_COLS:
            ax.plot(elapsed, data[col], label=col)
        ax.set_title(f"Fingertip sensor readings — {input_path.stem}")
        ax.set_xlabel("Elapsed time (seconds)")
        ax.set_ylabel("Recorded reading (column units)")
        ax.legend(ncol=2)
        ax.grid(True, alpha=0.3)
        fig.tight_layout()
        fig.savefig(out_dir / "fingertip_readings.png", dpi=140)
        plt.close(fig)

        fig, ax = plt.subplots(figsize=(10, 5))
        for col in ["roll (deg)", "pitch (deg)", "yaw (deg)"]:
            ax.plot(elapsed, data[col], label=col)
        ax.set_title(f"Orientation readings — {input_path.stem}")
        ax.set_xlabel("Elapsed time (seconds)")
        ax.set_ylabel("Degrees")
        ax.legend()
        ax.grid(True, alpha=0.3)
        fig.tight_layout()
        fig.savefig(out_dir / "orientation_readings.png", dpi=140)
        plt.close(fig)

    return report


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run basic quality checks on a glove sensor CSV."
    )
    parser.add_argument("csv_file", help="Path to the input CSV file")
    parser.add_argument(
        "--output", default="data/processed",
        help="Output folder (default: data/processed)"
    )
    args = parser.parse_args()
    report = process_file(Path(args.csv_file), Path(args.output))
    print(json.dumps(report, indent=2))
    print(f"\nOutputs saved under: {Path(args.output) / Path(args.csv_file).stem.replace(' ', '_')}")


if __name__ == "__main__":
    main()
