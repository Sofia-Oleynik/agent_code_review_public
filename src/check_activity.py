# src/check_activity.py
import os, json, datetime
from dotenv import load_dotenv
from  src.send_alert_to_email import send_message

load_dotenv("/home/oleynikss/agent_code_review/.env")

DB_PATH = "agent_code_review/data/pull_request_activity.json"
MAX_REQUESTS_PER_DAY = int(os.getenv("MAX_REQUESTS_PER_DAY", "200"))
NUMBER_OF_TEAMS = int(os.getenv("NUMBER_OF_TEAMS", "10"))
NUMBER_OF_REQUEST_PER_TEAM = int(os.getenv("NUMBER_OF_REQUEST_PER_TEAM", "5"))
ALLOWED_PER_DAY = min(MAX_REQUESTS_PER_DAY, NUMBER_OF_TEAMS * NUMBER_OF_REQUEST_PER_TEAM)

delta_time = 1  # минут — как у тебя было

def _load():
    try:
        with open(DB_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def _save(data):
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def _today():
    return datetime.datetime.now()


def check_repo_activity(repo_name: str):
    d = _load()
    now = _today()

    if d.get(repo_name) is None:
        d[repo_name] = {
            "repo_name": repo_name,
            "last_date_activity": now.isoformat(),
            "attempts": 1
        }
        _save(d)
        return (True, f"Запрос принят. Осталось сегодня: 99/{ALLOWED_PER_DAY}.", 99, ALLOWED_PER_DAY)

    rec = d.get(repo_name)

    last_activity_date = datetime.datetime.fromisoformat(rec["last_date_activity"])
    if last_activity_date.day != now.day or last_activity_date.month != now.month or last_activity_date.year != now.year:
        rec["last_date_activity"] = now.isoformat()
        rec["attempts"] = 1
        _save(d)  # Сохраняем сразу сброс
        return (True, f"Запрос принят. Осталось сегодня: 99/{ALLOWED_PER_DAY}.", 99, ALLOWED_PER_DAY)

    if (now - datetime.datetime.fromisoformat(rec["last_date_activity"])) < datetime.timedelta(minutes=delta_time):
        error = "Слишком частые запросы! Повторите через 1 минуту"
        isMessaged, response = send_message(f"ERROR with check_activity",
                                            f"Репозиторий: {repo_name}\n\nОшибка:\n\n{str(error)}")
        return (False, error, 0, ALLOWED_PER_DAY)

    rec["last_date_activity"] = now.isoformat()

    remaining = ALLOWED_PER_DAY - rec["attempts"]
    if remaining <= 0:
        d[repo_name] = rec; _save(d)
        error = "Лимит попыток на сегодня исчерпан!"
        isMessaged, response = send_message(f"ERROR with check_activity",
                                            f"Репозиторий: {repo_name}\n\nОшибка:\n\n{str(error)}")
        return (False, error, 0, ALLOWED_PER_DAY)

    d[repo_name] = rec; _save(d)
    return (True, f"Запрос принят. Осталось сегодня: {remaining}/{ALLOWED_PER_DAY}.", remaining, ALLOWED_PER_DAY)


def register_attempt(repo_name: str, success: bool):
    d = _load()
    now = _today()
    rec = d.get(repo_name, {"repo_name": repo_name, "last_date_activity": now.isoformat(), "attempts": 0})

    # Та же логика сброса дня
    last_activity_date = datetime.datetime.fromisoformat(rec["last_date_activity"])
    if last_activity_date.day != now.day or last_activity_date.month != now.month or last_activity_date.year != now.year:
        rec["last_date_activity"] = now.isoformat()
        rec["attempts"] = 0

    rec["attempts"] += 1
    d[repo_name] = rec
    _save(d)