# Reproducing and tracing a decision

## Trace one row

Open the two fixtures and the expected report. The key `labelling-standard` identifies the same watcher in each input. The registry associates it with `DEMO-STANDARD` and a previously observed edition dated 15 August. The captured response has the same document ID and a release date of 15 October. Both dates precede the scenario date. The comparator can therefore record a later edition and hand it to a reviewer.

[Registry](../examples/sample-watchers.json) · [Observations](../examples/sample-observations.json) · [Report](../examples/sample-report.json)

## Comparison rules

1. Validate the fixture types, unique JSON keys, scenario date, registry IDs and baseline dates. Unusable configuration aborts the replay before a report is emitted.
2. Match each captured response to a configured watcher and its expected document. An unknown watcher key makes the whole observation file ambiguous. A missing response, a wrong document or an invalid release for a known watcher produces an individual failed consultation.
3. For a comparable release, compare against the last successful observation. An earlier date or a date beyond the scenario is a failure in this dated-release model. A later valid date triggers editorial review.
4. Keep the baseline in the reported row. A timeout does not invent a replacement date. Continue processing the other watchers.

## Evidence and exit codes

The report records SHA-256 over the raw UTF-8 bytes of both fixture files. Even a formatting change alters the corresponding digest. Rows are ordered by watcher ID. The scenario date comes from the fixture, which makes an exact replay possible across runs. A matching digest establishes byte identity with the example input. The synthetic records have no official provenance.

| Exit code | Interpretation |
| --- | --- |
| 0 | A report was produced, or verification matched. Individual failed consultations are legitimate recorded outcomes. |
| 1 | The supplied expected report differs from the replay, including formatting or fingerprints. |
| 2 | A file could not be read, a fixture could not be interpreted, or command arguments were invalid. |

The operational comparisons also support content fingerprints and feed identifiers. Those signals require source-specific interpretation. A human reads the source and assesses its effect on existing references.
