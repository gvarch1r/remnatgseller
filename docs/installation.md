# Установка remnatgseller

Краткий гайд по развёртыванию **Remnashop** из репозитория [gvarch1r/remnatgseller](https://github.com/gvarch1r/remnatgseller), по шагам аналогично [официальной инструкции Remnashop](https://remnashop.mintlify.app/docs/en/install/installation).

Перед началом проверьте требования к серверу, Docker и доменам (см. [документацию Remnashop — requirements](https://remnashop.mintlify.app/install/requirements) и [переменные окружения](https://remnashop.mintlify.app/install/environment-variables)).

---

## Установка Docker

Если Docker ещё не установлен:

```bash
sudo curl -fsSL https://get.docker.com | sh
```

Убедитесь, что работает `docker compose` (plugin или standalone `docker-compose`).

---

## Вариант A: бот и панель на одном сервере

Бот подключается к Remnawave по **внутренней Docker-сети** (имя сервиса панели, например `remnawave`).

### Шаг 1. Каталог проекта

```bash
sudo mkdir -p /opt/remnatgseller && cd /opt/remnatgseller
```

### Шаг 2. Файлы `docker-compose` и `.env`

```bash
curl -o .env https://raw.githubusercontent.com/gvarch1r/remnatgseller/main/.env.example
curl -o docker-compose.yml https://raw.githubusercontent.com/gvarch1r/remnatgseller/main/docker-compose.prod.internal.yml
```

### Шаг 2a. Сеть Docker (если ещё не создана)

В `docker-compose.prod.internal.yml` используется внешняя сеть **`remnawave-network`** (та же, что у стека панели). Создайте её один раз, если панель ещё не создала:

```bash
docker network create remnawave-network
```

Если панель уже запущена и сеть есть — команду не дублируйте.

### Шаг 3. Секреты

```bash
sed -i "s|^APP_CRYPT_KEY=.*|APP_CRYPT_KEY=$(openssl rand -base64 32 | tr -d '\n')|" .env
sed -i "s|^BOT_SECRET_TOKEN=.*|BOT_SECRET_TOKEN=$(openssl rand -hex 64 | tr -d '\n')|" .env
sed -i "s|^DATABASE_PASSWORD=.*|DATABASE_PASSWORD=$(openssl rand -hex 24 | tr -d '\n')|" .env
sed -i "s|^REDIS_PASSWORD=.*|REDIS_PASSWORD=$(openssl rand -hex 24 | tr -d '\n')|" .env
```

### Шаг 4. Настройка `.env`

Откройте файл и заполните значения `change_me`:

```bash
nano .env
```

Минимально:

| Переменная | Описание |
|------------|----------|
| `APP_DOMAIN` | Домен бота **без** `https://` и **без** слэша в конце |
| `APP_CRYPT_KEY` | Уже может быть проставлен шагом 3 |
| `BOT_TOKEN` | Токен от [@BotFather](https://t.me/BotFather) |
| `BOT_SECRET_TOKEN` | Уже может быть проставлен шагом 3 |
| `BOT_OWNER_ID` | Telegram user id владельца |
| `BOT_SUPPORT_USERNAME` | Username поддержки **без** `@` |
| `REMNAWAVE_HOST` | Обычно `remnawave` — Docker-имя сервиса панели в общей сети |
| `REMNAWAVE_TOKEN` | API token панели (Settings → API Tokens) |
| `REMNAWAVE_WEBHOOK_SECRET` | Должен совпасть с `WEBHOOK_SECRET_HEADER` в `.env` панели |
| `DATABASE_PASSWORD` | Уже может быть проставлен шагом 3 |

Опционально из `.env.example`: `DATABASE_HOST`, `REDIS_HOST`, пароль Redis и др., если отличаются от умолчаний в compose.

**Панель Remnawave 2.7+:** клиент в образе подтягивается из [gvarch1r/remnapi](https://github.com/gvarch1r/remnapi) при сборке; для готового образа `ghcr.io` используйте актуальный тег релиза.

Если доступ к API панели только через reverse-proxy (например eGames) и нужна cookie — см. `REMNAWAVE_COOKIE` в `.env.example` и [wiki eGames](https://wiki.egam.es/ru/troubleshooting/common-issues/).

### Шаг 5. Вебхук с панели на бота

На сервере панели (`/opt/remnawave` или ваш путь) в `.env` панели:

```env
WEBHOOK_ENABLED=true
WEBHOOK_URL=https://ВАШ_ДОМЕН_БОТА/api/v1/remnawave
```

Скопируйте значение `WEBHOOK_SECRET_HEADER` в `REMNAWAVE_WEBHOOK_SECRET` бота.

Перезапустите панель:

```bash
cd /opt/remnawave && docker compose up -d
```

После настройки HTTPS на домене бота (см. [reverse-proxy-nginx-bundled.md](reverse-proxy-nginx-bundled.md)) в Telegram можно выставить вебхук на `https://<APP_DOMAIN>/api/v1/telegram` (путь формируется из кода бота).

### Шаг 6. Запуск бота

```bash
cd /opt/remnatgseller && docker compose up -d && docker compose logs -f -t
```

По умолчанию контейнер слушает **127.0.0.1:5000** — наружу выведите только через **reverse proxy** с HTTPS (Caddy/Nginx). **Nginx на том же сервере, что панель:** см. [docs/reverse-proxy-nginx-bundled.md](reverse-proxy-nginx-bundled.md). Общий обзор: [reverse proxies — Remnashop](https://remnashop.mintlify.app/docs/en/reverse-proxies).

---

## Вариант B: бот и панель на разных серверах

Бот ходит к панели по **публичному HTTPS** (домен или IP с валидным TLS — см. замечание про `verify` в клиенте).

### Шаги 1–3

Как в варианте A, но compose-файл другой:

```bash
sudo mkdir -p /opt/remnatgseller && cd /opt/remnatgseller
curl -o .env https://raw.githubusercontent.com/gvarch1r/remnatgseller/main/.env.example
curl -o docker-compose.yml https://raw.githubusercontent.com/gvarch1r/remnatgseller/main/docker-compose.prod.external.yml
```

Сеть **тоже** `remnawave-network` с `external: true` — создайте при необходимости:

```bash
docker network create remnawave-network
```

(Она нужна контейнерам бота между собой; к панели на другом хосте бот обращается по `REMNAWAVE_HOST`.)

Сгенерируйте секреты теми же командами `sed` + `openssl`, что в варианте A.

### Шаг 4. `.env`

Вместо `REMNAWAVE_HOST=remnawave` укажите **домен панели без схемы и без слэша**, например:

```env
REMNAWAVE_HOST=panel.example.com
```

Остальные поля — как в варианте A. Токен и секрет вебхука по-прежнему должны совпадать с панелью.

### Шаг 5–6

Вебхук панели: `https://ВАШ_ДОМЕН_БОТА/api/v1/remnawave` → перезапуск панели → `docker compose up -d` в `/opt/remnatgseller` → reverse proxy на бота.

---

## Локальная сборка образа вместо GHCR

Если нужен образ с вашими правками исходников, замените в скачанном `docker-compose.yml` у сервисов блок `image: ghcr.io/...` на:

```yaml
build:
  context: .
  dockerfile: Dockerfile
```

и положите рядом клон репозитория (не только `curl` одного yml). Либо используйте готовый [docker-compose.local.yml](https://github.com/gvarch1r/remnatgseller/blob/main/docker-compose.local.yml) из клона.

---

## Полезные ссылки

- Репозиторий бота: [github.com/gvarch1r/remnatgseller](https://github.com/gvarch1r/remnatgseller)
- Python SDK (OpenAPI / совместимость с remnapy): [github.com/gvarch1r/remnapi](https://github.com/gvarch1r/remnapi)
- Документация Remnawave: [docs.rw](https://docs.rw/docs)
- Установка (образец структуры): [remnashop.mintlify.app — Installation](https://remnashop.mintlify.app/docs/en/install/installation)
