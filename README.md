# BOTIA Regulatory Intelligence

**Automated monitoring and traceability for regulatory and scientific sources.** Paloma García Muley designed and developed the documentary monitoring system for BOTIA Safe Food. This repository demonstrates one of its decisions: when a source check should retain the previous observation, request editorial review, or record a failed consultation.

A public authority can revise a document while a knowledge catalogue still cites an older edition. A source can also return the wrong page, an older revision, or no response. The operational system keeps the observed evidence and the editorial decision separate, so a reviewer can reconstruct what changed and decide which references need updating.

[Professional portfolio](https://servicehubbotia-glitch.github.io/technology-AIportfolio/) · [Documented BOTIA monitoring case](https://servicehubbotia-glitch.github.io/technology-AIportfolio/knowledge-monitor.html?lang=en)

## Run it

From the project root, use Python 3.12 and its standard library. The replay and tests work offline.

```sh
python -B scripts/demo_watch.py
python -B scripts/demo_watch.py --verify examples/sample-report.json
python -B -m unittest discover -s tests -v
```

The first command prints the JSON report. The second compares it byte for byte with the committed example. The third tests failure isolation, identity and date checks, input integrity and the command-line interface. GitHub Actions runs the last two commands on pushes, pull requests and manual dispatch.

## Read the result

All three records are synthetic. **1 November 2026** is the date inside the scenario. Running the demo today replays that same observation set.

| Synthetic document | Last seen → observed | Result | What happens next |
| --- | --- | --- | --- |
| Additives bulletin | 1 Sep → 1 Sep | `SIN_CAMBIOS` | Retain the previous observation. |
| Labelling standard | 15 Aug → 15 Oct | `VERSION_NUEVA` | A reviewer examines the later edition before deciding whether to incorporate it. |
| Packaging guidance | 20 Oct → timeout | `CONSULTA_FALLIDA` | Preserve the last successful observation and investigate the failed check. |

The JSON records the watcher ID, document ID, previous and observed dates, outcome, reason and next action. Two SHA-256 digests identify the exact fixture bytes. To try a different case, copy the observations file, edit one release date and run:

```sh
python -B scripts/demo_watch.py --observations my-observations.json
```

[Watcher fixture](examples/sample-watchers.json) · [Observation fixture](examples/sample-observations.json) · [Expected report](examples/sample-report.json)

## What Paloma built

The operational Python system queries official sources, including EU Publications Office data for EUR-Lex, US eCFR sections, Codex records and EFSA publication feeds. Depending on the source, it compares dated versions, publication identifiers or content fingerprints. It records per-source failures, preserves successful observations and logs detections for editorial review. GitHub Actions runs checks and retains reports. The catalogue and index are protected during monitoring.

The public implementation replays **one dated-release comparison** from local fixtures. It supplies neither the live connectors nor the operational registry, catalogue, evidence archive or editorial criteria. The report proposes an action. Editorial review and follow-up checks are performed outside the replay.

[Architecture](ARCHITECTURE.md) · [Method and traceability](docs/methodology.md) · [Technical case study](docs/technical-case-study.md) · [Evaluation terms](LICENSE)
