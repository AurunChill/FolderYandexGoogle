# ObsidianYandexGoogle

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
