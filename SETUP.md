# Setup Guide

This lab package runs in two environments from the same code: the shared class lab
(the cyberlab path) and your own machine (the portable path). For a step-by-step guide to
running at home, including a real local model with no Docker, see
[RUN_LOCALLY.md](RUN_LOCALLY.md).

---

## Prerequisites

| | Cyberlab path | Portable path |
|---|---|---|
| Docker + Docker Compose v2 | on student/attacker hosts (optional) | **required** |
| Python 3.9+ | required (for the CLI helpers) | required |
| Network | VPN into the cyberlab subnet | none |
| GPU | provided (Tesla T4 on the GPU VM) | not needed (mock LLM) |

Install the (light) Python deps once:
```bash
python3 -m pip install -r common/requirements.txt
```
> The `ollama_client` and `wazuh_client` use only the Python standard library, so they work
> even without the pip install. `python-dotenv`, `rich`, and `tabulate` just make output nicer.

### Installing Docker (Ubuntu student VMs)

The dockerized labs (Module 2 targets and attacker, the Module 4 assistant, and the
offline mock) need Docker Engine plus the Compose plugin. On Ubuntu 22.04 / 24.04:
```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
newgrp docker            # apply the docker group now (or log out and back in)
docker --version && docker compose version
```

---

## 1. Configure `.env`

```bash
cp .env.example .env
```

Then edit the values. The important ones:

| Variable | Cyberlab value | Portable value |
|----------|----------------|----------------|
| `OLLAMA_HOST` | `http://10.50.142.235:11434` | `http://localhost:11435` (after `lab_up.sh core`) |
| `OLLAMA_MODEL` | `llama3.1:8b` | `llama3.1:8b` |
| `WAZUH_API` | `https://10.50.136.116:55000` | (leave as-is; unused offline) |
| `WAZUH_USER` / `WAZUH_PASS` | from your instructor | (unused offline) |
| `WAZUH_INDEXER` | `https://10.50.136.116:9200` | (unused offline) |
| `AI_SOC_MODE` | `vulnerable` | `vulnerable` |

`VERIFY_TLS=0` is set because the lab Wazuh uses self-signed certs. **Never** disable TLS
verification in production.

---

## 2A. Cyberlab path - verify the real services

```bash
python3 scripts/verify_env.py
```
Expected:
```
[PASS] Ollama   reachable at http://10.50.142.235:11434 - models: llama3.1:8b
[PASS] Wazuh    manager 4.14.x reachable at https://10.50.136.116:55000
```

If Wazuh fails with `401`: you are almost certainly using the **dashboard** password
for the **API** user. They are different (see below).

### Wazuh credentials (the #1 gotcha)

Wazuh has three separate credential sets:

| Set | User | Port | Goes in `.env` as |
|-----|------|------|-------------------|
| Dashboard / Indexer | `admin` | 443 / 9200 | `WAZUH_INDEXER_USER` / `WAZUH_INDEXER_PASS` |
| **Manager API** | `wazuh-wui` | 55000 | `WAZUH_USER` / `WAZUH_PASS` |
| Internal indexer svc | `kibanaserver` etc. | 9200 | (not needed) |

The password you type into the web dashboard is the `admin` (indexer) password. The
**API** on port 55000 uses `wazuh-wui` with a **different** password. `verify_env.py`
authenticates against the API, so if you paste the dashboard password as `WAZUH_PASS`
you get `401`.

Your instructor gives you the four `WAZUH_*` lines for `.env`:
```
WAZUH_USER=wazuh-wui
WAZUH_PASS=<api password for wazuh-wui>
WAZUH_INDEXER_USER=admin
WAZUH_INDEXER_PASS=<admin/dashboard password>
```
Paste them into `.env` and re-run `python3 scripts/verify_env.py`.

If Ollama fails with "Connection refused" or a timeout, check your VPN first, then tell
your instructor: the shared GPU VM may be down or unreachable from your subnet.

---

## 2B. Portable path - bring up the Docker lab

```bash
# Smoke-test the AI pipeline end to end (no GPU/VPN):
bash scripts/smoke_test.sh          # expect 4/4 PASS

# Start what a module needs (profiles):
scripts/lab_up.sh core              # mock-ollama + ai-soc-assistant   (Modules 1,3,4,5)
scripts/lab_up.sh core targets attack   # + victims + attacker         (Modules 2,5)
scripts/lab_up.sh logs              # synthetic log generator -> datasets/generated/
```

To run fully offline, set both of these in `.env` (the shipped defaults point at the
cyberlab GPU VM):
```
OLLAMA_HOST=http://localhost:11435          # host-side scripts -> local mock
AI_SOC_OLLAMA_HOST=http://mock-ollama:11434 # the assistant container -> local mock
```
Then `python3 common/ollama_client.py --health` should list `llama3.1:8b` (served by the mock).

Prefer to run your **own real Ollama** (on a home box or VM) and reach it over your
network or VPN? See [SELF_HOSTING_OLLAMA.md](SELF_HOSTING_OLLAMA.md), then set
`OLLAMA_HOST=http://<your-server-ip>:11434` in `.env`.

Service map (host ports default from `.env`):

| Service | URL / access | Profile |
|---------|--------------|---------|
| AI SOC assistant | http://localhost:8080 | core |
| Mock Ollama | http://localhost:11435/api/tags | core |
| Victim web (vulnerable) | http://localhost:8081 | targets |
| Victim SSH | `ssh labuser@localhost -p 2222` (pass `Password1`) | targets |
| Attacker shell | `docker exec -it soclab-attacker-1 bash` | attack |

---

## 3. Teardown

```bash
scripts/lab_down.sh     # stop containers (keep images/volumes)
scripts/teardown.sh     # stop + remove locally-built images, volumes, generated logs
```

---

## Isolation & safety

- The `victim-web` and `victim-ssh` containers are **intentionally vulnerable**. Keep them on
  the internal lab network only. Never bind them to a public interface or feed real data.
- Red-team payloads in Module 4 are benign (they flip verdicts or leak the assistant's own
  system prompt). No payload here provides real-world offensive capability.
- The Docker network `soclab` is bridged and local to the host; the attacker container reaches
  the victims by service name, not your real network.

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `port is already allocated` on 11434 | A real Ollama is running locally. The mock uses host port **11435** by default; change `MOCK_OLLAMA_PORT` in `.env` if needed. |
| `verify_env.py` Wazuh FAIL | Check VPN, `WAZUH_PASS`, and that port 55000 is reachable. |
| Assistant shows `[ERROR] Could not reach Ollama` | `OLLAMA_HOST` is wrong for your path (see the table in §1). |
| `docker compose` not found | Install Docker Desktop / the Compose v2 plugin. |
| Attacker `hydra`/`nmap` slow first run | The attacker image builds from Debian + apt on first `up`; subsequent runs are cached. |
