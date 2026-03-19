import subprocess
import sys
import requests

SCRIPTS = [
    "fantasy5_scraper.py",
    "fantasy5_stats_scraper.py",
    "powerball_scraper.py",
    "mega_millions_scraper.py",
    "pick4oh_scraper.py",
    "ny_lotto_scraper.py",
    "ny_lotto_stats_scraper.py",
]

SUMMARY_URL = "http://127.0.0.1:8000/api/system-summary"


def run_script(script_name: str):
    print("=" * 70)
    print(f"RUNNING: {script_name}")
    print("=" * 70)

    result = subprocess.run(
        [sys.executable, script_name],
        capture_output=True,
        text=True
    )

    if result.stdout:
        print(result.stdout)

    if result.stderr:
        print("ERROR OUTPUT:")
        print(result.stderr)

    if result.returncode == 0:
        print(f"OK: {script_name}")
    else:
        print(f"FAILED: {script_name} (exit code {result.returncode})")


def show_system_summary():
    print("=" * 70)
    print("SYSTEM SUMMARY")
    print("=" * 70)

    try:
        resp = requests.get(SUMMARY_URL, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        print(f"ok: {data.get('ok')}")
        print(f"states_count: {data.get('states_count')}")
        print(f"games_count: {data.get('games_count')}")
        print(f"draws_count: {data.get('draws_count')}")
        print(f"frequency_stats_count: {data.get('frequency_stats_count')}")
        print(f"grouped_games_count: {data.get('grouped_games_count')}")
        print(f"stats_supported_games_count: {data.get('stats_supported_games_count')}")
    except Exception as e:
        print(f"No se pudo obtener el resumen del sistema: {e}")


def main():
    for script in SCRIPTS:
        run_script(script)

    show_system_summary()


if __name__ == "__main__":
    main()