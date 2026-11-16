# AI Blue Team & Intro to AI Red Teaming - Bootcamp Labs

Student lab package for the 5-day bootcamp delivered by **Valix AI (Dr. Gaspard Baye)**
for **Evolve Academy**. Five days, two hours each. Every day is a self-contained module
with a step-by-step student guide, runnable labs, and a slide deck.

> **New here? Open [START_HERE.md](START_HERE.md).** It tells you exactly what to run
> first and links every lab in order.
>
> **Working from home? Open [RUN_LOCALLY.md](RUN_LOCALLY.md).** It shows how to run the
> labs on your own machine with no VPN.

---

## What's in the box

| Path | What it is |
|------|-----------|
| [module1-foundations/](module1-foundations/STUDENT_GUIDE.md) | Day 1 - AI in the SOC: connect to the model and the SIEM, first AI log triage |
| [module2-detection/](module2-detection/STUDENT_GUIDE.md) | Day 2 - Detection: read real attack telemetry and catch it |
| [module3-prompt-engineering/](module3-prompt-engineering/STUDENT_GUIDE.md) | Day 3 - Prompt engineering: Sigma rules, summaries, an AI triage workflow |
| [module4-red-teaming/](module4-red-teaming/STUDENT_GUIDE.md) | Day 4 - AI red teaming: prompt injection (direct and indirect) and its defense |
| [module5-capstone/](module5-capstone/SCENARIO.md) | Day 5 - Capstone: an end-to-end AI-powered incident, scored |
| [slides/](slides/) | One slide deck per module |
| [common/](common/) | Reusable `ollama_client`, `wazuh_client`, and a security prompt library |
| [datasets/](datasets/) | Sample auth and web logs, a poisoned log, and a threat-intel feed |
| [scripts/](scripts/) | `verify_env`, `lab_up`, `lab_down`, `teardown`, `smoke_test`, `selftest` |
| [docker/](docker/) | Optional local lab: mock model, AI SOC assistant, victims, attacker |

---

## Two ways to run the labs

### In class: the shared lab (Python only, no Docker)

You reach two shared machines over the lab network. You do not log in to them; your
scripts talk to the model and the SIEM:

- Ollama `llama3.1:8b` on the GPU VM, `10.50.142.235:11434`
- Wazuh 4.14 on `10.50.136.116` (dashboard 443, API 55000, indexer 9200)

```bash
# From the repo root
cp .env.example .env
# Paste the four WAZUH_* lines your instructor gives you into .env.
# OLLAMA_HOST and WAZUH_API already point at the two machines.

python3 scripts/verify_env.py     # Ollama and Wazuh should pass
```

Then start at [START_HERE.md](START_HERE.md).

### At home: your own machine (no VPN)

Run the real model with Ollama, or a mock model with Docker. Either way it is a
two-line change in `.env`:

```bash
ollama pull llama3.1:8b                      # then set OLLAMA_HOST=http://localhost:11434
python3 common/ollama_client.py --health
python3 module1-foundations/labs/first_ai_triage.py datasets/auth.log
```

The full walkthrough, including the Docker option and what replaces Wazuh at home, is in
[RUN_LOCALLY.md](RUN_LOCALLY.md).

---

## The signature lab: indirect prompt injection

Day 4 ties blue and red together. An attacker plants a prompt-injection payload inside a
field that ends up in a **log** (a crafted `User-Agent` or username). When an analyst asks
the AI SOC assistant to triage that alert, the payload hijacks the model: it flips a
malicious verdict to "benign," or leaks the system prompt. You then switch the assistant to
**hardened** mode (prompt isolation, input sanitization, output validation), run the same
attacks again, and see the Wazuh rule that flags injection payloads in logs before the AI
ever reads them.

---

## Safety & scope

This package is for **authorized, educational** security training in an isolated lab. The
"victim" apps are intentionally vulnerable and must never be exposed to the internet or
real data. Red-team payloads are benign (they flip a verdict or leak the assistant's own
prompt) and are always paired with the detection and mitigation that stops them. See
[SETUP.md](SETUP.md) for isolation notes.
