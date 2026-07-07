# 🤖 AI Agent for Automated Code Review of Student Assignments

An intelligent agent that automatically reviews student code, evaluates assignments against specified criteria, and provides structured feedback via GitHub Pull Request comments.

## 📋 Description

This project implements an AI-powered code review agent designed for educational platforms specializing in Machine Learning and Data Science courses. The agent automatically analyzes student submissions, evaluates them against predefined criteria, and provides detailed feedback with scoring.

**Key Features:**
- 🔍 Automated code review upon PR creation/reopening
- 📊 Evaluation against assignment criteria extracted from README
- 💬 Structured feedback with score justification
- ⏱️ Rate limiting (max 1 request per minute)
- 📧 Email alerts for system errors

**Demo Repository:** [test_code_review_agent](https://github.com/Sofia-Oleynik/test_code_review_agent/pull/2)

## ✨ Features

- **GitHub Integration:** Webhook handler for pull request events
- **Intelligent Review:** Uses LLM (OpenRouter/YandexGPT) for code analysis
- **Criteria Extraction:** Parses evaluation criteria from README.md
- **Jupyter Notebook Support:** Extracts code and markdown from `.ipynb` files
- **Rate Limiting:** Prevents abuse with per-repository limits
- **Attempt Tracking:** Monitors daily usage per repository
- **Email Alerts:** Sends error notifications to administrators
- **Queue Management:** Processes requests sequentially with configurable intervals

## 🔧 Technologies

- **Framework:** Flask
- **LLM Integration:** OpenRouter API, YandexGPT API
- **GitHub API:** PyGithub
- **Notebook Parsing:** nbformat
- **Environment Management:** python-dotenv
- **Email:** SMTP (Gmail)
- **Monitoring:** Custom logging and alert system

## 📁 Project Structure

```
agent_code_review/
├── app.py                      # Main Flask application
├── src/
│   ├── agentCodeReviewer.py    # LLM interaction logic
│   ├── check_activity.py       # Rate limiting and attempt tracking
│   ├── send_alert_to_email.py  # Email notification system
│   ├── check_token_use.py      # Token usage management
│   └── check_activity.py       # Repository activity tracking
├── data/
│   ├── pull_request_activity.json  # Request tracking database
│   └── systemPrompt.txt            # LLM system prompt
├── .env                         # Configuration variables
├── requirements.txt
└── README.md
```

## 🚀 Installation

### Prerequisites

- Python 3.7 or higher
- GitHub repository with webhook support
- OpenRouter or YandexGPT API key

### Clone the Repository

```bash
git clone https://github.com/Sofia-Oleynik/agent_code_review.git
cd agent_code_review
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Configuration

Create a `.env` file in the root directory:

```env
# GitHub
GITHUB_TOKEN=your_github_token

# LLM API (choose one or both)
OPENROUTER_API_KEY=your_openrouter_key
YANDEXGPT_API_KEY=your_yandex_key
YANDEX_CLOUD_FOLDER_ID=your_folder_id
MODEL=openai/gpt-4o-mini  # or "yandexgpt-lite"

# Rate Limiting
MIN_INTERVAL_SECONDS=60
MAX_REQUESTS_PER_DAY=200
NUMBER_OF_TEAMS=10
NUMBER_OF_REQUEST_PER_TEAM=5

# Email Alerts
USERNAME_EMAIL=your_email@gmail.com
PASSWORD_EMAIL_APP=your_app_password
```

### Run the Application

```bash
python app.py
```

## 🏗️ Architecture

### Workflow Diagram

```
GitHub Webhook (PR opened/reopened)
    ↓
Flask /webhook endpoint
    ↓
Validation (branch, event type)
    ↓
Queue Processing (rate limiting)
    ↓
Repository Activity Check
    ↓
Load Criteria from README.md
    ↓
Fetch solution.ipynb from develop branch
    ↓
Preprocess Notebook (remove outputs/attachments)
    ↓
LLM Analysis with Fallback (multiple models)
    ↓
Post Comment to PR with Score & Feedback
    ↓
Register Attempt & Log
```

### Key Components

**1. Webhook Handler (`app.py`)**
- Listens for GitHub pull request events
- Validates event type and branches
- Queues requests for processing
- Returns responses to GitHub

**2. Code Checker (`agentCodeReviewer.py`)**
- Loads system prompt and evaluation criteria
- Preprocesses Jupyter notebooks (removes outputs, images)
- Interacts with LLM APIs with fallback mechanism
- Handles rate limits and context length errors

**3. Activity Manager (`check_activity.py`)**
- Tracks daily attempts per repository
- Enforces per-minute and per-day limits
- Manages attempt counters with date-based reset

**4. Email Alert System (`send_alert_to_email.py`)**
- Sends error notifications to administrators
- Logs system failures and exceptions

## 📊 Rate Limiting

The agent implements multiple layers of rate limiting:

| Limit Type | Configuration | Default |
|------------|---------------|---------|
| **Per-Request Minimum Interval** | `MIN_INTERVAL_SECONDS` | 60 seconds |
| **Daily Requests Per Repository** | `MAX_REQUESTS_PER_DAY` | 200 |
| **Teams Limit** | `NUMBER_OF_TEAMS` | 10 |
| **Requests Per Team Per Day** | `NUMBER_OF_REQUEST_PER_TEAM` | 5 |
| **Effective Daily Limit** | Calculated | 50 |

## 🧠 LLM Prompting

The system uses a structured CETO (Context-Environment-Task-Objective) prompting framework:

```
[CONTEXT] Educational platform for ML courses
[ROLE] Strict but fair expert reviewer
[TASK] Analyze, evaluate, score, provide feedback
[PROCESS] Step-by-step evaluation workflow
[IMPORTANT] Mandatory requirements and constraints
[OUTPUT FORMAT] Structured review with justifications
[CRITERIA] Extracted from assignment README
```

### Evaluation Criteria

The agent evaluates student work against criteria extracted from README.md:

1. **Analyzes Assignment:** Identifies tasks and sub-tasks from criteria
2. **Reviews Solution:** Examines code and markdown cells
3. **Scores Each Criterion:** Assigns points per task
4. **Provides Justification:** Quotes code and explains reasoning
5. **Calculates Total Score:** 0-10 points with integer scoring

**Mandatory Requirements:**
- Comments for every logical code block
- Written analysis in markdown cells
- All criteria points must be addressed

## 📤 Output Format

The agent posts a structured comment to the Pull Request:

```markdown
### Ревью решения задания

**Задача [NUMBER]:**
- **Задача**: [Task name from criteria]
- **Максимальный балл**: [X/10]
- **Полученный балл**: [Y/10]
- **Обоснование**:
  - ✅ [Correct implementation with code quotes]
  - ❌ [Missing requirements with code quotes]

**Итог**
- Оценка работы: [Z] из 10
- Краткий вердикт: [Summary]
```

## 🔄 GitHub Integration

### Webhook Configuration

Configure GitHub webhook to send events to your endpoint:

1. **Payload URL:** `https://your-server.com/webhook`
2. **Content Type:** `application/json`
3. **Events:** `Pull request events`
4. **Secret:** (Optional, for verification)

### Required Permissions

The GitHub token needs:
- `repo` access (for private repositories)
- `public_repo` access (for public repositories)
- Webhook and PR comment permissions

## 📚 System Prompt Structure

The system prompt is stored in `data/systemPrompt.txt` and defines:

- **Context:** Educational environment description
- **Role:** Expert reviewer identity
- **Task:** Evaluation objectives
- **Process:** Step-by-step workflow
- **Constraints:** Mandatory requirements
- **Output Format:** Response structure
- **Criteria Placeholder:** Extracted from README


## 🐛 Error Handling

The agent handles various error scenarios:

1. **LLM Rate Limits:** Automatically retries with backoff
2. **Context Length Exceeded:** Notifies user to reduce notebook size
3. **Invalid Repository:** Validates repository existence
4. **Missing Files:** Checks for README and solution.ipynb
5. **API Failures:** Falls back to alternative models
6. **Processing Errors:** Sends email alerts to administrators

## 📈 Monitoring

The system logs:
- Request processing times
- LLM model used
- Token estimates
- Error details
- Activity attempts
- Repository activity

-------------------------------------------

# 🤖 ИИ-агент для автоматической проверки кода студенческих работ

Интеллектуальный агент для автоматической проверки студенческого кода, оценки заданий по заданным критериям и предоставления структурированной обратной связи через комментарии в Pull Request на GitHub.

## 📋 Описание

Данный проект реализует агента проверки кода на основе ИИ, предназначенного для образовательных платформ, специализирующихся на курсах по машинному обучению и Data Science. Агент автоматически анализирует студенческие работы, оценивает их по заданным критериям и предоставляет детальную обратную связь с выставлением баллов.

**Ключевые возможности:**
- 🔍 Автоматическая проверка кода при создании или повторном открытии Pull Request
- 📊 Оценка по критериям, извлеченным из README
- 💬 Структурированная обратная связь с обоснованием оценки
- ⏱️ Ограничение частоты запросов (макс. 1 запрос в минуту)
- 📧 Email-уведомления об ошибках системы

**Демонстрационный репозиторий:** [test_code_review_agent](https://github.com/Sofia-Oleynik/test_code_review_agent/pull/2)

## ✨ Возможности

- **Интеграция с GitHub:** Обработчик вебхуков для событий Pull Request
- **Интеллектуальная проверка:** Использование LLM (OpenRouter/YandexGPT) для анализа кода
- **Извлечение критериев:** Парсинг критериев оценивания из README.md
- **Поддержка Jupyter Notebook:** Извлечение кода и разметки из файлов `.ipynb`
- **Ограничение запросов:** Предотвращение злоупотреблений с лимитами на репозиторий
- **Отслеживание попыток:** Мониторинг ежедневного использования на репозиторий
- **Email-алерты:** Отправка уведомлений об ошибках администраторам
- **Управление очередью:** Последовательная обработка запросов с настраиваемыми интервалами

## 🔧 Технологии

- **Фреймворк:** Flask
- **Интеграция LLM:** OpenRouter API, YandexGPT API
- **GitHub API:** PyGithub
- **Парсинг ноутбуков:** nbformat
- **Управление окружением:** python-dotenv
- **Email:** SMTP (Gmail)
- **Мониторинг:** Кастомное логирование и система оповещений

## 📁 Структура проекта

```
agent_code_review/
├── app.py                      # Основное Flask-приложение
├── src/
│   ├── agentCodeReviewer.py    # Логика взаимодействия с LLM
│   ├── check_activity.py       # Ограничение запросов и отслеживание попыток
│   ├── send_alert_to_email.py  # Система email-уведомлений
│   ├── check_token_use.py      # Управление использованием токенов
│   └── check_activity.py       # Отслеживание активности репозиториев
├── data/
│   ├── pull_request_activity.json  # База данных запросов
│   └── systemPrompt.txt            # Системный промпт LLM
├── .env                         # Переменные конфигурации
├── requirements.txt
└── README.md
```

## 🚀 Установка

### Предварительные требования

- Python 3.7 или выше
- Репозиторий GitHub с поддержкой вебхуков
- API-ключ OpenRouter или YandexGPT

### Клонирование репозитория

```bash
git clone https://github.com/Sofia-Oleynik/agent_code_review.git
cd agent_code_review
```

### Установка зависимостей

```bash
pip install -r requirements.txt
```

### Настройка

Создайте файл `.env` в корневой директории:

```env
# GitHub
GITHUB_TOKEN=ваш_токен_github

# LLM API (выберите один или оба)
OPENROUTER_API_KEY=ваш_ключ_openrouter
YANDEXGPT_API_KEY=ваш_ключ_yandex
YANDEX_CLOUD_FOLDER_ID=ваш_id_папки
MODEL=openai/gpt-4o-mini  # или "yandexgpt-lite"

# Ограничение запросов
MIN_INTERVAL_SECONDS=60
MAX_REQUESTS_PER_DAY=200
NUMBER_OF_TEAMS=10
NUMBER_OF_REQUEST_PER_TEAM=5

# Email-алерты
USERNAME_EMAIL=ваша_почта@gmail.com
PASSWORD_EMAIL_APP=пароль_приложения
```

### Запуск приложения

```bash
python app.py
```

## 🏗️ Архитектура

### Схема работы

```
Вебхук GitHub (PR открыт/переоткрыт)
    ↓
Эндпоинт Flask /webhook
    ↓
Валидация (ветка, тип события)
    ↓
Обработка очереди (ограничение запросов)
    ↓
Проверка активности репозитория
    ↓
Загрузка критериев из README.md
    ↓
Получение solution.ipynb из ветки develop
    ↓
Предобработка ноутбука (удаление outputs/вложений)
    ↓
Анализ LLM с резервными моделями
    ↓
Публикация комментария в PR с оценкой и обратной связью
    ↓
Регистрация попытки и логирование
```

### Ключевые компоненты

**1. Обработчик вебхуков (`app.py`)**
- Прослушивает события Pull Request на GitHub
- Валидирует тип события и ветки
- Помещает запросы в очередь для обработки
- Возвращает ответы в GitHub

**2. Проверщик кода (`agentCodeReviewer.py`)**
- Загружает системный промпт и критерии оценки
- Предварительно обрабатывает Jupyter Notebook (удаляет outputs, изображения)
- Взаимодействует с LLM API с механизмом резервирования
- Обрабатывает ограничения скорости и ошибки длины контекста

**3. Менеджер активности (`check_activity.py`)**
- Отслеживает ежедневные попытки на репозиторий
- Применяет ограничения на запросы в минуту и в день
- Управляет счетчиками попыток с сбросом по дате

**4. Система email-оповещений (`send_alert_to_email.py`)**
- Отправляет уведомления об ошибках администраторам
- Логирует сбои и исключения системы

## 📊 Ограничение запросов

Агент реализует несколько уровней ограничения запросов:

| Тип ограничения | Конфигурация | Значение по умолчанию |
|-----------------|--------------|----------------------|
| **Минимальный интервал между запросами** | `MIN_INTERVAL_SECONDS` | 60 секунд |
| **Ежедневно запросов на репозиторий** | `MAX_REQUESTS_PER_DAY` | 200 |
| **Лимит команд** | `NUMBER_OF_TEAMS` | 10 |
| **Запросов на команду в день** | `NUMBER_OF_REQUEST_PER_TEAM` | 5 |
| **Эффективный дневной лимит** | Рассчитывается | 50 |

## 🧠 Промптинг LLM

Система использует структурированную структуру промптов CETO (Context-Environment-Task-Objective):

```
[CONTEXT] Образовательная платформа для курсов по ML
[ROLE] Строгий, но справедливый эксперт-рецензент
[TASK] Анализировать, оценивать, выставлять баллы, давать обратную связь
[PROCESS] Пошаговый процесс оценки
[IMPORTANT] Обязательные требования и ограничения
[OUTPUT FORMAT] Структурированный обзор с обоснованиями
[CRITERIA] Извлекается из README задания
```

### Критерии оценки

Агент оценивает студенческие работы по критериям, извлеченным из README.md:

1. **Анализирует задание:** Выявляет задачи и подзадачи из критериев
2. **Проверяет решение:** Изучает код и ячейки разметки
3. **Оценивает каждый критерий:** Назначает баллы за каждую задачу
4. **Предоставляет обоснование:** Цитирует код и объясняет логику
5. **Вычисляет итоговый балл:** 0-10 баллов с целочисленной оценкой

**Обязательные требования:**
- Комментарии к каждому логическому блоку кода
- Письменный анализ в ячейках разметки
- Все пункты критериев должны быть выполнены

## 📤 Формат вывода

Агент публикует структурированный комментарий в Pull Request:

```markdown
### Ревью решения задания

**Задача [НОМЕР]:**
- **Задача**: [Название задачи из критериев]
- **Максимальный балл**: [X/10]
- **Полученный балл**: [Y/10]
- **Обоснование**:
  - ✅ [Правильная реализация с цитатами кода]
  - ❌ [Отсутствующие требования с цитатами кода]

**Итог**
- Оценка работы: [Z] из 10
- Краткий вердикт: [Резюме]
```

## 🔄 Интеграция с GitHub

### Настройка вебхука

Настройте вебхук GitHub для отправки событий на ваш сервер:

1. **Payload URL:** `https://ваш-сервер.com/webhook`
2. **Content Type:** `application/json`
3. **События:** `Pull request events`
4. **Секрет:** (Опционально, для верификации)

### Необходимые разрешения

Токен GitHub должен иметь доступ:
- `repo` (для частных репозиториев)
- `public_repo` (для публичных репозиториев)
- Разрешения на вебхуки и комментарии в PR

## 📚 Структура системного промпта

Системный промпт хранится в `data/systemPrompt.txt` и определяет:

- **Контекст:** Описание образовательной среды
- **Роль:** Идентичность эксперта-рецензента
- **Задача:** Цели оценки
- **Процесс:** Пошаговый рабочий процесс
- **Ограничения:** Обязательные требования
- **Формат вывода:** Структура ответа
- **Заполнитель критериев:** Извлекается из README

## 🐛 Обработка ошибок

Агент обрабатывает различные сценарии ошибок:

1. **Ограничения LLM:** Автоматические повторные попытки с задержкой
2. **Превышение длины контекста:** Уведомляет пользователя о необходимости уменьшить размер ноутбука
3. **Неверный репозиторий:** Проверяет существование репозитория
4. **Отсутствующие файлы:** Проверяет наличие README и solution.ipynb
5. **Сбои API:** Переключение на резервные модели
6. **Ошибки обработки:** Отправка email-алертов администраторам

## 📈 Мониторинг

Система логирует:
- Время обработки запросов
- Используемую модель LLM
- Оценку токенов
- Детали ошибок
- Попытки активности
- Активность репозиториев
