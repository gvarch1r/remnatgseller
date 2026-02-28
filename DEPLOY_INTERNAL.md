# Развёртывание RemnatgSeller на сервере с панелью (internal)

Бот и панель Remnawave на одном сервере.

## 1. Подготовка на сервере

```bash
mkdir -p /opt/remnatgseller && cd /opt/remnatgseller
```

## 2. Файлы

Скачать `docker-compose` и `.env`:

```bash
# docker-compose для internal (бот и панель на одном сервере)
curl -o docker-compose.yml https://raw.githubusercontent.com/gvarch1r/remnatgseller/main/docker-compose.prod.internal.yml

# Пример .env
curl -o .env https://raw.githubusercontent.com/gvarch1r/remnatgseller/main/.env.example
```

Или скопировать из локального репозитория:
- `docker-compose.prod.internal.yml` → `docker-compose.yml`
- `.env.example` → `.env`

**Локальная сборка:** если деплоите свой форк, измените в docker-compose `image:` на свой образ или соберите локально:
```bash
docker build -t remnatgseller:local .
# и в docker-compose: image: remnatgseller:local
```

## 3. Настройка .env

Обязательно заполнить:

| Переменная | Описание |
|------------|----------|
| `APP_DOMAIN` | Домен бота (без https://) |
| `APP_CRYPT_KEY` | `openssl rand -base64 32` |
| `BOT_TOKEN` | Токен от @BotFather |
| `BOT_SECRET_TOKEN` | `openssl rand -hex 64` |
| `BOT_DEV_ID` | Ваш Telegram ID |
| `BOT_SUPPORT_USERNAME` | Username поддержки без @ |
| `REMNAWAVE_HOST` | `remnawave` (имя контейнера панели) |
| `REMNAWAVE_TOKEN` | API-токен из панели |
| `REMNAWAVE_WEBHOOK_SECRET` | Совпадает с `WEBHOOK_SECRET_HEADER` в .env панели |
| `DATABASE_PASSWORD` | Пароль БД |
| `REDIS_PASSWORD` | Пароль Redis |

**Баннеры:** Пока дизайнер не готов — `BOT_USE_BANNERS=false`.  
Когда появятся баннеры — положить в `./assets/banners/` и `BOT_USE_BANNERS=true`.

## 4. Сеть Docker

Бот должен быть в той же сети, что и панель:

```bash
docker network ls | grep remnawave
```

Если сети нет — панель создаёт её при первом запуске. Запустите панель, затем бота.

## 5. Webhook в панели

В `.env` панели Remnawave:

```
WEBHOOK_ENABLED=true
WEBHOOK_URL=https://ваш-домен/api/v1/remnawave
```

## 6. Reverse proxy

Проксировать на бота:

```
https://ваш-домен/api/v1 -> http://remnatgseller:5000
```

**Nginx:** при установке с панелью Remnawave конфиг обычно в `/opt/remnawave/nginx/` или в папке панели. Добавьте `server`/`location` для домена бота, например:

```nginx
location /api/v1 {
    proxy_pass http://remnatgseller:5000;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

Бот должен быть в той же Docker-сети, что и Nginx/панель.

## 7. Запуск

```bash
cd /opt/remnatgseller
docker compose up -d
docker compose logs -f
```

## 8. Обновление

```bash
cd /opt/remnatgseller
docker compose pull
docker compose down
docker compose up -d
```

С `RESET_ASSETS=true` — перезаписать assets из образа (осторожно, перезатрёт кастомные переводы и баннеры).
