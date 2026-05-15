# SubSpace — платформа для публикации платного контента

SubSpace — это веб-платформа, где авторы могут публиковать статьи и видео, продавать доступ к контенту через разовую подписку, а пользователи — покупать подписку через Stripe и получать доступ к эксклюзивным материалам.
## Функциональность

- Регистрация и аутентификация по номеру телефона (с подтверждением через SMS-код пока в консоли).
- Разграничение доступа: бесплатный контент доступен всем, платный — только авторизованным пользователям с активной подпиской.
- Интеграция со Stripe (подписка, отмена подписки, вебхуки для подтверждения оплаты).
- Управление контентом (CRUD через админку и API).
- Асинхронные задачи через Celery.
- API на Django REST Framework (JWT-авторизация).
- Полноценный CI/CD через GitHub Actions (тесты, сборка Docker-образов, деплой на сервер).
- Документация API — Swagger/ReDoc.

## Технологии

- **Backend:** Django, Django REST Framework, Celery, PostgreSQL, Redis
- **Frontend:** Bootstrap 5 (шаблоны), HTML, CSS
- **Платежи:** Stripe (Checkout Sessions, Webhooks)
- **Контейнеризация:** Docker, Docker Compose
- **CI/CD:** GitHub Actions
- **Деплой:** VPS (Yandex Cloud), Nginx, Gunicorn

## Локальный запуск (без Docker)
1. Клонируй репозиторий:
    ```commandline
   git clone https://github.com/whale-inv/subspace.git
   cd subspace
    ```
2. Установи зависимости:  
   `poetry install`
3. Создай файл `.env` (скопируй `.env.example` и заполни).
4. Выполни миграции и собери статику:
    ```
    python manage.py migrate
    python manage.py collectstatic
    ```
5. Запусти сервер:
```
python manage.py runserver
```
## Запуск через Docker (локально)
```
docker-compose up --build
```
После запуска:
* Сайт будет доступен по адресу `http://localhost`
* Админка — `http://localhost/admin`
* API — `http://localhost/api/`

## Деплой на сервер (CI/CD)
Проект настроен на автоматический деплой при пуше в ветку main с помощью GitHub Actions.
1. В репозитории должны быть настроены секреты:
   * `DOCKER_USERNAME`, `DOCKER_PASSWORD`
   * `SERVER_HOST`, `SERVER_USER`, `SSH_PRIVATE_KEY`
2. При пуше в `main` автоматически:
   * Запускаются тесты.
   * Собираются Docker-образы.
   * Образы пушатся в Docker Hub.
   * На сервере выполняются `docker-compose pull` и `docker-compose up -d`.

На сервере выполняются docker-compose pull и docker-compose up -d.

## Документация API
После запуска проекта документация доступна по адресам:

* Swagger UI: `/swagger/`
* ReDoc: `/redoc/`