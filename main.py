import argparse
import json
import subprocess
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ENVS_FILE = BASE_DIR / "envs.json"
RUNS_DIR = BASE_DIR / "runs"

SUPPORTED_SYMPTOMS = {
    "high_load": "Server load is high and response is slow",
    "web_504": "Web server is returning 504 Gateway Timeout",
    "other": "Other (free text)",
}


def load_json(path, default):
    if not path.exists():
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f"Error: {path.name} is not valid JSON.")
        return default


def load_envs():
    return load_json(ENVS_FILE, [])


def find_env(envs, name):
    for env in envs:
        if env["name"] == name:
            return env
    return None


def ensure_runs_dir():
    RUNS_DIR.mkdir(exist_ok=True)


def timestamp_now():
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


def select_from_list(title, items):
    print(f"\n{title}")
    for i, item in enumerate(items, start=1):
        print(f"{i}. {item}")

    while True:
        choice = input("Select number: ").strip()
        if not choice.isdigit():
            print("Error: please enter a number.")
            continue

        index = int(choice) - 1
        if 0 <= index < len(items):
            return items[index]

        print("Error: number out of range.")


def select_symptom():
    symptom_keys = list(SUPPORTED_SYMPTOMS.keys())

    print("\nAvailable symptoms")
    for i, key in enumerate(symptom_keys, start=1):
        print(f"{i}. {SUPPORTED_SYMPTOMS[key]}")

    while True:
        choice = input("Select number: ").strip()
        if not choice.isdigit():
            print("Error: please enter a number.")
            continue

        index = int(choice) - 1
        if 0 <= index < len(symptom_keys):
            return symptom_keys[index]

        print("Error: number out of range.")


def prompt_custom_symptom():
    while True:
        text = input("Describe the symptom: ").strip()
        if text:
            return text
        print("Error: symptom description is required.")


def run_command(command):
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=15,
        )
        output = result.stdout.strip()
        error = result.stderr.strip()

        if result.returncode != 0 and error:
            return f"[command]\n{command}\n\n[stderr]\n{error}\n"
        if output:
            return output
        if error:
            return error
        return "(no output)"
    except subprocess.TimeoutExpired:
        return f"(timeout) {command}"
    except Exception as e:
        return f"(error) {command}\n{e}"


def get_common_commands():
    return {
        "date.txt": "date",
        "hostname.txt": "hostname",
        "uptime.txt": "uptime",
        "free.txt": "free -m",
        "df.txt": "df -h",
        "top.txt": "top -b -n 1 | head -30",
        "ps_cpu.txt": "ps aux --sort=-%cpu | head -15",
        "ps_mem.txt": "ps aux --sort=-%mem | head -15",
    }


def get_check_commands(symptom):
    if symptom == "high_load":
        return get_common_commands()

    if symptom == "web_504":
        commands = get_common_commands()
        commands.update(
            {
                "apache_error_tail.txt": "tail -n 50 /var/log/apache2/error.log",
                "apache_access_tail.txt": "tail -n 50 /var/log/apache2/access.log",
            }
        )
        return commands

    if symptom == "other":
        return get_common_commands()

    return {}


def get_review_guidance(symptom):
    if symptom == "high_load":
        return {
            "order": [
                "uptime.txt",
                "free.txt",
                "top.txt",
                "ps_cpu.txt",
                "ps_mem.txt",
                "df.txt",
            ],
            "notes": [
                "Check whether load average in uptime is consistently high.",
                "Use free -m to check available memory and whether swap is in use.",
                "Use top to review CPU usage, wa, and load average.",
                "Check ps_cpu.txt for processes consuming high CPU.",
                "Check ps_mem.txt for processes consuming high memory.",
                "Use df -h to confirm disk usage is not close to full.",
            ],
        }

    if symptom == "web_504":
        return {
            "order": [
                "uptime.txt",
                "free.txt",
                "top.txt",
                "apache_error_tail.txt",
                "apache_access_tail.txt",
                "ps_cpu.txt",
                "ps_mem.txt",
                "df.txt",
            ],
            "notes": [
                "Check whether load average in uptime is abnormally high.",
                "Use free -m to check for memory pressure and swap usage.",
                "Use top to review CPU, memory, and wa imbalance.",
                "Check apache_error_tail.txt for timeout, proxy, or backend errors.",
                "Check apache_access_tail.txt for concentrated traffic or suspicious IPs.",
                "Check ps_cpu.txt for high CPU processes.",
                "Check ps_mem.txt for high memory processes.",
                "Use df -h to confirm disk usage is not abnormal.",
            ],
        }

    if symptom == "other":
        return {
            "order": [
                "uptime.txt",
                "free.txt",
                "top.txt",
                "ps_cpu.txt",
                "ps_mem.txt",
                "df.txt",
            ],
            "notes": [
                "Check for obvious abnormalities in load average, CPU, memory, and disk usage.",
                "Use top and ps output to identify any unusually heavy processes.",
                "Collect additional service-specific logs if needed.",
                "Send the collected baseline information to AI and ask what logs or commands should be checked next.",
            ],
        }

    return {"order": [], "notes": []}


