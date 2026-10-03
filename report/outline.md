# Technical Report — Red-Teaming Apertus (Track 1A)

> Skeleton for the publication-quality PDF. Each `[FIG]` / `[TABLE]` is a
> placeholder to fill. Target: clear enough that the jury can reproduce
> every claim from the repo alone.

## 1. Abstract
- What we tested (model, 5 attack classes, N total prompt variations)
- Headline results (X of 5 issues confirmed, strongest finding in one line)
- Responsible-disclosure statement

## 2. Introduction & scope
- Apertus 1.5 (8B-Instruct; 70B where noted), why red-teaming an open
  sovereign LLM matters
- In-scope: jailbreaks, bias/stereotyping, privacy, IP/copyright,
  factual correctness, prompt injection
- Out-of-scope: <state explicitly>

## 3. Methodology
### 3.1 Attack taxonomy
[TABLE 1: attack class × intent × #variations × seeds]
### 3.2 Harness design
- Deterministic seeded generation; JSONL logging of every prompt/response
- Heuristic judges as triage; human confirmation protocol for every finding
- One-command reproduction (`bash reproduce.sh <run-id>`)
### 3.3 Threat model
- Who the attacker is, what access they have (black-box API), what
  "success" means per class
### 3.4 Ethics & responsible disclosure
- Synthetic canaries only; no real PII; no large copyrighted excerpts
  stored; findings shared with organizers first

## 4. Findings (one subsection per issue — use findings/*.md format)
### 4.1 Issue 1: <title>
- Summary, severity/breadth/novelty/validity, repro command, redacted
  transcript excerpt, impact, suggested mitigation
- [FIG 1: example transcript, redacted]
### 4.2 Issue 2 … (up to 5)

## 5. Severity matrix
[TABLE 2: issues × severity/breadth/novelty/validity with one-line
justifications — mirrors the jury rubric]

## 6. Cross-cutting observations
- Patterns across issues (e.g. "safety drops off-English", "confidentiality
  markings ignored")
- Negative results worth reporting (attack classes that did NOT work —
  shows rigor)

## 7. Suggested mitigations (for model builders)
- Per-issue + systemic (multilingual safety data, hierarchy training, …)

## 8. Limitations
- What the harness cannot prove; heuristic judge false-positive rate;
  translation verification status; compute constraints

## 9. Reproducibility appendix
- Exact environment (transformers/torch versions), model revisions,
  all run IDs + seeds, `reproduce.sh` usage

## 10. References
