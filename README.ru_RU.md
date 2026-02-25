<div align="center" markdown>

<p align="center">
    <a href="https://github.com/gvarch1r/remnatgseller/blob/main/README.md"><b>ENGLISH</b></a> •
    <u><b>РУССКИЙ</b></u>
</p>

# RemnatgSeller

**Telegram-бот для продажи VPN-подписок, интегрированный с Remnawave.**

[![Static Badge](https://img.shields.io/badge/Telegram-white?style=social&logo=Telegram&logoColor=blue&logoSize=auto&labelColor=white&link=https%3A%2F%2Ft.me%2Fremna_shop)](https://t.me/remna_shop)
[![Static Badge](https://img.shields.io/badge/Remnawave-white?style=social&logo=Telegram&logoColor=blue&logoSize=auto&labelColor=white&link=https%3A%2F%2Ft.me%2Fremnawave)](https://t.me/+xQs17zMzwCY1NzYy)
![GitHub Repo stars](https://img.shields.io/github/stars/gvarch1r/remnatgseller)
</div>

---

RemnatgSeller — бот для Telegram, который автоматизирует продажу VPN-подписок. Работает с панелью Remnawave, админка встроена прямо в Telegram.

## Что умеет

| Модуль | Описание |
|--------|----------|
| **Планы** | Тарифы с лимитами по трафику/устройствам, мультивалютные цены, привязка сквадов, правила доступности |
| **Промокоды** | Награды: дни, трафик, скидки, бесплатные планы. Срок жизни по времени или числу активаций |
| **Рассылки** | Массовые сообщения по аудитории (план, статус подписки). Медиа и HTML |
| **Рефералы** | Двухуровневая система, награды баллами или днями, настраиваемые правила |
| **Платежи** | Telegram Stars, YooKassa, Cryptomus, Heleket, CryptoPay, RoboKassa и др. |
| **Пробный период** | Пробники с настраиваемыми лимитами и доступностью |
| **Контроль доступа** | 5 режимов: полная блокировка, открытый, по приглашениям, запрет покупок/регистрации |
| **Статистика** | Пользователи, транзакции, подписки, планы, промокоды, рефералы |
| **Редактор пользователей** | Профиль, управление подпиской, роли, блокировка, синхронизация с панелью |

Дополнительно: управление устройствами, рекламные ссылки, скидки, интернационализация, баннеры, MiniApp.

---

## Установка

**Требования:** Ubuntu/Debian, 2+ ГБ ОЗУ (рекомендуется 4+), [Docker](https://docs.docker.com/get-started/get-docker/)

> [!WARNING]
> **Remnawave 2.3.x–2.6.x** поддерживается. Для 2.6.x используется папка `remnapy-production` (см. `pyproject.toml`).

### 1. Подготовка

```bash
mkdir /opt/remnatgseller && cd /opt/remnatgseller
```

Скачайте конфиги:

- **Внешняя панель** (бот на отдельном сервере):
  ```bash
  curl -o docker-compose.yml https://raw.githubusercontent.com/gvarch1r/remnatgseller/refs/heads/main/docker-compose.prod.external.yml
  ```
- **Внутренняя панель** (тот же сервер):
  ```bash
  curl -o docker-compose.yml https://raw.githubusercontent.com/gvarch1r/remnatgseller/refs/heads/main/docker-compose.prod.internal.yml
  ```

```bash
curl -o .env https://raw.githubusercontent.com/gvarch1r/remnatgseller/refs/heads/main/.env.example
```

### 2. Настройка .env

Генерация секретов:

```bash
sed -i "s|^APP_CRYPT_KEY=.*|APP_CRYPT_KEY=$(openssl rand -base64 32 | tr -d '\n')|" .env && sed -i "s|^BOT_SECRET_TOKEN=.*|BOT_SECRET_TOKEN=$(openssl rand -hex 64 | tr -d '\n')|" .env
sed -i "s|^DATABASE_PASSWORD=.*|DATABASE_PASSWORD=$(openssl rand -hex 24 | tr -d '\n')|" .env && sed -i "s|^REDIS_PASSWORD=.*|REDIS_PASSWORD=$(openssl rand -hex 24 | tr -d '\n')|" .env
```

Отредактируйте `.env`: `APP_DOMAIN`, `BOT_TOKEN`, `BOT_DEV_ID`, `BOT_SUPPORT_USERNAME`, `REMNAWAVE_HOST`, `REMNAWAVE_TOKEN`, `REMNAWAVE_WEBHOOK_SECRET`.

> [!IMPORTANT]
> В `.env` панели Remnawave укажите:
> ```
> WEBHOOK_ENABLED=true
> WEBHOOK_URL=https://ваш-домен-бота.com/api/v1/remnawave
> ```

### 3. Запуск

```bash
docker compose up -d && docker compose logs -f -t
```

### 4. Обратный прокси

Направьте `https://ваш-домен/api/v1` → `http://remnatgseller:5000`
Примеры: [документация Remnawave](https://docs.rw/docs/install/reverse-proxies/).

### 5. Обновление

```bash
cd /opt/remnatgseller && docker compose pull && docker compose down && RESET_ASSETS=true docker compose up -d && docker compose logs -f
```

`RESET_ASSETS=true` сохраняет старые ассеты в `*.bak` и подставляет новые.

---

## Кастомизация

**Баннеры:** `/opt/remnatgseller/assets/banners/(locale)/` — форматы: jpg, png, gif, webp. Файл `default.jpg` не удалять.

**Переводы:** `/opt/remnatgseller/assets/translations/(locale)/` — правки и перезапуск контейнера.
