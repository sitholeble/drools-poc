import argparse
import csv
import logging
import os
import sys
from typing import Any, Dict, List

import mlflow
from mlflow.entities import ViewType
from mlflow.tracking import MlflowClient


def _setup_logging(level: str) -> None:
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
        stream=sys.stdout,
    )


def _to_float(maybe: Any) -> float:
    if maybe is None:
        return float("nan")
    try:
        return float(maybe)
    except Exception:
        return float("nan")


def _pick_metric(run_metrics: Dict[str, Any], key: str, default: float = float("nan")) -> float:
    v = run_metrics.get(key)
    if v is None:
        return default
    return _to_float(v)


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize MLflow performance for recommendation experiments.")
    parser.add_argument("--tracking-uri", default=os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000"))
    parser.add_argument("--experiment-name", default=os.getenv("MLFLOW_EXPERIMENT_NAME", "gym-recommendation-ilp"))
    parser.add_argument("--output-csv", default="analysis_results.csv")
    parser.add_argument("--min-runtime-ms", type=float, default=None)
    args = parser.parse_args()

    _setup_logging(os.getenv("LOG_LEVEL", "INFO"))
    log = logging.getLogger("mlflow-performance-analysis")

    mlflow.set_tracking_uri(args.tracking_uri)
    client = MlflowClient()

    exp = client.get_experiment_by_name(args.experiment_name)
    if exp is None:
        raise SystemExit(f"Experiment not found: {args.experiment_name}")

    runs = client.search_runs(
        [exp.experiment_id],
        filter_string="",
        run_view_type=ViewType.ACTIVE_ONLY,
        max_results=10000,
    )

    rows: List[Dict[str, Any]] = []
    for run in runs:
        # MLflow 3.x exposes metrics/params as dicts (not Metric/Param entities).
        run_metrics = dict(run.data.metrics)
        run_params = dict(run.data.params)

        runtime_ms = _pick_metric(run_metrics, "runtimeMs")
        if args.min_runtime_ms is not None and not (runtime_ms >= args.min_runtime_ms):
            continue

        feasible = int(_pick_metric(run_metrics, "feasible", default=0))
        best_obj = _pick_metric(run_metrics, "best_objectiveValue")
        best_score = _pick_metric(run_metrics, "best_satisfactionScore")

        rows.append(
            {
                "run_id": run.info.run_id,
                "run_name": run.data.tags.get("mlflow.runName", run.info.run_name),
                "scenarioId": run_params.get("scenarioId", run.data.tags.get("scenarioId")),
                "profile": run_params.get("profile", run.data.tags.get("profile")),
                "diversityBonusPerCategory": run_params.get("diversityBonusPerCategory"),
                "top2Enabled": run_params.get("top2Enabled"),
                "maxBudget": run_params.get("maxBudget"),
                "maxClasses": run_params.get("maxClasses"),
                "maxDurationMinutes": run_params.get("maxDurationMinutes"),
                "feasible": feasible,
                "best_objectiveValue": best_obj,
                "best_satisfactionScore": best_score,
                "runtimeMs": runtime_ms,
            }
        )

    # CSV export
    with open(args.output_csv, "w", encoding="utf-8", newline="") as f:
        fieldnames = list(rows[0].keys()) if rows else [
            "run_id",
            "run_name",
            "scenarioId",
            "profile",
            "diversityBonusPerCategory",
            "top2Enabled",
            "maxBudget",
            "maxClasses",
            "maxDurationMinutes",
            "feasible",
            "best_objectiveValue",
            "best_satisfactionScore",
            "runtimeMs",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    if not rows:
        log.warning("No runs found under experiment=%s", args.experiment_name)
        print({"experiment": args.experiment_name, "runs": 0})
        return

    # Simple performance summary
    feasible_rows = [r for r in rows if r["feasible"] == 1]
    best_row = max(feasible_rows or rows, key=lambda r: r["best_objectiveValue"])

    def avg(values: List[float]) -> float:
        values = [v for v in values if v == v]  # drop NaNs
        return sum(values) / len(values) if values else float("nan")

    summary = {
        "experiment": args.experiment_name,
        "totalRuns": len(rows),
        "feasibleRuns": len(feasible_rows),
        "bestRun": best_row["run_id"],
        "bestProfile": best_row["profile"],
        "best_objectiveValue": best_row["best_objectiveValue"],
        "best_satisfactionScore": best_row["best_satisfactionScore"],
        "avg_runtimeMs": avg([r["runtimeMs"] for r in rows]),
        "outputCsv": args.output_csv,
    }

    log.info("Summary: %s", summary)
    print(summary)


if __name__ == "__main__":
    main()

