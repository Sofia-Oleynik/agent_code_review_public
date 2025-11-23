# agentCodeReviewer.py
import os, json, logging, time, re
from typing import List, Dict, Tuple
from openai import OpenAI
from dotenv import load_dotenv
import nbformat as nbf  # NEW
from nbformat.reader import reads as nb_read  # NEW
from hawk_python_sdk import Hawk  # NEW

load_dotenv("/home/oleynikss/agent_code_review/.env")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
YANDEXGPT_API_KEY = os.getenv("YANDEXGPT_API_KEY")
YANDEX_CLOUD_FOLDER_ID = os.getenv("YANDEX_CLOUD_FOLDER_ID")
MODEL = os.getenv("MODEL")

MODELS = [
    MODEL
    # "yandexgpt-lite",
    # "yandexgpt",
    #"google/gemini-2.0-flash-exp:free",
    # "qwen/qwen3-coder:free",
    # "x-ai/grok-4-fast:free",
    ]

is_used_yandex = any("yandexgpt" in model for model in MODELS) if MODELS else False

MAX_ATTEMPTS_PER_MODEL = 15  # NEW
REQUEST_TIMEOUT = 60  # сек, по вкусу

class CodeChecker:
    def __init__(
            self,
            max_history_size: int = 10,
            system_prompt: str = ""
        ):

        self.client = OpenAI(
            base_url="https://llm.api.cloud.yandex.net/v1" if is_used_yandex else "https://openrouter.ai/api/v1",
            api_key=YANDEXGPT_API_KEY if is_used_yandex else OPENROUTER_API_KEY,
            max_retries=0,
            timeout=REQUEST_TIMEOUT,
            project=f"{YANDEX_CLOUD_FOLDER_ID}" if is_used_yandex else None
        )
        self.max_history_size = max_history_size
        self.system_prompt = system_prompt
        self.chat_history = {}
        self.system_message = self.generate_system_message()

    def generate_system_message(self) -> Dict:
        return {"role": "system", "content": self.system_prompt}

    def load_criteria_from_readme(self, readme_content: str) -> None:
        criteria_text = (readme_content or "").strip()
        self.system_message = {
            "role": "system",
            "content": f"{self.system_message['content']}\n{criteria_text}"
        }



    # NEW: вытащить только текст/код из .ipynb и выкинуть картинки/outputs
    def preprocess_notebook_to_text(self, nb_raw: str) -> Tuple[str, int]:
        if not nb_raw:
            return "", 0
        try:
            nb = nbf.reads(nb_raw, as_version=4)
        except Exception as exc:
            # если по какой-то причине это невалидный JSON ноутбука — отправим как текст
            raise ValueError(str(exc))

        chunks = []
        for cell in nb.cells:
            if cell.cell_type == "markdown":
                # attachments в markdown нам не нужны
                cell.attachments = {}
                chunks.append(cell.source or "")
            elif cell.cell_type == "code":
                # очищаем outputs и execution_count
                cell.outputs = []
                cell.execution_count = None
                # оставляем код
                chunks.append(cell.source or "")
            # raw можно игнорировать

        text = "\n\n".join(chunks).strip()
        approx_tokens = int(len(text) / 4)  # грубая оценка токенов

        return text, approx_tokens

    def _is_upstream_ratelimit(self, err_text: str) -> bool:
        # OpenRouter типично возвращает "... is temporarily rate-limited upstream"
        return "temporarily rate-limited upstream" in err_text.lower()

    def _is_maximim_contenxt_length_exception(self, err_text: str) -> bool:
        return "maximum context length is" in err_text.lower() or "exceeds the maximum number of tokens allowed" in err_text.lower()

    def analyze_code_with_fallback(self, code: str, chat_id: int) -> Tuple[str, str]:
        if chat_id not in self.chat_history:
            self.chat_history[chat_id] = [self.system_message]

        self.chat_history[chat_id].append({"role": "user", "content": code})
        self.chat_history[chat_id] = self.chat_history[chat_id][-self.max_history_size:]

        last_error = None
        for model in MODELS:
            for attempt in range(1, MAX_ATTEMPTS_PER_MODEL + 1):
                try:
                    resp = self.client.chat.completions.create(
                        model=f"gpt://{YANDEX_CLOUD_FOLDER_ID}/{model}/latest" if is_used_yandex else model,
                        temperature=0.0,
                        messages=[
                            {"role": m["role"], "content": m["content"]}
                            for m in self.chat_history[chat_id]
                        ],
                    )


                    content = resp.choices[0].message.content or ""
                    # удачно
                    self.chat_history[chat_id].append({"role":"assistant","content":content})
                    return content, model, last_error

                except Exception as e:
                    txt = str(e)
                    last_error = txt
                    logging.error(f"Model {model} attempt {attempt} failed: {txt}")

                    # Если именно upstream ratelimit — ждем секунду и идем к следующей попытке
                    if self._is_upstream_ratelimit(txt):
                        time.sleep(3)

                    if self._is_maximim_contenxt_length_exception(txt):
                        break

        # Все модели не сработали
        return "error", MODELS[0], last_error