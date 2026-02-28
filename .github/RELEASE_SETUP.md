# Настройка релизов (Create GitHub Release)

Чтобы шаг «Create GitHub Release» в workflow работал, нужен Personal Access Token (PAT) — `GITHUB_TOKEN` в некоторых случаях не имеет прав на обновление релизов.

## 1. Создать PAT

1. GitHub → **Settings** → **Developer settings** → **Personal access tokens** → **Tokens (classic)**
2. **Generate new token (classic)**
3. Название: `remnatgseller-release`
4. Срок: на выбор (90 дней или без срока)
5. Права: включить **repo** (полный доступ к репозиторию)
6. **Generate token** и скопировать токен

## 2. Добавить секрет в репозиторий

1. Репозиторий → **Settings** → **Secrets and variables** → **Actions**
2. **New repository secret**
3. Name: `GH_PAT`
4. Value: вставить скопированный токен
5. **Add secret**

После этого workflow сможет обновлять релизы.
