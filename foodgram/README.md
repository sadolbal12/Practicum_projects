# Foodgram

[![Main Foodgram workflow](https://github.com/sadolbal12/foodgram/actions/workflows/main.yml/badge.svg)](https://github.com/sadolbal12/foodgram/actions/workflows/main.yml)

Сервис публикации рецептов: подписки на авторов, избранное, список покупок с выгрузкой ингредиентов, REST API и React-интерфейс.

**Проект на сервере:** [https://krutoikitigramm.hopto.org](https://krutoikitigramm.hopto.org)

**Документация API:** [https://krutoikitigramm.hopto.org/api/docs/](https://krutoikitigramm.hopto.org/api/docs/)

**Автор:** Сергей ([GitHub](https://github.com/sadolbal12))

---

## Технологии

| Часть | Стек |
|-------|------|
| Backend | Python 3.12, Django 5, DRF, Djoser, PostgreSQL |
| Frontend | React (сборка в Docker-образ gateway) |
| Инфраструктура | Docker, nginx, Gunicorn, GitHub Actions |

На продакшене три контейнера: **PostgreSQL**, **backend (Django + Gunicorn)**, **gateway (nginx + статика фронтенда)**. Образы публикуются в Docker Hub и подтягиваются на сервер при деплое.

---

## API

Спецификация: [`docs/openapi-schema.yml`](docs/openapi-schema.yml).

Основные возможности:

- пагинация списков: `page`, `limit`;
- фильтрация рецептов: `tags`, `author`, `is_favorited`, `is_in_shopping_cart`;
- авторизация: `POST /api/auth/token/login/`, токен в заголовке `Authorization: Token <key>`;
- аватар: `PUT /api/users/me/avatar/` (base64 в поле `avatar`; в попапе фронта допустимы расширения **.jpg** и **.png**, не `.jpeg`);
- список покупок: `GET /api/recipes/download_shopping_cart/` (файл `.txt`).

---

## Локальный запуск (Docker)

1. Клонируйте репозиторий и перейдите в каталог проекта.

2. Создайте `.env` из примера и при необходимости отредактируйте:

```bash
cp .env.example .env
```

3. Запустите контейнеры:

```bash
docker compose up -d --build
```

4. Выполните миграции и загрузку данных:

```bash
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py load_ingredients_and_tags
docker compose exec backend python manage.py load_demo_data
```

5. Откройте в браузере: [http://localhost:8080](http://localhost:8080)

Админка: [http://localhost:8080/admin/](http://localhost:8080/admin/)

### Учётные записи для проверки (команда `load_demo_data`)

Вход на сайте — **по email** (не по username), как в форме авторизации.

| Email | Пароль | Роль |
|-------|--------|------|
| admin@example.ru | 12345 | суперпользователь, админка `/admin/` |
| chef@example.ru | foodgram123 | обычный пользователь |
| user@example.ru | foodgram123 | обычный пользователь |

На продакшене пользователи создаются автоматически при деплое (CI).

---

## Деплой на сервер

Деплой выполняется автоматически при push в ветку `main` (GitHub Actions):

1. flake8 и тесты;
2. сборка образа **backend** (при изменениях в `backend/`);
3. сборка образа **gateway** (при изменениях в `frontend/`, `nginx/`, `docs/`);
4. SSH-деплой: `pull`, `up`, `migrate`, `collectstatic`, `load_ingredients_and_tags`, `load_demo_data`.

Секреты в репозитории: `DOCKER_USERNAME`, `DOCKER_PASSWORD`, `SERVER_IP`, `SERVER_USER`, `SSH_PRIVATE_KEY`, при необходимости Telegram.

На сервере внешний nginx (SSL) проксирует трафик на контейнер gateway (`127.0.0.1:8080`).

**После push в `main` ручные действия на сервере не требуются**, если CI прошёл успешно.

Если после деплоя вход не работает, на сервере выполните вручную (пересоздаст пароли):

```bash
cd foodgram
sudo docker compose -f docker-compose.production.yml exec -T backend python manage.py load_demo_data
```

---

## Структура проекта

```
foodgram/
├── backend/          # Django-приложение
├── frontend/         # React (собирается в образ gateway)
├── nginx/            # Конфигурация и Dockerfile gateway
├── docs/             # OpenAPI и ReDoc
├── data/             # CSV ингредиентов (резерв)
├── docker-compose.yml
└── docker-compose.production.yml
```

---

## Management-команды

| Команда | Назначение |
|---------|------------|
| `load_ingredients_and_tags` | Теги и ингредиенты из `backend/data/ingredients.json` |
| `load_demo_data` | Тестовые пользователи (для проверки входа) |

---

## Проверка API

Коллекция Postman: [`postman_collection/`](postman_collection/).
