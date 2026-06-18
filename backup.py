#!/usr/bin/env python3
"""
backup.py — заливает весь Obsidian-vault на Yandex Disk и/или Google Drive,
сохраняя ту же структуру папок. Запускать удобнее через backup.sh.

  python backup.py --target yandex
  python backup.py --target google
  python backup.py --target both

Настройки и токены — в config.json рядом с этим файлом (НЕ коммитить, НЕ заливать).
Инкрементально: файл, уже существующий на облаке с тем же размером, пропускается.
Удаление на облаке не выполняется (только добавление/обновление).
"""

import argparse
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent          # .../MouseRecordings/_backup
VAULT = HERE.parent                             # .../MouseRecordings (корень vault)
CONFIG = HERE / "config.json"
GOOGLE_TOKEN = HERE / "token.json"


# ----------------------------------------------------------------------------
# Конфиг и обход файлов
# ----------------------------------------------------------------------------
def load_config():
    if not CONFIG.exists():
        sys.exit(f"Нет файла настроек: {CONFIG}\nСкопируй config.example.json -> config.json и заполни.")
    with open(CONFIG, encoding="utf-8") as f:
        return json.load(f)


def save_config(cfg):
    with open(CONFIG, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


def iter_files(cfg):
    """Отдаёт пары (локальный путь, относительный путь от корня vault)."""
    include_obsidian = cfg.get("include_obsidian", True)
    include_git = cfg.get("include_git", False)
    extra = set(cfg.get("exclude", []))
    backup_dir = HERE.name                      # сам _backup исключаем всегда

    for root, dirs, files in os.walk(VAULT):
        rel = Path(root).relative_to(VAULT)
        keep = []
        for d in dirs:
            child = (rel / d) if rel != Path(".") else Path(d)
            top = child.parts[0]
            if top == backup_dir:               # не заливаем venv/токены/сам скрипт
                continue
            if top == ".git" and not include_git:
                continue
            if top == ".obsidian" and not include_obsidian:
                continue
            if d in extra or child.as_posix() in extra:
                continue
            keep.append(d)
        dirs[:] = keep

        for fname in files:
            local = Path(root) / fname
            relpath = (rel / fname) if rel != Path(".") else Path(fname)
            if relpath.as_posix() in extra or fname in extra:
                continue
            yield local, relpath


# ----------------------------------------------------------------------------
# Yandex Disk
# ----------------------------------------------------------------------------
def yandex_connect(cfg):
    import yadisk

    y = cfg["yandex"]
    client = yadisk.YaDisk(id=y.get("client_id", ""),
                           secret=y.get("client_secret", ""),
                           token=y.get("token", ""))

    if y.get("token") and client.check_token():
        return client

    # Интерактивная авторизация по коду подтверждения (один раз).
    print("\n=== Авторизация Yandex Disk ===")
    print("1) Открой ссылку в браузере и подтверди доступ:")
    print("   " + client.get_code_url())
    code = input("2) Вставь код подтверждения: ").strip()
    response = client.get_token(code)
    client.token = response.access_token
    if not client.check_token():
        sys.exit("Не удалось получить токен Yandex (проверь client_secret и код).")
    cfg["yandex"]["token"] = client.token
    save_config(cfg)
    print("Токен Yandex сохранён в config.json.\n")
    return client


def yandex_ensure_dir(client, remote_dir, made):
    """Создаёт вложенные папки по очереди (mkdir -p)."""
    if remote_dir in made:
        return
    parts = [p for p in remote_dir.strip("/").split("/") if p]
    cur = ""
    for p in parts:
        cur += "/" + p
        if cur not in made and not client.exists(cur):
            client.mkdir(cur)
        made.add(cur)
    made.add(remote_dir)


def backup_yandex(cfg, files):
    client = yandex_connect(cfg)
    folder = "/" + cfg["backup_folder"].strip("/")
    made = set()
    up = skip = err = 0

    for local, relpath in files:
        remote = folder + "/" + relpath.as_posix()
        try:
            yandex_ensure_dir(client, os.path.dirname(remote), made)
            if client.exists(remote):
                meta = client.get_meta(remote)
                if getattr(meta, "size", None) == local.stat().st_size:
                    skip += 1
                    continue
            print(f"==> Yandex: {relpath.as_posix()}")
            client.upload(str(local), remote, overwrite=True)
            up += 1
        except Exception as e:                  # noqa: BLE001 — хотим продолжить остальные
            err += 1
            print(f"    ! ошибка {relpath.as_posix()}: {e}", file=sys.stderr)

    print(f"Yandex: загружено {up}, пропущено {skip}, ошибок {err}.")


# ----------------------------------------------------------------------------
# Google Drive
# ----------------------------------------------------------------------------
GOOGLE_SCOPES = ["https://www.googleapis.com/auth/drive.file"]


def google_connect(cfg):
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    creds = None
    if GOOGLE_TOKEN.exists():
        creds = Credentials.from_authorized_user_file(str(GOOGLE_TOKEN), GOOGLE_SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            g = cfg["google"]
            client_config = {
                "installed": {
                    "client_id": g["client_id"],
                    "client_secret": g["client_secret"],
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": ["http://localhost"],
                }
            }
            print("\n=== Авторизация Google Drive (откроется браузер) ===")
            flow = InstalledAppFlow.from_client_config(client_config, GOOGLE_SCOPES)
            creds = flow.run_local_server(port=0)
        GOOGLE_TOKEN.write_text(creds.to_json(), encoding="utf-8")
        print("Токен Google сохранён в token.json.\n")

    return build("drive", "v3", credentials=creds)


def drive_find(service, name, parent, folder=False):
    safe = name.replace("\\", "\\\\").replace("'", "\\'")
    q = f"name = '{safe}' and '{parent}' in parents and trashed = false"
    if folder:
        q += " and mimeType = 'application/vnd.google-apps.folder'"
    res = service.files().list(q=q, spaces="drive",
                               fields="files(id, size, mimeType)").execute()
    return res.get("files", [])


def drive_folder_id(service, relparts, cache):
    """Возвращает id папки (создаёт цепочку при необходимости). relparts от корня бэкапа."""
    key = "/".join(relparts)
    if key in cache:
        return cache[key]
    parent = cache[""]                          # id корневой папки бэкапа
    built = []
    for part in relparts:
        built.append(part)
        ck = "/".join(built)
        if ck in cache:
            parent = cache[ck]
            continue
        found = drive_find(service, part, parent, folder=True)
        if found:
            parent = found[0]["id"]
        else:
            meta = {"name": part, "mimeType": "application/vnd.google-apps.folder",
                    "parents": [parent]}
            parent = service.files().create(body=meta, fields="id").execute()["id"]
        cache[ck] = parent
    return parent


def backup_google(cfg, files):
    from googleapiclient.http import MediaFileUpload

    service = google_connect(cfg)
    cache = {}

    # корневая папка бэкапа в "My Drive"
    root_name = cfg["backup_folder"]
    found = drive_find(service, root_name, "root", folder=True)
    if found:
        cache[""] = found[0]["id"]
    else:
        meta = {"name": root_name, "mimeType": "application/vnd.google-apps.folder",
                "parents": ["root"]}
        cache[""] = service.files().create(body=meta, fields="id").execute()["id"]

    up = skip = err = 0
    for local, relpath in files:
        try:
            parent = drive_folder_id(service, list(relpath.parts[:-1]), cache)
            name = relpath.name
            existing = drive_find(service, name, parent)
            media = MediaFileUpload(str(local), resumable=True)
            if existing:
                if existing[0].get("size") and int(existing[0]["size"]) == local.stat().st_size:
                    skip += 1
                    continue
                print(f"==> Google: {relpath.as_posix()}")
                service.files().update(fileId=existing[0]["id"], media_body=media).execute()
            else:
                print(f"==> Google: {relpath.as_posix()}")
                meta = {"name": name, "parents": [parent]}
                service.files().create(body=meta, media_body=media, fields="id").execute()
            up += 1
        except Exception as e:                  # noqa: BLE001
            err += 1
            print(f"    ! ошибка {relpath.as_posix()}: {e}", file=sys.stderr)

    print(f"Google: загружено {up}, пропущено {skip}, ошибок {err}.")


# ----------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="Бэкап Obsidian-vault на облака.")
    ap.add_argument("--target", choices=["yandex", "google", "both"], required=True)
    args = ap.parse_args()

    cfg = load_config()
    print(f"Vault: {VAULT}")
    print(f"Папка бэкапа на облаке: {cfg['backup_folder']}")

    if args.target in ("yandex", "both"):
        backup_yandex(cfg, list(iter_files(cfg)))
    if args.target in ("google", "both"):
        backup_google(cfg, list(iter_files(cfg)))

    print("Готово.")


if __name__ == "__main__":
    main()
