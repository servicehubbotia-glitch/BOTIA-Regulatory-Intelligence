# A changed regulation and a retained citation

## The operational case

A dated snapshot in Paloma García Muley’s portfolio documents an example from EU Regulation 2023/915. During the October 2026 monitoring window, the catalogue still referenced the consolidation of 8 October 2025. The watcher observed an edition dated 19 August 2026 and recorded the discrepancy for review. The portfolio shows the status at the time of that snapshot.

A document’s availability, its significance for a particular reference and an editor’s decision to incorporate it are three different facts. Recording the source identity and both editions lets a reviewer investigate the second and third questions after detection.

[Portfolio case and historical snapshot](https://servicehubbotia-glitch.github.io/technology-AIportfolio/knowledge-monitor.html?lang=en) · [EUR-Lex consolidation cited in the case](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:02023R0915-20260819)

## Trying the decision locally

The synthetic labelling standard in the demo lets a reviewer reproduce that comparison without the source collection. Change its observed date to the previous date and the row becomes unchanged. Give it a date earlier than the baseline and the row records a regressive response. In each case the other two rows can still be evaluated.

This small example makes the project’s engineering choices inspectable: stable document identity, failure isolation, traceable input bytes and an explicit handoff to an editor. It can be evaluated with Python alone.
