<div align="center" markdown>

<p align="center">
    <u><b>ENGLISH</b></u> •
    <a href="https://github.com/gvarch1r/remnatgseller/blob/main/README.ru_RU.md"><b>РУССКИЙ</b></a>
</p>

# RemnatgSeller

**Telegram bot for selling VPN subscriptions, integrated with Remnawave.**

[![Static Badge](https://img.shields.io/badge/Telegram-white?style=social&logo=Telegram&logoColor=blue&logoSize=auto&labelColor=white&link=https%3A%2F%2Ft.me%2Fremna_shop)](https://t.me/remna_shop)
[![Static Badge](https://img.shields.io/badge/Remnawave-white?style=social&logo=Telegram&logoColor=blue&logoSize=auto&labelColor=white&link=https%3A%2F%2Ft.me%2Fremnawave)](https://t.me/+xQs17zMzwCY1NzYy)
![GitHub Repo stars](https://img.shields.io/github/stars/gvarch1r/remnatgseller)
</div>

---

RemnatgSeller is a self-hosted Telegram bot that automates VPN subscription sales. It works with the Remnawave panel and provides a full admin dashboard right inside Telegram.

## What's included

| Module | Description |
|--------|-------------|
| **Plans** | Create plans with traffic/device limits, multi-currency pricing, squad binding, availability rules |
| **Promocodes** | Rewards: extra days, traffic, discounts, free plans. Lifetime by time or activations |
| **Broadcasts** | Mass messages by audience (plan, subscription status). Media + HTML support |
| **Referrals** | Two-level system, rewards in points or days, configurable accrual rules |
| **Payments** | Telegram Stars, YooKassa, Cryptomus, Heleket, CryptoPay, RoboKassa and more |
| **Trial** | Free trial plans with configurable limits and availability |
| **Access control** | 5 modes: full lock, open, invite-only, purchase/register restricted |
| **Statistics** | Users, transactions, subscriptions, plans, promocodes, referrals |
| **User editor** | Full profile, subscription management, roles, blocking, sync with panel |

Additional: device management, ad links, discount system, i18n, banners, MiniApp support.

---

## Installation

**Requirements:** Ubuntu/Debian, 2+ GB RAM, 4+ GB recommended, [Docker](https://docs.docker.com/get-started/get-docker/)

> [!WARNING]
> **Remnawave 2.3.x–2.6.4** supported. For 2.6.x, use the bundled `remnapy-production` (see `pyproject.toml`).

### 1. Clone and setup

```bash
mkdir /opt/remnatgseller && cd /opt/remnatgseller
```

Download configs:

- **External panel** (bot on separate server):
  ```bash
  curl -o docker-compose.yml https://raw.githubusercontent.com/gvarch1r/remnatgseller/refs/heads/main/docker-compose.prod.external.yml
  ```
- **Internal panel** (same server):
  ```bash
  curl -o docker-compose.yml https://raw.githubusercontent.com/gvarch1r/remnatgseller/refs/heads/main/docker-compose.prod.internal.yml
  ```

```bash
curl -o .env https://raw.githubusercontent.com/gvarch1r/remnatgseller/refs/heads/main/.env.example
```

### 2. Configure .env

Generate secrets:

```bash
sed -i "s|^APP_CRYPT_KEY=.*|APP_CRYPT_KEY=$(openssl rand -base64 32 | tr -d '\n')|" .env && sed -i "s|^BOT_SECRET_TOKEN=.*|BOT_SECRET_TOKEN=$(openssl rand -hex 64 | tr -d '\n')|" .env
sed -i "s|^DATABASE_PASSWORD=.*|DATABASE_PASSWORD=$(openssl rand -hex 24 | tr -d '\n')|" .env && sed -i "s|^REDIS_PASSWORD=.*|REDIS_PASSWORD=$(openssl rand -hex 24 | tr -d '\n')|" .env
```

Edit `.env` and set: `APP_DOMAIN`, `BOT_TOKEN`, `BOT_DEV_ID`, `BOT_SUPPORT_USERNAME`, `REMNAWAVE_HOST`, `REMNAWAVE_TOKEN`, `REMNAWAVE_WEBHOOK_SECRET`.

> [!IMPORTANT]
> Configure webhook in Remnawave panel `.env`:
> ```
> WEBHOOK_ENABLED=true
> WEBHOOK_URL=https://your-bot-domain.com/api/v1/remnawave
> ```

### 3. Run

```bash
docker compose up -d && docker compose logs -f -t
```

### 4. Reverse proxy

Forward `https://your-domain/api/v1` → `http://remnatgseller:5000`
See [Remnawave reverse proxy docs](https://docs.rw/docs/install/reverse-proxies/) for examples.

### 5. Upgrade

```bash
cd /opt/remnatgseller && docker compose pull && docker compose down && RESET_ASSETS=true docker compose up -d && docker compose logs -f
```

`RESET_ASSETS=true` backs up old assets to `*.bak` and applies new ones.

---

## Customization

**Banners:** `/opt/remnatgseller/assets/banners/(locale)/` — formats: jpg, png, gif, webp. Keep `default.jpg`.

**Translations:** `/opt/remnatgseller/assets/translations/(locale)/` — edit and restart container.
