# Run the Labs on Your Own Machine

You can do the labs at home with no VPN and no access to the class lab. Pick one of
the two options below for the AI model. Both use the same lab scripts; only two lines
in `.env` change.

| | Option A: real model (Ollama) | Option B: mock model (Docker) |
|---|---|---|
| What you get | The same `llama3.1:8b` model used in class | A small deterministic stand-in |
| Needs | About 8 GB of RAM and 5 GB of disk | Docker; any laptop, no GPU |
| Best for | Realistic answers; Modules 1, 2, 3, 5 | Module 4, where attacks land every time |
| Answers | Vary from run to run | Always the same |

Wazuh (the SIEM) is not available at home. Every lab that uses it has a dataset-based
path, listed in [What replaces Wazuh](#what-replaces-wazuh) below.

---

## 1. Get the code

```bash
git clone https://github.com/bayegaspard/AI-for-Blue-Teamers-Bootcamp-Student-Labs.git
cd AI-for-Blue-Teamers-Bootcamp-Student-Labs      # run every command from this folder
cp .env.example .env
```

You need Python 3.9 or newer. The lab scripts use only the standard library, so there is
nothing to install. Optional, for nicer terminal output:

```bash
python3 -m pip install -r common/requirements.txt
```

---

## 2. Start a model

### Option A - the real model with Ollama

1. Install Ollama from <https://ollama.com/download> (macOS, Windows, Linux).
2. Download the course model (about 4.9 GB, one time):
   ```bash
   ollama pull llama3.1:8b
   ```
3. Open `.env` and change this one line:
   ```
   OLLAMA_HOST=http://localhost:11434
   ```
4. Check it:
   ```bash
   python3 common/ollama_client.py --health
   ```
   Expected: `[OK] Ollama reachable at http://localhost:11434` and `llama3.1:8b` in the
   model list.

The first answer takes 30 to 60 seconds while the model loads; after that it stays warm.
Without a GPU, expect each answer to take from a few seconds up to a minute.

To use a model you already have, set `OLLAMA_MODEL` in `.env` to its exact name from
`ollama list`. Smaller models are faster but follow the output format less reliably.

### Option B - the mock model with Docker

1. Install Docker Desktop (macOS, Windows) or Docker Engine (Linux), and start it.
2. Start the local stack:
   ```bash
   scripts/lab_up.sh core
   ```
3. Open `.env` and change these two lines:
   ```
   OLLAMA_HOST=http://localhost:11435
   AI_SOC_OLLAMA_HOST=http://mock-ollama:11434
   ```
4. Check it:
   ```bash
   python3 common/ollama_client.py --health
   bash scripts/smoke_test.sh          # expect 4/4 PASS
   ```

This also starts the web version of the AI SOC assistant at <http://localhost:8080>.

Stop it with `scripts/lab_down.sh`. Remove everything it created with
`scripts/teardown.sh`.

---

## 3. Check your setup

```bash
python3 scripts/verify_env.py
```

At home, Ollama should pass and the two Wazuh checks should fail. That is expected:
there is no Wazuh on your machine. You are ready when Ollama passes.

---

## 4. Do the labs

Open each module's student guide and follow it. These are the commands that work at home:

| Module | Guide | Run this |
|---|---|---|
| 1 Foundations | [STUDENT_GUIDE](module1-foundations/STUDENT_GUIDE.md) | `python3 module1-foundations/labs/first_ai_triage.py datasets/auth.log` |
| 2 Detection | [STUDENT_GUIDE](module2-detection/STUDENT_GUIDE.md) | `python3 module2-detection/labs/detect_bruteforce.py` and `python3 module2-detection/labs/detect_web_attacks.py` |
| 3 Prompt engineering | [STUDENT_GUIDE](module3-prompt-engineering/STUDENT_GUIDE.md) | `python3 module3-prompt-engineering/labs/triage_workflow.py --source file` |
| 4 AI red teaming | [STUDENT_GUIDE](module4-red-teaming/STUDENT_GUIDE.md) | `python3 module4-red-teaming/labs/inject.py --list` |
| 5 Capstone | [SCENARIO](module5-capstone/SCENARIO.md), [WORKSHEET](module5-capstone/STUDENT_WORKSHEET.md) | Follow Path B (the datasets), then `python3 module5-capstone/labs/capstone_check.py` |

### What replaces Wazuh

| Lab | In class | At home |
|---|---|---|
| 1.4 Meet the SIEM | Wazuh dashboard and `wazuh_client.py` | Read the lab for the concepts; the alerts it shows come from the logs in `datasets/` |
| 2.1 See the telemetry | Alerts from the shared Wazuh | `cat datasets/auth.log datasets/access.log` |
| 3.4 Triage workflow | Live alerts | Add `--source file` to use the bundled sample alerts |
| 5 Capstone | Path A (Wazuh) | Path B (the datasets) |

Commands that call `common/wazuh_client.py` will report that Wazuh is unreachable. Skip
them and use the dataset command next to them in the guide.

### A note on Module 4 with a real model

A real model is not deterministic. A blatant payload is often refused, and a subtle one
may need two or three tries to land, in either mode. The pattern is what matters: the
vulnerable prompt can be hijacked and the hardened prompt resists far more often. If you
want every attack and every defense to behave the same way each run, use Option B.

---

## Optional: your own attack lab (Docker)

To generate the attacks yourself against intentionally vulnerable targets on your own
machine:

```bash
scripts/lab_up.sh core targets attack
docker exec -it soclab-attacker-1 bash
#   inside: /opt/attacks/attack_ssh_bruteforce.sh victim-ssh labuser
#           /opt/attacks/attack_web_sqli.sh victim-web 8081
```

Keep these containers on your own machine. They are vulnerable on purpose. See
[SETUP.md](SETUP.md) for the service map and safety notes.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `[FAIL]` from `ollama_client.py --health` | Option A: is the Ollama app running? Try `ollama list`. Option B: is Docker running, and did `scripts/lab_up.sh core` finish? |
| The health check passes but a lab says the model is missing | `OLLAMA_MODEL` in `.env` must match a name from `ollama list` exactly. |
| `HTTP Error 404` from a lab even though `ollama list` shows the model | Another Ollama (often a Docker container) is also listening on 11434 and `localhost` reaches it instead. Set `OLLAMA_HOST=http://127.0.0.1:11434`, or stop the container. |
| The first answer times out | The model is still loading. Run the command again. |
| `port is already allocated` on 11434 | Ollama already uses that port. The mock uses 11435 for that reason; change `MOCK_OLLAMA_PORT` in `.env` if 11435 is also taken. |
| Wazuh checks fail | Expected at home. Use the dataset path for that lab. |
| `docker compose` not found | Install Docker Desktop, or the Compose v2 plugin on Linux. |