def build_summary(symptom, symptom_text, env, commands, run_id):
    guidance = get_review_guidance(symptom)

    lines = [
        f"run_id: {run_id}",
        f"timestamp: {datetime.now().isoformat(timespec='seconds')}",
        f"symptom: {symptom}",
        f"symptom_description: {symptom_text}",
        "",
        "[environment]",
        f"name: {env.get('name', '')}",
        f"os: {env.get('os', '')}",
        f"web: {env.get('web', '')}",
        f"app: {env.get('app', '')}",
        f"db: {env.get('db', '')}",
        f"control_panel: {env.get('control_panel', '')}",
        f"role: {env.get('role', '')}",
        f"notes: {env.get('notes', '')}",
        "",
        "[executed_commands]",
    ]

    for filename, command in commands.items():
        lines.append(f"{filename}: {command}")

    lines.append("")
    lines.append("[recommended_review_order]")
    for i, filename in enumerate(guidance["order"], start=1):
        lines.append(f"{i}. {filename}")

    lines.append("")
    lines.append("[review_notes]")
    for note in guidance["notes"]:
        lines.append(f"- {note}")

    return "\n".join(lines) + "\n"


def build_prompt(symptom, symptom_text, env, commands):
    purpose_map = {
        "high_load": "I want to identify likely causes of high load and perform initial triage.",
        "web_504": "I want to identify likely causes of 504 errors and perform initial triage.",
        "other": "I want to identify likely causes of this issue and determine what should be checked next.",
    }

    file_list = "\n".join([f"- {name}" for name in commands.keys()])

    return f"""You are an assistant helping with Linux/Web server incident investigation.
Please analyze the following initial triage data and respond concisely in English.

[Symptom]
{symptom_text}

[Purpose]
{purpose_map.get(symptom, "I want to perform initial triage.")}

[Environment]
- OS: {env.get('os', '')}
- Web server: {env.get('web', '')}
- App / Runtime: {env.get('app', '')}
- DB: {env.get('db', '')}
- Control panel: {env.get('control_panel', '')}
- Role: {env.get('role', '')}
- Notes: {env.get('notes', '')}

[Collected files]
{file_list}

[Request]
- List up to 3 likely causes in priority order
- Add a short reason for each cause
- Suggest additional logs or commands to check
- Show the next investigation steps in order
- End with a short 2-3 line summary for reporting

[How to use]
Provide the contents of the txt files in this run directory together with this prompt.
"""


def save_text(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def cmd_env_list():
    envs = load_envs()
    if not envs:
        print("No environments found.")
        return

    for env in envs:
        print(f"- {env['name']}")


def cmd_run(symptom=None):
    envs = load_envs()
    if not envs:
        print("No environments found. Prepare envs.json first.")
        return

    if symptom is None:
        symptom = select_symptom()

    if symptom == "other":
        symptom_text = prompt_custom_symptom()
    else:
        symptom_text = SUPPORTED_SYMPTOMS.get(symptom, symptom)

    commands = get_check_commands(symptom)
    if not commands:
        print(f"Error: unsupported symptom '{symptom}'")
        return

    env_names = [env["name"] for env in envs]
    env_name = select_from_list("Available environments", env_names)
    env = find_env(envs, env_name)

    ensure_runs_dir()

    run_prefix = symptom if symptom != "other" else "other"
    run_id = f"{run_prefix}_{timestamp_now()}"
    run_dir = RUNS_DIR / run_id
    raw_dir = run_dir / "raw"

    run_dir.mkdir(exist_ok=True)
    raw_dir.mkdir(exist_ok=True)

    print(f"\nRunning initial triage: {symptom}")
    print(f"Output directory: {run_dir}")

    for filename, command in commands.items():
        print(f"- collecting: {filename}")
        output = run_command(command)
        save_text(raw_dir / filename, output + "\n")

    summary = build_summary(symptom, symptom_text, env, commands, run_id)
    prompt = build_prompt(symptom, symptom_text, env, commands)

    save_text(run_dir / "summary.txt", summary)
    save_text(run_dir / "prompt.txt", prompt)

    print("\nDone.")
    print(f"Saved summary: {run_dir / 'summary.txt'}")
    print(f"Saved prompt : {run_dir / 'prompt.txt'}")
    print(f"Saved raw data: {raw_dir}")


def main():
    parser = argparse.ArgumentParser(description="initial_triage_tool")
    subparsers = parser.add_subparsers(dest="command")

    env_parser = subparsers.add_parser("env", help="environment commands")
    env_sub = env_parser.add_subparsers(dest="subcommand")
    env_sub.add_parser("list", help="list environments")

    run_parser = subparsers.add_parser("run", help="run initial triage")
    run_parser.add_argument("symptom", nargs="?", choices=list(SUPPORTED_SYMPTOMS.keys()))

    args = parser.parse_args()

    if args.command == "env":
        if args.subcommand == "list":
            cmd_env_list()
            return

    if args.command == "run":
        cmd_run(args.symptom)
        return

    parser.print_help()


if __name__ == "__main__":
    main()