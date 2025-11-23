from flask import Flask, request, jsonify
from github import Auth, Github
import os
import logging
import requests
from src.agentCodeReviewer import CodeChecker
from src.check_activity import check_repo_activity, register_attempt, delta_time
from src.send_alert_to_email import send_message
from pprint import pformat

from collections import deque
import os, hmac, hashlib, json, time, threading
from dotenv import load_dotenv

load_dotenv("/home/oleynikss/agent_code_review/.env")

# Настройки
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
DESIGN_BRANCH = "develop"
BASE_BRANCH = 'main'
SYSTEM_PROMPT_PATH = "/home/oleynikss/agent_code_review/data/systemPrompt.txt"

REQUEST_QUEUE = deque()  # NEW
MIN_INTERVAL_SECONDS = int(os.getenv("MIN_INTERVAL_SECONDS", "60"))  # NEW
_last_processed_at = 0.0  # NEW
_queue_lock = threading.Lock()  # NEW

# Инициализация Flask и GitHub API
app = Flask(__name__)
auth = Auth.Token(GITHUB_TOKEN)
g = Github(auth=auth)

# Инициализация логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def list_files_recursive(repo, path="", ref=DESIGN_BRANCH):
    """Рекурсивно обойти репозиторий и вернуть пути (README.md и *solution.ipynb)."""
    stack = [path]
    targets = {"readme": None, "notebooks": []}
    while stack:
        cur = stack.pop()
        for f in repo.get_contents(cur, ref=ref):
            if f.type == "dir":
                stack.append(f.path)
            else:
                if f.path.lower().endswith("readme.md") and not targets["readme"]:
                    targets["readme"] = f
                if f.path.endswith("solution.ipynb"):
                    targets["notebooks"].append(f)
    return targets

def _worker_loop():
    """Фоновый воркер: достаёт задачи из очереди и обрабатывает по одной, выдерживая паузу."""
    global _last_processed_at
    while True:
        job = None
        with _queue_lock:
            if REQUEST_QUEUE:
                job = REQUEST_QUEUE.popleft()
        if not job:
            time.sleep(1)
            continue

        # Глобальный интервал между задачами
        now = time.time()
        wait = _last_processed_at + MIN_INTERVAL_SECONDS - now
        if wait > 0:
            time.sleep(wait)
        _last_processed_at = time.time()

        try:
            process_job(job)
        except Exception as e:
            isMessaged, response = send_message(f"ERROR with _worker_loop", str(e))
            if not isMessaged:
                app.logger.error(response)
            logging.exception(f"Job failed: {e}")
        # цикл продолжается

# Стартуем воркер при загрузке
# threading.Thread(target=_worker_loop, daemon=True).start()

def process_job(repo_name: str, pr_number: str):
    """Основная обработка: проверки, чтение файлов, вызов LLM, комментарий в PR."""

    repo = g.get_repo(repo_name)
    pr = repo.get_pull(pr_number)

    # check attempts/limits именно в момент обработки (а не постановки в очередь)
    ok, info_msg, remaining, allowed = check_repo_activity(repo_name)  # CHANGED API
    if not ok:
        pr.create_issue_comment(info_msg)
        return

    with open(SYSTEM_PROMPT_PATH, "r", encoding="utf-8") as f:
        system_prompt = f.read()


    targets = list_files_recursive(repo, ref=DESIGN_BRANCH)
    readme_content = ""
    nb_text = ""

    if targets["readme"]:
        r = requests.get(targets["readme"].download_url)
        r.raise_for_status()
        readme_content = r.text

    # Берём первый подходящий ноутбук (или все — если нужно)
    if targets["notebooks"]:
        r = requests.get(targets["notebooks"][0].download_url)
        r.raise_for_status()
        notebook_raw = r.text
    else:
        notebook_raw = ""

    checker = CodeChecker(system_prompt=system_prompt)
    # Загружаем критерии из README
    checker.load_criteria_from_readme(readme_content)

    # Предобработка ноутбука: удалить outputs/attachments, собрать только текст/код
    nb_text, approx_tokens = checker.preprocess_notebook_to_text(notebook_raw)  # NEW

    # Проверка на размер контекста (например, 1_000_000 токенов)
    if approx_tokens > 1000000:
        pr.create_issue_comment(
            f"Слишком большая длина входа (> 1M токенов). "
            f"Попробуйте удалить неинформативные выводы ячеек блокнота."
        )
        register_attempt(repo_name, success=False)  # NEW
        isMessaged, response = send_message(f"ERROR with approx_tokens", f"Репозиторий: {repo_name}\n\n"
                                                                         f"Ошибка:\n\nСлишком большая длина кода")
        if not isMessaged:
            app.logger.error(response)
        return

    # Анализ кода (с фоллбэком моделей и спец-обработкой rate-limited upstream)
    analysis, model_used, last_error = checker.analyze_code_with_fallback(
        nb_text, chat_id=pr_number
    )

    if analysis == "error":
        pr.create_issue_comment(
            "Ошибка при обращении к LLM. Повторите запрос позднее или измените его. \n"
            f"Последняя ошибка: {last_error}: \n"
        )
        register_attempt(repo_name, success=False)
        isMessaged, response = send_message(f"ERROR with LLM", f"Репозиторий: {repo_name}\n\nОшибка:\n\n{str(last_error)}")
        if not isMessaged:
            app.logger.error(response)
        return

    # Финальный комментарий с метаданными
    pr.create_issue_comment(
        f"{analysis}\n\n---\n"
        f"Попыток осталось на сегодня: {remaining}/{allowed} \n"
        f"оценка входных токенов: ~{approx_tokens:,} \n"
        f"модель: {model_used}"
    )
    register_attempt(repo_name, success=True)  # NEW

@app.route("/webhook", methods=["POST"])
def webhook():
    raw_body = request.data  # bytes

    app.logger.info('webhook hit: processing started')

    ############################################
    # здесь будет верификация подписи GitHub   #
    ############################################

    # Проверка типа события на pull-request
    event = request.headers.get("X-GitHub-Event", "")
    if event != "pull_request":
        return jsonify({"status": "ignored"}), 200

    app.logger.info('webhook hit: it is PR')


    data = request.get_json(force=True, silent=False)
    action = data.get("action")
    pr_data = data.get("pull_request")
    if action not in ("opened", "reopened") or not pr_data:
        return jsonify({"status": "ignored"}), 200

    base_branch = pr_data["base"]["ref"]
    head_branch = pr_data["head"]["ref"]
    repo_name = pr_data["head"]["repo"]["full_name"]
    pr_number = pr_data["number"]

    if base_branch != BASE_BRANCH or head_branch != DESIGN_BRANCH:
        return jsonify({"status": "ignored"}), 200

    app.logger.info('webhook hit: corrected branch names')

    try:
        process_job(repo_name, pr_number)

        return jsonify({"status": "processed"}), 200

    except Exception as e:
        logging.exception(f"process_job crashed: {e}")
        isMessaged, response = send_message(f"ERROR with process_job", f"Репозиторий: {repo_name}\n\nОшибка:\n\n{str(e)}")
        if not isMessaged:
            app.logger.error(response)
        return jsonify({"status": "error", "details": str(e)}), 500


@app.route('/health', methods=['GET'])
def health_check():
    """Эндпоинт для проверки работоспособности сервера."""
    return jsonify({'status': 'ok'}), 200

