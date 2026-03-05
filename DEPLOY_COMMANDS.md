# Команды для push и деплоя

## 1. Git — push на GitHub (только вы как контрибьютор)

```powershell
cd /path/to/remnatgseller

# Убедиться, что автор — вы (для Contributors)
git config user.name "gvarch1r"
git config user.email "gvarch1r@gmail.com"

# Добавить все изменения
git add -A

# Коммит
git commit -m "feat: промокоды, FAQ, локации, быстрый старт, брендинг"

# Push
git push origin main
```

## 2. Сборка и деплой образа (GitHub Actions)

После `git push` образ **не** пересоберётся автоматически. Сборка запускается при:

- **Push тега** (v1.0.0, v2.0.0 и т.п.):
  ```powershell
  git tag v1.1.0
  git push origin v1.1.0
  ```

- **Ручной запуск** workflow:
  - GitHub → Actions → "Remnatgseller - Release" → Run workflow

## 3. Деплой на сервер

```bash
cd /opt/remnatgseller

# Обновить compose и .env (если ещё не сделано)
curl -sO https://raw.githubusercontent.com/gvarch1r/remnatgseller/main/docker-compose.prod.internal.yml
# или: cp docker-compose.prod.internal.yml docker-compose.yml

# Обновить образ и перезапустить
docker compose pull
docker compose down
RESET_ASSETS=true docker compose up -d

# Логи
docker compose logs -f
```

## 4. Локальная сборка (без GitHub Actions)

```bash
cd /opt/remnatgseller
git clone https://github.com/gvarch1r/remnatgseller.git /opt/remnatgseller-src
cd /opt/remnatgseller-src
cp docker-compose.prod.internal.yml ../remnatgseller/docker-compose.yml
cp .env.example ../remnatgseller/.env
cd ../remnatgseller
docker compose -f docker-compose.yml -f ../remnatgseller-src/docker-compose.build.yml up -d --build
```
