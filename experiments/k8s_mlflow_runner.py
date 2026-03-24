import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

import mlflow

# Repo root (parent of `experiments/`) when running `python experiments/k8s_mlflow_runner.py`
_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from ilp_recommendation_example import recommend_for_user_detailed


def _setup_logging() -> None:
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
        stream=sys.stdout,
    )


def _load_matrix() -> List[Dict[str, Any]]:
    matrix_file = os.getenv("EXPERIMENT_MATRIX_FILE")
    matrix_json = os.getenv("EXPERIMENT_MATRIX_JSON")

    if matrix_json:
        return json.loads(matrix_json)

    if not matrix_file:
        raise ValueError("Missing one of EXPERIMENT_MATRIX_FILE or EXPERIMENT_MATRIX_JSON")

    with open(matrix_file, "r", encoding="utf-8") as f:
        return json.load(f)


def _get_choice(maybe_s: Any, default: Any) -> Any:
    if maybe_s is None:
        return default
    return maybe_s


def _scenario_value(scenario: Dict[str, Any], keys: List[str], default: Any) -> Any:
    for k in keys:
        if k in scenario:
            return scenario[k]
    return default


def main() -> None:
    _setup_logging()
    log = logging.getLogger("k8s-mlflow-runner")

    tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000")
    experiment_name = os.getenv("MLFLOW_EXPERIMENT_NAME", "gym-recommendation-ilp")
    matrix_index = int(os.getenv("JOB_COMPLETION_INDEX", "0"))

    matrix = _load_matrix()
    if matrix_index < 0 or matrix_index >= len(matrix):
        raise IndexError(f"JOB_COMPLETION_INDEX={matrix_index} out of range (matrix size={len(matrix)})")

    scenario = matrix[matrix_index]
    scenario_id = _scenario_value(scenario, ["scenarioId", "scenario_id", "id"], f"idx-{matrix_index}")

    profile = _scenario_value(scenario, ["profile"], "mixed")
    max_budget = float(_scenario_value(scenario, ["maxBudget", "max_budget"], 50))
    max_classes = int(_scenario_value(scenario, ["maxClasses", "max_classes"], 3))
    max_duration = float(_scenario_value(scenario, ["maxDurationMinutes", "max_duration"], 150))
    diversity_bonus = float(
        _scenario_value(scenario, ["diversityBonusPerCategory", "diversity_bonus"], 2.0)
    )
    top2_enabled = bool(_scenario_value(scenario, ["top2Enabled", "top2_enabled"], True))

    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment(experiment_name)

    run_name = os.getenv("MLFLOW_RUN_NAME", f"reco-{experiment_name}-{scenario_id}")

    tags = {
        "scenarioId": str(scenario_id),
        "profile": str(profile),
        "top2Enabled": str(top2_enabled),
    }
    params = {
        "maxBudget": max_budget,
        "maxClasses": max_classes,
        "maxDurationMinutes": max_duration,
        "diversityBonusPerCategory": diversity_bonus,
        "top2Enabled": top2_enabled,
    }

    log.info("Starting MLflow run: %s (index=%s)", run_name, matrix_index)

    t0 = time.perf_counter()
    with mlflow.start_run(run_name=run_name) as run:
        mlflow.set_tags(tags)
        mlflow.log_params(params)
        try:
            result = recommend_for_user_detailed(
                user_id_or_preferences=profile,
                max_budget=max_budget,
                max_classes=max_classes,
                max_duration=max_duration,
                diversity_bonus=diversity_bonus,
                top2_enabled=top2_enabled,
            )
            runtime_ms = int((time.perf_counter() - t0) * 1000)
            mlflow.log_metric("runtimeMs", runtime_ms)

            feasible = 1 if result.get("feasible") else 0
            mlflow.log_metric("feasible", feasible)

            if result.get("best") is not None:
                best = result["best"]
                mlflow.log_metric("best_objectiveValue", float(best["objectiveValue"]))
                mlflow.log_metric("best_satisfactionScore", float(best["satisfactionScore"]))
                mlflow.log_metric("best_totalPrice", float(best["totalPrice"]))
                mlflow.log_metric("best_totalDurationMinutes", float(best["totalDurationMinutes"]))
                mlflow.log_metric("best_categoriesIncludedCount", float(len(best["categoriesIncluded"])))
                mlflow.log_metric("best_numRecommendedClasses", float(len(best["recommendedClassIds"])))

            if result.get("second_best") is not None:
                second = result["second_best"]
                mlflow.log_metric("second_objectiveValue", float(second["objectiveValue"]))
                mlflow.log_metric("second_satisfactionScore", float(second["satisfactionScore"]))
                mlflow.log_metric("second_totalPrice", float(second["totalPrice"]))
                mlflow.log_metric("second_totalDurationMinutes", float(second["totalDurationMinutes"]))
                mlflow.log_metric(
                    "second_categoriesIncludedCount", float(len(second["categoriesIncluded"]))
                )
                mlflow.log_metric("second_numRecommendedClasses", float(len(second["recommendedClassIds"])))

            # Artifact for post-processing
            out_path = "/tmp/mlflow_result.json"
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2)
            mlflow.log_artifact(out_path, artifact_path="recommendation")

            log.info("MLflow run complete. runtimeMs=%s feasible=%s", runtime_ms, feasible)
            print(json.dumps({"runId": run.info.run_id, "scenarioId": scenario_id, "result": result}))
        except Exception as e:
            mlflow.set_tag("status", "failed")
            log.exception("Run failed for scenarioId=%s", scenario_id)
            # Re-raise so Kubernetes marks the pod/job as failed.
            raise


if __name__ == "__main__":
    main()

