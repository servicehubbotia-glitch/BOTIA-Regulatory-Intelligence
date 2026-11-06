"""Replay synthetic dated releases. All inputs are local, read-only JSON."""

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from datetime import date
from pathlib import Path

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"
ACTIONS = {
    "SIN_CAMBIOS": "retain_last_observation",
    "VERSION_NUEVA": "request_editorial_review",
    "CONSULTA_FALLIDA": "investigate_and_retry",
}


def unique_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def read_fixture(path, kind):
    raw = path.read_bytes()
    data = json.loads(raw.decode("utf-8"), object_pairs_hook=unique_keys)
    if not isinstance(data, dict) or data.get("kind") != kind:
        raise ValueError(f"expected a {kind} fixture")
    return data, hashlib.sha256(raw).hexdigest()


def calendar_day(value):
    if not isinstance(value, str) or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value):
        raise ValueError("expected a date in YYYY-MM-DD format")
    return date.fromisoformat(value)


def classify(watcher, observation, scenario_date):
    if not isinstance(observation, dict):
        return "CONSULTA_FALLIDA", "missing_or_invalid_observation", None
    if "error" in observation:
        reason = observation["error"]
        if set(observation) != {"error"} or reason not in ("timeout", "unavailable"):
            reason = "invalid_response"
        return "CONSULTA_FALLIDA", reason, None
    if observation.get("document") != watcher["document"]:
        return "CONSULTA_FALLIDA", "document_mismatch", None
    try:
        observed = calendar_day(observation.get("release"))
    except ValueError:
        return "CONSULTA_FALLIDA", "invalid_release_date", None
    release = observed.isoformat()
    if observed > scenario_date:
        return "CONSULTA_FALLIDA", "future_release", release
    if release < watcher["last_seen"]:
        return "CONSULTA_FALLIDA", "regressive_release", release
    if release == watcher["last_seen"]:
        return "SIN_CAMBIOS", "same_release", release
    return "VERSION_NUEVA", "later_release", release


def replay(watcher_path, observation_path):
    registry, registry_hash = read_fixture(watcher_path, "synthetic-watchers-v1")
    capture, capture_hash = read_fixture(observation_path, "synthetic-observations-v1")
    scenario_date = calendar_day(capture.get("scenario_date"))
    watchers = registry.get("watchers")
    observations = capture.get("observations")
    if not isinstance(watchers, dict) or not watchers or not isinstance(observations, dict):
        raise ValueError("expected a nonempty watcher map and an observation map")
    if observations.keys() - watchers.keys():
        raise ValueError("observation supplied for an unknown watcher")

    results = []
    for source_id, watcher in sorted(watchers.items()):
        if not re.fullmatch(r"[a-z][a-z0-9-]{0,63}", source_id) or not isinstance(watcher, dict):
            raise ValueError("invalid watcher entry")
        document = watcher.get("document")
        if not isinstance(document, str) or not re.fullmatch(r"DEMO-[A-Z0-9-]+", document):
            raise ValueError("watcher requires a synthetic document ID")
        if calendar_day(watcher.get("last_seen")) > scenario_date:
            raise ValueError("last observation is later than the scenario date")
        status, reason, release = classify(watcher, observations.get(source_id), scenario_date)
        results.append({
            "watcher_id": source_id,
            "document": document,
            "last_seen": watcher["last_seen"],
            "observed_release": release,
            "status": status,
            "reason": reason,
            "next_action": ACTIONS[status],
        })

    counts = Counter(row["status"] for row in results)
    return {
        "kind": "synthetic-replay-report-v1",
        "scenario_date": scenario_date.isoformat(),
        "input_sha256": {"watchers": registry_hash, "observations": capture_hash},
        "counts": {status: counts[status] for status in ACTIONS},
        "results": results,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--watchers", type=Path, default=EXAMPLES / "sample-watchers.json")
    parser.add_argument("--observations", type=Path, default=EXAMPLES / "sample-observations.json")
    parser.add_argument("--verify", type=Path, metavar="REPORT", help="compare exact report bytes")
    args = parser.parse_args()
    try:
        report = replay(args.watchers, args.observations)
        rendered = (json.dumps(report, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
        if args.verify is None:
            sys.stdout.buffer.write(rendered)
        elif args.verify.read_bytes() != rendered:
            print("Report mismatch.", file=sys.stderr)
            return 1
        else:
            print("Verified: report matches the replay byte for byte.")
    except (OSError, ValueError) as exc:
        print(f"Cannot replay fixtures: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
