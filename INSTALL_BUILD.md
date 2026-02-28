# Установка с локальной сборкой образа

Если при `docker compose up` возникает `error from registry: denied` — образ не опубликован или приватный. Соберите его локально.

## 1. Клонировать репозиторий

```bash
git clone https://github.com/gvarch1r/remnatgseller.git /opt/remnatgseller
cd /opt/remnatgseller
```

## 2. Настроить .env

```bash
cp .env.example .env
# Сгенерировать секреты:
sed -i "s|^APP_CRYPT_KEY=.*|APP_CRYPT_KEY=$(openssl rand -base64 32 | tr -d '\n')|" .env && sed -i "s|^BOT_SECRET_TOKEN=.*|BOT_SECRET_TOKEN=$(openssl rand -hex 64 | tr -d '\n')|" .env
sed -i "s|^DATABASE_PASSWORD=.*|DATABASE_PASSWORD=$(openssl rand -hex 24 | tr -d '\n')|" .env && sed -i "s|^REDIS_PASSWORD=.*|REDIS_PASSWORD=$(openssl rand -hex 24 | tr -d '\n')|" .env
```

Отредактируйте `.env`: `APP_DOMAIN`, `BOT_TOKEN`, `BOT_DEV_ID`, `BOT_SUPPORT_USERNAME`, `REMNAWAVE_HOST`, `REMNAWAVE_TOKEN`, `REMNAWAVE_WEBHOOK_SECRET`.

## 3. Собрать и запустить

```bash
docker compose -f docker-compose.prod.internal.yml -f docker-compose.build.yml up -d --build
```

## 4. Логи

```bash
docker compose -f docker-compose.prod.internal.yml -f docker-compose.build.yml logs -f -t
```

---

**Если postgres и valkey тоже дают "denied"** — возможно лимит Docker Hub. Попробуйте `docker login` (логин на hub.docker.com) или повторить позже.
