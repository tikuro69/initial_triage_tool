# initial_triage_tool

A small Python CLI tool for collecting baseline system information during the initial stage of incident investigation.

This tool is designed for the **first look** of a problem, not for full diagnosis.  
It collects basic read-only system information, saves the results with a timestamp, and generates a prompt file that can be passed to AI for the next step of investigation.

## Features

- Collects basic system information for initial triage
- Saves outputs under a timestamped run directory
- Generates:
  - `summary.txt`
  - `prompt.txt`
  - raw command outputs in `raw/`
- Supports predefined incident types:
  - `high_load`
  - `web_504`
  - `other` (free text)
- Uses simple read-only commands only

## Purpose

When an issue happens, it is easy to forget what to check first.

This tool helps you:

- collect basic evidence quickly
- keep a timestamped record
- organize the first review order
- prepare input for AI-assisted investigation

It does **not** attempt to fully diagnose the issue automatically.

## Requirements

- Python 3.9+
- Linux environment for command execution

## File Structure

```text
initial_triage_tool/
├─ main.py
├─ envs.json
├─ README.md
└─ runs/

runs/
└─ web_504_2026-04-03_11-47-05/
   ├─ summary.txt
   ├─ prompt.txt
   └─ raw/
      ├─ date.txt
      ├─ hostname.txt
      ├─ uptime.txt
      ├─ free.txt
      ├─ df.txt
      ├─ top.txt
      ├─ apache_error_tail.txt
      ├─ apache_access_tail.txt
      ├─ ps_cpu.txt
      └─ ps_mem.txt
```

## envs.json

Prepare an `envs.json` file like this:

```json
[
  {
    "name": "web_hosting",
    "os": "Ubuntu22",
    "web": "Apache",
    "app": "PHP",
    "db": "MySQL",
    "control_panel": "cPanel",
    "role": "Shared Web hosting",
    "notes": "multiple domains, access/error logs available"
  }
]
```

## Usage

### List environments

```bash
python main.py env list
```

### Run triage with menu selection

```bash
python main.py run
```

### Run triage directly with a symptom

```bash
python main.py run high_load
python main.py run web_504
python main.py run other
```

## Supported Incident Types

### `high_load`

Collects baseline information for a high load / slow response situation.

### `web_504`

Collects baseline information for a 504 Gateway Timeout situation.
This also tries to collect Apache access and error log tails.

### `other`

Lets you enter a free-text symptom description and collects the common baseline command set.

## Commands Collected

Common baseline commands:

* `date`
* `hostname`
* `uptime`
* `free -m`
* `df -h`
* `top -b -n 1 | head -30`
* `ps aux --sort=-%cpu | head -15`
* `ps aux --sort=-%mem | head -15`

Additional commands for `web_504`:

* `tail -n 50 /var/log/apache2/error.log`
* `tail -n 50 /var/log/apache2/access.log`

## Output Files

### `summary.txt`

Contains:

* run ID
* timestamp
* selected symptom
* environment info
* executed commands
* recommended review order
* review notes

### `prompt.txt`

Contains an English prompt you can pass to AI together with the collected raw files.

### `raw/`

Contains the raw output of each command.

## Notes

* This tool focuses on **initial triage only**
* It uses simple read-only commands
* Log paths may differ depending on your environment
* Some commands may fail because of permissions or missing files
* The tool still saves those results so you can see what happened

## Limitations

* It is not a full incident diagnosis framework
* It is not environment-aware beyond the values in `envs.json`
* It assumes a Linux-like environment
* Apache log paths are currently fixed in the code for `web_504`

## Example Workflow

1. Run the tool
2. Check `summary.txt`
3. Review the files listed in the recommended order
4. Open `prompt.txt`
5. Send the prompt and selected raw outputs to AI
6. Continue investigation based on AI suggestions

## Future Ideas

* configurable log paths via `envs.json`
* additional incident types
* output bundling into a single AI input file
* richer environment profiles

## License

MIT
