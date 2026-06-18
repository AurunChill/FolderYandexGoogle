# ObsidianYandexGoogle

**Русский** · [English](#english)

Простой бэкап Obsidian-vault (или любой папки) на **Yandex Disk** и/или **Google Drive** с сохранением структуры папок. Один Python-скрипт + интерактивный launcher.

- Заливает весь vault в одноимённую структуру на облаке.
- **Инкрементально**: файл того же размера на облаке пропускается — повторный бэкап быстрый.
- Два облака на выбор: Яндекс, Google или оба.
- Ничего лишнего: чистый Python (`yadisk` + Google Drive API), без сторонних бинарников.

> Бэкап-зеркало, а не система версий: перезапись затирает прежнюю версию, удалённые локально файлы на облаке **не** удаляются.

## Установка и запуск

```bash
git clone https://github.com/AurunChill/ObsidianYandexGoogle.git
cd ObsidianYandexGoogle
cp config.example.json config.json     # заполнить своими данными (см. ниже)
./backup.sh
```

`backup.sh` при первом запуске сам создаёт `venv`, ставит зависимости и показывает меню:

```
1) Яндекс Диск
2) Google Drive
3) Оба
```

Авторизация запрашивается **один раз** (токены сохраняются локально):
- **Яндекс** — скрипт даст ссылку, подтвердишь доступ, вставишь код.
- **Google** — откроется браузер для подтверждения.

Запускать с машины, где есть браузер (для первичного входа), не headless.

## Настройка доступов

### Yandex Disk
1. https://oauth.yandex.ru/ → создать приложение.
2. Redirect URI: `https://oauth.yandex.ru/verification_code`.
3. Доступы «Яндекс.Диск REST API»: `cloud_api:disk.read`, `cloud_api:disk.write`, `cloud_api:disk.info`.
4. Вписать `client_id` и `client_secret` в `config.json` → `yandex`.

### Google Drive
1. https://console.cloud.google.com/ → создать проект.
2. **APIs & Services → Library** → включить **Google Drive API** (в том же проекте!).
3. **OAuth consent screen** → добавить свой аккаунт в **Test users**.
4. **Credentials → Create → OAuth client ID → тип Desktop app** → скопировать `client_id`/`client_secret` в `config.json` → `google`.

## config.json

```json
{
  "backup_folder": "ObsidianBackup",
  "include_obsidian": true,
  "include_git": false,
  "exclude": ["папка/которую/пропустить", "файл.tmp"],

  "yandex": {
    "client_id": "...",
    "client_secret": "...",
    "token": ""
  },
  "google": {
    "client_id": "....apps.googleusercontent.com",
    "client_secret": "..."
  }
}
```

| Поле | Назначение |
|---|---|
| `backup_folder` | имя папки бэкапа в корне каждого облака |
| `include_obsidian` | включать ли папку `.obsidian` (настройки Obsidian) |
| `include_git` | включать ли `.git` (обычно нет) |
| `exclude` | список папок/файлов (относительные пути), которые не заливать |
| `yandex.token` | заполняется автоматически после первой авторизации |

Папка с самим скриптом (`venv`, токены) из бэкапа исключается всегда.

## Использование напрямую (без меню)

```bash
venv/bin/python backup.py --target yandex
venv/bin/python backup.py --target google
venv/bin/python backup.py --target both
```

## Безопасность

`config.json`, `token.json`, `credentials.json`, `venv/` содержат секреты/окружение и занесены в `.gitignore` — **не коммить их и не публикуй**. Токены дают доступ к твоему Диску/Drive, храни их только локально.

## Ограничения

- Сравнение файлов идёт **по размеру**: правка, не изменившая размер байт-в-байт, не зальётся.
- Зеркального удаления нет (удалённые локально файлы остаются на облаке).
- Google использует scope `drive.file` — скрипт видит и трогает только файлы, созданные им самим.

## Лицензия

[MIT](LICENSE) © AurunChill

---

# English

[Русский](#obsidianyandexgoogle) · **English**

Simple backup of an Obsidian vault (or any folder) to **Yandex Disk** and/or **Google Drive**, preserving the folder structure. One Python script + an interactive launcher.

- Uploads the whole vault into the same structure on the cloud.
- **Incremental**: a file with the same size already on the cloud is skipped — repeat backups are fast.
- Two clouds to choose from: Yandex, Google, or both.
- Pure Python (`yadisk` + Google Drive API), no external binaries.

> It's a backup mirror, not a version history: overwrites replace the previous version, and files deleted locally are **not** removed from the cloud.

## Install & run

```bash
git clone https://github.com/AurunChill/ObsidianYandexGoogle.git
cd ObsidianYandexGoogle
cp config.example.json config.json     # fill in your data (see below)
./backup.sh
```

On first run `backup.sh` creates a `venv`, installs dependencies and shows a menu:

```
1) Yandex Disk
2) Google Drive
3) Both
```

Authorization is requested **once** (tokens are stored locally):
- **Yandex** — the script prints a link, you confirm access and paste the code.
- **Google** — a browser opens for consent.

Run it from a machine with a browser (for the first login), not headless.

## Configure access

### Yandex Disk
1. https://oauth.yandex.ru/ → create an app.
2. Redirect URI: `https://oauth.yandex.ru/verification_code`.
3. Scopes for "Yandex.Disk REST API": `cloud_api:disk.read`, `cloud_api:disk.write`, `cloud_api:disk.info`.
4. Put `client_id` and `client_secret` into `config.json` → `yandex`.

### Google Drive
1. https://console.cloud.google.com/ → create a project.
2. **APIs & Services → Library** → enable **Google Drive API** (in the same project!).
3. **OAuth consent screen** → add your account to **Test users**.
4. **Credentials → Create → OAuth client ID → type Desktop app** → copy `client_id`/`client_secret` into `config.json` → `google`.

## config.json

```json
{
  "backup_folder": "ObsidianBackup",
  "include_obsidian": true,
  "include_git": false,
  "exclude": ["folder/to/skip", "file.tmp"],

  "yandex": {
    "client_id": "...",
    "client_secret": "...",
    "token": ""
  },
  "google": {
    "client_id": "....apps.googleusercontent.com",
    "client_secret": "..."
  }
}
```

| Field | Meaning |
|---|---|
| `backup_folder` | name of the backup folder at the root of each cloud |
| `include_obsidian` | whether to include the `.obsidian` folder (Obsidian settings) |
| `include_git` | whether to include `.git` (usually no) |
| `exclude` | list of folders/files (relative paths) to skip |
| `yandex.token` | filled in automatically after the first authorization |

The script's own folder (`venv`, tokens) is always excluded from the backup.

## Direct usage (no menu)

```bash
venv/bin/python backup.py --target yandex
venv/bin/python backup.py --target google
venv/bin/python backup.py --target both
```

## Security

`config.json`, `token.json`, `credentials.json`, `venv/` contain secrets/environment and are listed in `.gitignore` — **do not commit or publish them**. Tokens grant access to your Disk/Drive; keep them local only.

## Limitations

- File comparison is **by size**: an edit that doesn't change the byte size won't be re-uploaded.
- No mirror deletion (files deleted locally remain on the cloud).
- Google uses the `drive.file` scope — the script only sees and touches files it created itself.

## License

[MIT](LICENSE) © AurunChill
