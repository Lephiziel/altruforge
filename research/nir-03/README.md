# NIR-03 / P0.1 — Forge recovery after interruption

This study continues the [NIR-02 local Git pilot](../nir-02/README.md) by exercising publication recovery on a disposable Forgejo instance. It asks when a restarted worker can identify the PR for its verified commit, preserve another contributor's changes, and distinguish a completed handoff from a conflict or an unresolved effect.

The final exploratory matrix covered seven scenarios and five recovery policies. An independent oracle confirmed 20 completions, classified 10 outcomes as explicitly unknown, and observed five safe blocks after remote head drift. A receiving checkpoint helped when the receipt had already committed. Read-back and retry with duplicate reconciliation both resolved all five eligible interrupted cases in their respective trials.

In separate endpoint probes, concurrent requests created multiple open PRs for the same branch tuple, including with identical request bodies. A PR could also be created for a head that advanced after an exact-tip check. The guarded TLA+ profile passed its configured checks, and relaxed profiles produced counterexamples for artifact binding and duplicate effects.

| Material | Location |
| --- | --- |
| State, trust boundaries, invariants, and progress conditions | [Publication specification](SPECIFICATION.md) |
| TLA+ model and TLC profiles | [Model](model/Publication.tla), [guarded](model/guarded.cfg), [stable](model/stable.cfg), [mutable refs](model/mutable-refs.cfg), [blind replay](model/blind-replay.cfg) |
| Fault schedule, controls, and oracle rules | [Experimental method](METHOD.md) |
| Endpoint probes and trial driver | [Forgejo probes](characterize.py), [runner](run.py), [independent oracle](oracle.py) |
| Commands, outputs, and interpretation | [Results](RESULTS.md) and [replication guide](REPLICATION.md) |

The study used only synthetic fixtures and disposable loopback repositories. Its conclusion is scoped to the tested provider, configuration and bounded schedules.
