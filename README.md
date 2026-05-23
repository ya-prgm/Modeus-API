# 🔷 API Modeus UTMN

> **Неофициальный API для взаимодействия с системой Modeus Тюменского государственного университета**
(если заменить эндпоинты, можно использовать для любого ВУЗа)

Telegram: @ya_prgm

Telegram: @ya_prgm

Telegram: @ya_prgm

Telegram: @ya_prgm

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📋 Содержание

- [О проекте](#-о-проекте)
- [Возможности](#-возможности)
- [Быстрый старт](#-быстрый-старт)
- [Структура проекта](#-структура-проекта)
- [API Endpoints](#-api-endpoints)
  - [Аутентификация](#-1-auth)
  - [Профиль пользователя](#-2-profile)
  - [Расписание](#-3-schedule)
  - [Оценки](#-4-grades)
  - [Поиск пользователей](#-5-search)
  - [Расписание по ID](#-6-schedule-by-id)
  - [Календарь LMS](#-7-calendar)
- [Примеры использования](#-примеры-использования)
- [Обработка ошибок](#-обработка-ошибок)
- [Архитектура](#-архитектура)
- [Кэширование](#-кэширование)
- [Технические детали](#-технические-детали)
- [Лицензия](#-лицензия)

---

## 🎯 О проекте

**Modeus API** — это неофициальный REST API, разработанный для взаимодействия с системой [Modeus](https://utmn.modeus.org/) Тюменского государственного университета. Проект позволяет получать доступ к данным студентов через удобный HTTP-интерфейс. Разработан - Telegram: @ya_prgm

> ⚠️ **Внимание**: Это неофициальный проект. Используйте на свой страх и риск.

### Зачем нужен этот проект?

- **Интеграция** с внешними приложениями и сервисами
- **Автоматизация** получения расписания и оценок
- **Разработка** мобильных и веб-приложений для студентов
- **Анализ** данных учебного процесса

---

## ✨ Возможности

| Функция | Описание |
|---------|----------|
| 🔐 **Аутентификация** | Безопасный вход через учётные данные ТюмГУ |
| 👤 **Профиль** | Получение данных о студенте |
| 📅 **Расписание** | Расписание занятий с привязкой к аудиториям |
| 📊 **Оценки** | Доступ к результатам текущей сессии |
| 🔍 **Поиск** | Поиск студентов по ФИО |
| 🗓️ **Календарь** | Интеграция с LMS (Moodle) |

---

## 🚀 Быстрый старт

### Установка

```bash
# Клонирование репозитория
git clone  https://github.com/ya-prgm/Modeus-API.git
cd modeus-api

# Установка зависимостей
pip install -r requirements.txt
```

### Запуск сервера

```bash
python main.py
```

Сервер запустится на `http://localhost:5000`

### Остановка

Нажмите `Ctrl+C` в терминале

---

## 📁 Структура проекта

```
modeus-api/
├── main.py                 # Точка входа приложения
├── requirements.txt        # Зависимости Python
├── README.md              # Документация
│
├── api/                   # API маршруты
│   ├── __init__.py
│   └── routes.py          # Все endpoints
│
├── services/              # Бизнес-логика
│   ├── __init__.py
│   ├── auth.py           # Аутентификация Modeus
│   ├── profile.py        # Работа с профилем
│   ├── schedule.py       # Расписание занятий
│   ├── grades.py         # Оценки студентов
│   ├── search.py         # Поиск пользователей
│   └── calendar.py       # Интеграция с LMS
│
├── database/             # Работа с данными
│   ├── __init__.py
│   └── mmap_db.py        # Хранилище на mmap
│
└── utils/                # Утилиты
    ├── __init__.py
    └── headers.py        # HTTP заголовки
```

---

## 🔌 API Endpoints

### 🔒 1. `/auth` — Аутентификация

Аутентификация пользователя в системе Modeus и получение токена сессии.

**Метод:** `POST`  
**Content-Type:** `application/json`

#### Параметры запроса

| Параметр | Тип | Обязательно | Описание |
|----------|-----|-------------|----------|
| `login` | string | ✅ | Логин от личного кабинета ТюмГУ |
| `password` | string | ✅ | Пароль от личного кабинета |

#### Пример запроса

```bash
curl -X POST http://localhost:5000/auth \
  -H "Content-Type: application/json" \
  -d '{"login": "student@utmn.ru", "password": "secret123"}'
```

```python
import requests

response = requests.post(
    "http://localhost:5000/auth",
    json={
        "login": "student@utmn.ru",
        "password": "secret123"
    }
)
print(response.json())
```

#### Ответ успеха

```json
{
  "status": "success",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "process_time": "1.234"
}
```

| Поле | Тип | Описание |
|------|-----|----------|
| `status` | string | Статус выполнения (`success`) |
| `token` | string | Токен авторизации для последующих запросов |
| `process_time` | string | Время выполнения в секундах |

#### Обработка ошибок

```json
{
  "detail": "Invalid login or password"
}
```

| Код | Описание |
|-----|----------|
| `401` | Неверный логин или пароль |

---

### 👤 2. `/profile` — Профиль пользователя

Получение данных профиля текущего авторизованного пользователя.

**Метод:** `POST`  
**Content-Type:** `application/json`

#### Параметры запроса

| Параметр | Тип | Обязательно | Описание |
|----------|-----|-------------|----------|
| `token` | string | ✅ | Токен авторизации (полученный в `/auth`) |

#### Пример запроса

```bash
curl -X POST http://localhost:5000/profile \
  -H "Content-Type: application/json" \
  -d '{"token": "your_token_here"}'
```

```python
import requests

response = requests.post(
    "http://localhost:5000/profile",
    json={"token": "your_token_here"}
)
print(response.json())
```

#### Ответ успеха

```json
{
  "fullName": "Иванов Иван Иванович",
  "birthDate": "2001-05-15",
  "email": "student@utmn.ru",
  "phone": "+7 (912) 345-67-89",
  "specialtyCode": "09.03.01",
  "specialtyName": "Информатика и вычислительная техника",
  "profile": "ПИ",
  "learningStartDate": "2021-09-01",
  "citizenship": "Российская Федерация",
  "service": {
    "personId": "abc123",
    "studentId": "def456",
    "aprId": "ghi789",
    "academicPeriodStartDate": "2024-02-01T00:00:00.000Z",
    "academicPeriodEndDate": "2024-06-30T23:59:59.999Z"
  },
  "process_time": "0.567"
}
```

#### Обработка ошибок

```json
{
  "detail": "Invalid token"
}
```

| Код | Описание |
|-----|----------|
| `401` | Недействительный токен |
| `500` | Ошибка получения профиля |

---

### 📅 3. `/schedule` — Расписание занятий

Получение расписания занятий для текущего пользователя.

**Метод:** `POST`  
**Content-Type:** `application/json`

#### Параметры запроса

| Параметр | Тип | Обязательно | Описание |
|----------|-----|-------------|----------|
| `token` | string | ✅ | Токен авторизации |
| `date_start` | string | ✅ | Начальная дата (`YYYY-MM-DD`) |
| `date_end` | string | ✅ | Конечная дата (`YYYY-MM-DD`) |

#### Пример запроса

```bash
curl -X POST http://localhost:5000/schedule \
  -H "Content-Type: application/json" \
  -d '{
    "token": "your_token_here",
    "date_start": "2024-03-01",
    "date_end": "2024-03-31"
  }'
```

```python
import requests

response = requests.post(
    "http://localhost:5000/schedule",
    json={
        "token": "your_token_here",
        "date_start": "2024-03-01",
        "date_end": "2024-03-31"
    }
)
print(response.json())
```

#### Ответ успеха

```json
{
  "status": "success",
  "schedule": [
    {
      "day": "Пт 01.03.2024",
      "schedule": [
        {
          "name": "Программирование",
          "topic": "Лабораторная работа №5",
          "start": "09:30 - 11:05",
          "location": "310 корпус 1 (ул. Ленина, 16)"
        },
        {
          "name": "Математический анализ",
          "topic": "Практическое занятие",
          "start": "11:20 - 12:55",
          "location": "205 корпус 2 (ул. Республики, 25)"
        }
      ]
    },
    {
      "day": "Пн 04.03.2024",
      "schedule": [
        {
          "name": "Физика",
          "topic": "Лекция",
          "start": "08:00 - 09:35",
          "location": "101 ауд. (главный корпус)"
        }
      ]
    }
  ],
  "process_time": "0.892"
}
```

#### Структура ответа

| Поле | Тип | Описание |
|------|-----|----------|
| `day` | string | День недели и дата (формат: `ДД ДД.ММ.ГГГГ`) |
| `name` | string | Название дисциплины |
| `topic` | string | Тема занятия |
| `start` | string | Временной интервал (`ЧЧ:ММ - ЧЧ:ММ`) |
| `location` | string | Место проведения (`Аудитория (Адрес)`) или `Онлайн` |

---

### 📊 4. `/grades` — Оценки

Получение результатов текущего учебного периода.

**Метод:** `POST`  
**Content-Type:** `application/json`

#### Параметры запроса

| Параметр | Тип | Обязательно | Описание |
|----------|-----|-------------|----------|
| `token` | string | ✅ | Токен авторизации |

#### Пример запроса

```bash
curl -X POST http://localhost:5000/grades \
  -H "Content-Type: application/json" \
  -d '{"token": "your_token_here"}'
```

```python
import requests

response = requests.post(
    "http://localhost:5000/grades",
    json={"token": "your_token_here"}
)
print(response.json())
```

#### Ответ успеха

```json
{
  "status": "success",
  "grades": {
    "abc123def456": {
      "id": "abc123def456",
      "name": "Программирование на Python",
      "result": 85
    },
    "ghi789jkl012": {
      "id": "ghi789jkl012",
      "name": "Математический анализ",
      "result": 92
    },
    "mno345pqr678": {
      "id": "mno345pqr678",
      "name": "Линейная алгебра",
      "result": 78
    }
  },
  "process_time": "1.123"
}
```

#### Структура оценки

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | string | Уникальный идентификатор курса |
| `name` | string | Название дисциплины |
| `result` | number | Оценка (баллы) |

---

### 🔍 5. `/search` — Поиск пользователей

Поиск студентов и сотрудников по ФИО.

**Метод:** `POST`  
**Content-Type:** `application/json`

#### Параметры запроса

| Параметр | Тип | Обязательно | Описание |
|----------|-----|-------------|----------|
| `token` | string | ✅ | Токен авторизации |
| `full_name` | string | ✅ | ФИО для поиска (минимум 2 символа) |

#### Пример запроса

```bash
curl -X POST http://localhost:5000/search \
  -H "Content-Type: application/json" \
  -d '{
    "token": "your_token_here",
    "full_name": "Иванов"
  }'
```

```python
import requests

response = requests.post(
    "http://localhost:5000/search",
    json={
        "token": "your_token_here",
        "full_name": "Иванов"
    }
)
print(response.json())
```

#### Ответ успеха

```json
{
  "status": "success",
  "users": [
    {
      "fullName": "Иванов Иван Иванович",
      "personId": "person123",
      "specialtyName": "Информатика и вычислительная техника",
      "specialtyProfile": "Программная инженерия",
      "learningStartDate": "2021-09-01"
    },
    {
      "fullName": "Иванов Петр Сергеевич",
      "personId": "person456",
      "specialtyName": "Прикладная математика",
      "specialtyProfile": "Математическое моделирование",
      "learningStartDate": "2022-09-01"
    }
  ],
  "process_time": "0.345"
}
```

> 💡 Максимум возвращается 10 результатов для оптимизации автодополнения.

---

### 📋 6. `/schedule-by-id` — Расписание по ID

Получение расписания другого пользователя по его ID.

**Метод:** `POST`  
**Content-Type:** `application/json`

#### Параметры запроса

| Параметр | Тип | Обязательно | Описание |
|----------|-----|-------------|----------|
| `token` | string | ✅ | Токен авторизации |
| `date_start` | string | ✅ | Начальная дата (`YYYY-MM-DD`) |
| `date_end` | string | ✅ | Конечная дата (`YYYY-MM-DD`) |
| `person_id` | string | ✅ | ID пользователя (из поиска) |

#### Пример запроса

```bash
curl -X POST http://localhost:5000/schedule-by-id \
  -H "Content-Type: application/json" \
  -d '{
    "token": "your_token_here",
    "date_start": "2024-03-01",
    "date_end": "2024-03-31",
    "person_id": "person123"
  }'
```

```python
import requests

response = requests.post(
    "http://localhost:5000/schedule-by-id",
    json={
        "token": "your_token_here",
        "date_start": "2024-03-01",
        "date_end": "2024-03-31",
        "person_id": "person123"
    }
)
print(response.json())
```

#### Ответ

Формат аналогичен `/schedule` — возвращает расписание указанного пользователя.

---

### 🗓️ 7. `/calendar` — Календарь LMS

Получение событий календаря из системы LMS (Moodle).

**Метод:** `POST`  
**Content-Type:** `application/json`

#### Параметры запроса

| Параметр | Тип | Обязательно | Описание |
|----------|-----|-------------|----------|
| `token` | string | ✅ | Токен авторизации |
| `year` | integer | ✅ | Год (например: `2024`) |
| `month` | integer | ✅ | Месяц (1-12) |

#### Пример запроса

```bash
curl -X POST http://localhost:5000/calendar \
  -H "Content-Type: application/json" \
  -d '{
    "token": "your_token_here",
    "year": 2024,
    "month": 3
  }'
```

```python
import requests

response = requests.post(
    "http://localhost:5000/calendar",
    json={
        "token": "your_token_here",
        "year": 2024,
        "month": 3
    }
)
print(response.json())
```

#### Ответ успеха

```json
{
  "status": "success",
  "calendar": {
    "01.03.2024": [
      {
        "name": "Дедлайн по лабораторной работе",
        "full_name": "Срок сдачи ЛР №3",
        "course": "Программирование на Python",
        "event_type": "due",
        "start_time": "01 March 2024, 23:59:59",
        "module": "assignment",
        "event_url": "/mod/assign/view.php?id=123"
      }
    ],
    "05.03.2024": [
      {
        "name": "Вебинар",
        "full_name": "Онлайн-лекция",
        "course": "Математический анализ",
        "event_type": "course",
        "start_time": "05 March 2024, 14:00:00",
        "module": "webinar",
        "event_url": "/mod/webinar/view.php?id=456"
      }
    ]
  },
  "process_time": "0.678"
}
```

#### Структура события

| Поле | Тип | Описание |
|------|-----|----------|
| `name` | string | Название события |
| `full_name` | string | Полное название |
| `course` | string | Название курса |
| `event_type` | string | Тип события (`due`, `course`, `group`, etc.) |
| `start_time` | string | Дата и время начала |
| `module` | string | Модуль LMS |
| `event_url` | string | URL события |

---

## 💡 Примеры использования

### Python

```python
import requests
import json

BASE_URL = "http://localhost:5000"

class ModeusAPI:
    def __init__(self):
        self.token = None
    
    def authenticate(self, login: str, password: str):
        """Аутентификация"""
        response = requests.post(
            f"{BASE_URL}/auth",
            json={"login": login, "password": password}
        )
        data = response.json()
        self.token = data.get("token")
        return data
    
    def get_schedule(self, start: str, end: str):
        """Получить расписание"""
        if not self.token:
            raise ValueError("Необходимо сначала авторизоваться")
        
        response = requests.post(
            f"{BASE_URL}/schedule",
            json={
                "token": self.token,
                "date_start": start,
                "date_end": end
            }
        )
        return response.json()
    
    def get_grades(self):
        """Получить оценки"""
        if not self.token:
            raise ValueError("Необходимо сначала авторизоваться")
        
        response = requests.post(
            f"{BASE_URL}/grades",
            json={"token": self.token}
        )
        return response.json()

# Использование
api = ModeusAPI()

# Авторизация
auth_result = api.authenticate("student@utmn.ru", "password123")
print(f"Авторизация: {auth_result['status']}")

# Получить расписание на март
schedule = api.get_schedule("2024-03-01", "2024-03-31")
for day in schedule.get("schedule", []):
    print(f"\n{day['day']}")
    for lesson in day['schedule']:
        print(f"  {lesson['start']} - {lesson['name']}")
        print(f"  📍 {lesson['location']}")

# Получить оценки
grades = api.get_grades()
print("\n📊 Оценки:")
for course_id, data in grades.get("grades", {}).items():
    print(f"  {data['name']}: {data['result']} баллов")
```

### JavaScript / Node.js

```javascript
const axios = require('axios');

const BASE_URL = 'http://localhost:5000';

class ModeusAPI {
    constructor() {
        this.token = null;
    }

    async authenticate(login, password) {
        const response = await axios.post(`${BASE_URL}/auth`, {
            login,
            password
        });
        this.token = response.data.token;
        return response.data;
    }

    async getSchedule(start, end) {
        const response = await axios.post(`${BASE_URL}/schedule`, {
            token: this.token,
            date_start: start,
            date_end: end
        });
        return response.data;
    }

    async getGrades() {
        const response = await axios.post(`${BASE_URL}/grades`, {
            token: this.token
        });
        return response.data;
    }
}

// Использование
const api = new ModeusAPI();

async function main() {
    await api.authenticate('student@utmn.ru', 'password123');
    
    const schedule = await api.getSchedule('2024-03-01', '2024-03-31');
    console.log('📅 Расписание:', JSON.stringify(schedule, null, 2));
    
    const grades = await api.getGrades();
    console.log('📊 Оценки:', JSON.stringify(grades, null, 2));
}

main().catch(console.error);
```

---

## ⚠️ Обработка ошибок

### HTTP коды ошибок

| Код | Метод | Описание |
|-----|-------|----------|
| `400` | Все | Некорректный формат запроса |
| `401` | Все | Ошибка аутентификации (неверный токен/пароль) |
| `500` | Все | Внутренняя ошибка сервера |

### Формат ошибки

```json
{
  "detail": "Сообщение об ошибке"
}
```

### Типичные ошибки

| Ошибка | Причина | Решение |
|--------|---------|---------|
| `Invalid login or password` | Неверные учётные данные | Проверьте логин и пароль |
| `Invalid token` | Истёк или недействителен токен | Повторите авторизацию через `/auth` |
| `Profile data not found` | Не удалось получить профиль | Проверьте авторизацию |
| `Invalid date format` | Неверный формат даты | Используйте `YYYY-MM-DD` |

---

## 🏗️ Архитектура

```
                    ┌─────────────────────────────────────┐
                    │           FastAPI Application       │
                    │              (main.py)              │
                    └──────────────────┬──────────────────┘
                                       │
                    ┌──────────────────▼──────────────────┐
                    │          API Routes (routes.py)     │
                    │    POST /auth, /profile, /schedule  │
                    └──────────────────┬──────────────────┘
                                       │
        ┌───────────────────────────────┼───────────────────────────────┐
        │                               │                               │
┌───────▼────────┐            ┌────────▼────────┐            ┌────────▼────────┐
│  Auth Service   │            │ Profile Service │            │ Schedule Service│
│  (auth.py)      │            │ (profile.py)    │            │ (schedule.py)   │
└────────┬────────┘            └────────┬────────┘            └────────┬────────┘
         │                               │                               │
┌────────▼────────┐            ┌────────▼────────┐            ┌────────▼────────┐
│ Modeus API      │            │ Modeus API      │            │ Modeus API      │
│ auth.modeus.org│            │ utmn.modeus.org│            │ utmn.modeus.org │
└─────────────────┘            └─────────────────┘            └─────────────────┘
```

### Компоненты

| Компонент | Назначение |
|-----------|------------|
| **FastAPI** | Веб-фреймворк для построения REST API |
| **httpx** | Асинхронный HTTP-клиент для запросов к Modeus |
| **mmap** | Файловый кэш для хранения сессий и данных |
| **BeautifulSoup** | Парсинг SAML-ответов при аутентификации |

### Поток запроса

1. **Клиент** отправляет запрос на endpoint
2. **Routes** валидирует входные данные
3. **Service** выполняет бизнес-логику
4. **Auth Service** обеспечивает валидность токена
5. **Modeus API** возвращает данные
6. **Response** форматируется и возвращается клиенту

---

## 💾 Кэширование

Проект использует многоуровневое кэширование для оптимизации производительности:

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Memory    │ -> │   Mmap      │ -> │   Modeus    │
│   (Local)   │    │   (File)    │    │   (API)     │
└─────────────┘    └─────────────┘    └─────────────┘
     Fastest           Medium            Slowest
```

### Типы кэша

| Тип | Хранилище | Срок жизни | Назначение |
|-----|-----------|------------|------------|
| **Локальный** | RAM | Запрос | Профили, оценки |
| **Mmap** | Файл | 55 минут | Токены, сессии |
| **Modeus** | API | Неограничен | Данные расписания |

### Файлы кэша

| Файл | Содержимое |
|------|------------|
| `users.mmap` | Пользователи и токены |
| `sessions.mmap` | Активные сессии |
| `profiles.mmap` | Данные профилей |
| `grades.mmap` | Оценки студентов |

---

## 🔧 Технические детали

### Зависимости

```
fastapi>=0.100.0
uvicorn>=0.23.0
httpx>=0.24.0
pydantic>=2.0.0
beautifulsoup4>=4.12.0
```

### Конфигурация

| Параметр | Значение | Описание |
|----------|----------|----------|
| **Host** | `0.0.0.0` | Принимает соединения с любых адресов |
| **Port** | `5000` | Порт HTTP-сервера |
| **Log Level** | `DEBUG` | Уровень логирования |

### Заголовки ответа

Каждый ответ содержит заголовок `X-Process-Time` с временем выполнения запроса в секундах.

```http
HTTP/1.1 200 OK
Content-Type: application/json; charset=utf-8
X-Process-Time: 0.567
```

### Безопасность

- ✅ Токены генерируются криптографически стойким генератором
- ✅ Пароли хранятся локально для автоматического переавторизации
- ✅ Используется HTTP/2 для оптимизации соединений
- ⚠️ Рекомендуется использовать HTTPS в production

---

## 📝 Логирование

Сервер ведёт логирование всех операций:

```python
# Формат лога
%(asctime)s - %(name)s - %(levelname)s - %(message)s

# Пример
2024-03-01 12:30:45 - services.schedule - INFO - Request: POST /schedule completed in 0.892 seconds
```

### Уровни логирования

| Уровень | Использование |
|---------|---------------|
| `DEBUG` | Детальная отладка запросов |
| `INFO` | Общая информация о работе |
| `WARNING` | Предупреждения |
| `ERROR` | Ошибки выполнения |

---



<div align="center">
  <p>Сделано с ❤️ для студентов ТюмГУ</p>
  <p>2026</p>
</div>
