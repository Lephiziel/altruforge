# TLC tool availability check

**Checked:** 2026-11-26 in the NIR-04 worktree. No model run was attempted because TLC was not available locally and the environment did not provide a verified JAR.

```text
$ command -v tlc
[no path; command not found]
$ command -v tlatex
[no path; command not found]
$ command -v java
/usr/bin/java
$ java -version
openjdk version "27.0.1.1" 2026-11-17
OpenJDK Runtime Environment (build 27.0.1.1)
OpenJDK 64-Bit Server VM (build 27.0.1.1, mixed mode, sharing)
$ find /usr/share/java /home/lephiziel/.local /home/lephiziel/Projects /tmp -type f -iname 'tla2tools*.jar'
[no matching files]
```

These are discovery results, not model-checking output. The official TLA+ repository says `tla2tools.jar` is distributed from releases and requires Java 11+ ([official project](https://github.com/tlaplus/tlaplus)). No NIR-04 state count, pass, or counterexample is reported.
