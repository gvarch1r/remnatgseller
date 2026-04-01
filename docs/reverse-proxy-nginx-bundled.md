# Nginx reverse proxy (bundled)

Простая схема: **Nginx на том же сервере**, что и Remnawave Panel, проксирует HTTPS на контейнер бота. Структура как в [официальном гайде Remnashop — Nginx bundled](https://remnashop.mintlify.app/docs/en/reverse-proxies/nginx/bundled), адаптировано под **[gvarch1r/remnatgseller](https://github.com/gvarch1r/remnatgseller)**.

> **Bundled** — имеется в виду установка Nginx рядом со стеком панели (типично `/opt/remnawave/nginx`).

> **Важно:** Nginx и TLS для панели уже должны быть настроены; ниже добавляется только то, что нужно для домена **бота**.

---

## 1. Сертификат для домена бота

Выпустите сертификат (замените `BOT_DOMAIN` на домен из `APP_DOMAIN`, без `https://`):

```bash
acme.sh --issue --standalone -d 'BOT_DOMAIN' \
  --key-file /opt/remnawave/nginx/botdomain_privkey.key \
  --fullchain-file /opt/remnawave/nginx/botdomain_fullchain.pem \
  --alpn --tlsport 8443
```

Пути к ключам можно взять другие — главное, чтобы совпали с `nginx.conf` и volume’ами в compose Nginx.

---

## 2. Сеть Docker: Nginx и бот должны видеть друг друга

Имя **`remnatgseller`** резолвится только если контейнер бота подключён к **той же** сети, что и `remnawave-nginx` (обычно `remnawave-network`).

Проверка:

```bash
docker network inspect remnawave-network --format '{{range .Containers}}{{.Name}} {{end}}'
```

Должны быть и `remnawave-nginx`, и `remnatgseller` (или как у вас назван контейнер сервиса бота).

Стек бота поднимайте **до** или **вместе** с Nginx, чтобы имя появилось в DNS:

```bash
cd /opt/remnatgseller && docker compose up -d
```

---

## 3. Server block для домена бота

Откройте конфиг:

```bash
cd /opt/remnawave/nginx && nano nginx.conf
```

**Не подставляйте** для бота классический `upstream remnatgseller { server remnatgseller:5000; }`: Nginx резолвит хост **при старте**. Если бот ещё не в сети или контейнер выключен — получите `host not found in upstream "remnatgseller:5000"` и контейнер Nginx уйдёт в рестарт.

Используйте **`proxy_pass` с переменной** и встроенный DNS Docker **`127.0.0.11`** — резолвинг при запросе, Nginx стартует даже если бот поднимется позже.

В **конец** `nginx.conf` добавьте `server` (подставьте `BOT_DOMAIN`):

```nginx
server {
    server_name BOT_DOMAIN;

    listen 443 ssl;
    listen [::]:443 ssl;
    http2 on;

    location /api/v1 {
        resolver 127.0.0.11 valid=10s ipv6=off;
        set $remnatgseller_upstream http://remnatgseller:5000;
        proxy_http_version 1.1;
        proxy_pass $remnatgseller_upstream;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Port $server_port;

        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    ssl_protocols          TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384:DHE-RSA-CHACHA20-POLY1305;

    ssl_session_timeout 1d;
    ssl_session_cache shared:MozSSL:10m;
    ssl_session_tickets    off;
    ssl_certificate "/etc/nginx/ssl/botdomain_fullchain.pem";
    ssl_certificate_key "/etc/nginx/ssl/botdomain_privkey.key";
    ssl_trusted_certificate "/etc/nginx/ssl/botdomain_fullchain.pem";

    ssl_stapling           on;
    ssl_stapling_verify    on;
    resolver               1.1.1.1 1.0.0.1 8.8.8.8 8.8.4.4 208.67.222.222 208.67.220.220 valid=60s;
    resolver_timeout       2s;

    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_buffers 16 8k;
    gzip_http_version 1.1;
    gzip_min_length 256;
    gzip_types
        application/atom+xml
        application/geo+json
        application/javascript
        application/x-javascript
        application/json
        application/ld+json
        application/manifest+json
        application/rdf+xml
        application/rss+xml
        application/xhtml+xml
        application/xml
        font/eot
        font/otf
        font/ttf
        image/svg+xml
        text/css
        text/javascript
        text/plain
        text/xml;
}
```

Префикс **`/api/v1`** закрывает и вебхук панели (`/api/v1/remnawave`), и Telegram (`/api/v1/telegram`), см. константы в коде бота.

---

## 4. Монтирование сертификатов в контейнер Nginx

В `docker-compose` сервиса Nginx панели добавьте volume’ы для файлов бота (если их ещё нет).

**Важно:** у **цепочки** и **ключа** должны быть **разные** пути **внутри контейнера**. Нельзя монтировать два файла в один и тот же путь — сработает только последний mount.

Пример, если acme.sh сохранил файлы как `botdomain_fullchain.pem` и `botdomain_privkey.key`:

```yaml
services:
  remnawave-nginx:
    image: nginx:1.28
    container_name: remnawave-nginx
    hostname: remnawave-nginx
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro
      - ./fullchain.pem:/etc/nginx/ssl/fullchain.pem:ro
      - ./privkey.key:/etc/nginx/ssl/privkey.key:ro
      - ./botdomain_fullchain.pem:/etc/nginx/ssl/botdomain_fullchain.pem:ro
      - ./botdomain_privkey.key:/etc/nginx/ssl/botdomain_privkey.key:ro
    restart: always
    ports:
      - '0.0.0.0:443:443'
    networks:
      - remnawave-network
```

Если файлы названы с доменом (например `test.bot.vpn.supn.tech_fullchain.pem`), всё равно монтируйте их в **два разных** файла в контейнере — те же, что в `server` блоке для бота в `nginx.conf`:

```yaml
      - ./test.bot.vpn.supn.tech_fullchain.pem:/etc/nginx/ssl/botdomain_fullchain.pem:ro
      - ./test.bot.vpn.supn.tech_privkey.key:/etc/nginx/ssl/botdomain_privkey.key:ro
```

Пути слева — относительно каталога, где лежит compose Nginx (часто `/opt/remnawave/nginx`).

---

## 5. Перезапуск

Сначала бот (чтобы в `remnawave-network` появился DNS-имя `remnatgseller`), затем Nginx:

```bash
cd /opt/remnatgseller && docker compose up -d && docker compose logs -f -t
```

```bash
cd /opt/remnawave/nginx && docker compose up -d && docker compose logs -f
```

Если в `nginx.conf` уже используете вариант с **`resolver 127.0.0.11`** и **`proxy_pass $remnatgseller_upstream`**, порядок менее критичен, но контейнер бота всё равно должен быть в **той же** сети.

В `.env` панели вебхук должен указывать на этот домен, например:

`WEBHOOK_URL=https://BOT_DOMAIN/api/v1/remnawave`

### `host not found in upstream "remnatgseller:5000"`

1. Уберите блок `upstream remnatgseller { ... }` и `proxy_pass http://remnatgseller` — замените на конфиг из **§3** (переменная + `resolver 127.0.0.11`).
2. Убедитесь, что сервисы бота в compose подключены к `remnawave-network` и контейнер запущен:  
   `docker ps | grep remnatgseller`

### `cannot load certificate "…/botdomain_fullchain.pem" … Expecting: TRUSTED CERTIFICATE`

На **хосте** в каталоге с compose Nginx файл цепочки не PEM или пустой (нет строки `-----BEGIN CERTIFICATE-----`). Проверка:

```bash
cd /opt/remnawave/nginx
head -3 botdomain_fullchain.pem
ls -la botdomain_fullchain.pem botdomain_privkey.key
```

Исправьте volume в compose (слева — реальный путь к fullchain), либо скопируйте выданные acme/cerbot файлы в `botdomain_fullchain.pem` / `botdomain_privkey.key` и перезапустите Nginx. Нельзя монтировать два разных файла в один путь внутри контейнера.

Предупреждение **`ssl_stapling` ignored, no OCSP responder** на старом сертификате обычно безопасно; при желании отключите `ssl_stapling` / `ssl_stapling_verify` в том `server`, где сертификат без OCSP URL.

---

## Ссылки

- Оригинал по структуре: [Remnashop — Nginx bundled](https://remnashop.mintlify.app/docs/en/reverse-proxies/nginx/bundled)
- Установка бота: [docs/installation.md](installation.md)
- Репозиторий: [github.com/gvarch1r/remnatgseller](https://github.com/gvarch1r/remnatgseller)
