from telethon.sync import TelegramClient
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputPeerEmpty, InputPeerChannel, InputPeerUser
from telethon.tl.functions.channels import InviteToChannelRequest
from telethon.errors.rpcerrorlist import (
    PeerFloodError, UserPrivacyRestrictedError,
    ChatAdminRequiredError, UserNotMutualContactError
)
import csv, traceback, time, random, re, os, sys, webbrowser

# ──────────────────────────────────────────────────────────────────────────── #
# 1.  Настройка через переменные окружения
#     TG_API_ID , TG_API_HASH , TG_PHONE   (обязательны)
# ──────────────────────────────────────────────────────────────────────────── #
try:
    api_id   = int(os.environ["TG_API_ID"])
    api_hash = os.environ["TG_API_HASH"]
    phone    = os.environ["TG_PHONE"]
except KeyError:
    print("❌  Нужно задать переменные окружения TG_API_ID, TG_API_HASH, TG_PHONE")
    sys.exit(1)

DEFAULT_PAUSE = int(os.getenv("TG_PAUSE_SEC", 60))  # секунд между инвайтами

# ──────────────────────────────────────────────────────────────────────────── #
print("\n📰  Хочешь полезных материалов?")
print("Автор скрипта 👉  https://t.me/jabrail_digital\n")
ans = input("Перейти в канал? (y/N): ").strip().lower()
if ans == "y":
    webbrowser.open("https://t.me/jabrail_digital")

# ──────────────────────────────────────────────────────────────────────────── #
client = TelegramClient(phone, api_id, api_hash)
client.start()

last_csv = None  # запомним последний созданный CSV

# ──────────────────────────────────────────────────────────────────────────── #
# Вспомогательные функции
# ──────────────────────────────────────────────────────────────────────────── #
def list_dialogs(include_channels=True):
    chats = client(GetDialogsRequest(offset_date=None, offset_id=0,
                                     offset_peer=InputPeerEmpty(), limit=200, hash=0)).chats
    res = []
    for c in chats:
        if getattr(c, "left", False):
            continue
        if getattr(c, "megagroup", False):
            res.append(c)
        elif include_channels and getattr(c, "broadcast", False):
            res.append(c)
    return res

def choose(items, title):
    while True:
        print("\n" + title)
        for i, it in enumerate(items, 1):
            name = it if isinstance(it, str) else it.title
            print(f"{i} — {name}")
        print("0 — Назад   |   q — Выход")
        s = input("> ").strip().lower()
        if s == "q":
            sys.exit()
        if s == "0":
            return None
        if s.isdigit() and 1 <= int(s) <= len(items):
            return items[int(s) - 1]

# ──────────────────────────────────────────────────────────────────────────── #
# 1. Скрап участников
# ──────────────────────────────────────────────────────────────────────────── #
def scrape():
    global last_csv
    dlg = choose(list_dialogs(include_channels=False), "Группа/чат для скрапа")
    if not dlg:
        return
    try:
        users = client.get_participants(dlg, aggressive=True)
    except ChatAdminRequiredError:
        print("🚫 Нужны права админа.")
        return

    fn = f"members-{re.sub('-+','-', re.sub('[^a-zA-Z]','-', dlg.title.lower()))}.csv"
    with open(fn, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["username", "user id", "access hash", "name", "group", "group id"])
        for u in users:
            w.writerow([
                u.username or "",
                u.id,
                u.access_hash,
                f"{u.first_name or ''} {u.last_name or ''}".strip(),
                dlg.title,
                dlg.id
            ])
    last_csv = fn
    print(f"✅ Сохранено {len(users)} участников в {fn}")

# ──────────────────────────────────────────────────────────────────────────── #
# 2. Добавление
# ──────────────────────────────────────────────────────────────────────────── #
def add():
    global last_csv

    csv_path = (last_csv if last_csv and os.path.exists(last_csv) else
                choose([f for f in os.listdir('.') if f.startswith('members-') and f.endswith('.csv')],
                       "CSV-файл с участниками"))
    if not csv_path:
        return
    with open(csv_path, encoding="utf-8") as f:
        rows = list(csv.reader(f))[1:]
    users = [{"username": r[0], "id": int(r[1]), "access_hash": int(r[2])} for r in rows]
    random.shuffle(users)

    target = choose(list_dialogs(include_channels=True), "Куда добавлять участников")
    if not target:
        return
    target_ent = InputPeerChannel(target.id, target.access_hash)

    mode = input("Способ (1 — username, 2 — id) > ").strip()
    if mode not in ("1", "2"):
        return

    try:
        limit = int(input("Сколько людей добавить? (Enter = все): ").strip() or 0)
    except ValueError:
        limit = 0

    try:
        pause_sec = int(input(f"Пауза между инвайтами (Enter = {DEFAULT_PAUSE}): ").strip() or DEFAULT_PAUSE)
    except ValueError:
        pause_sec = DEFAULT_PAUSE

    log_file = f"added-{target.id}.txt"
    added_ids = set()
    if os.path.exists(log_file):
        with open(log_file) as lf:
            added_ids = {int(x.strip()) for x in lf if x.strip().isdigit()}

    skipped = done = err = 0
    print("\n▶️  Начинаем добавление (Ctrl+C — остановить)…\n")

    try:
        for u in users:
            if limit and done >= limit:
                break
            if u["id"] in added_ids:
                skipped += 1
                continue
            try:
                ent = (client.get_input_entity(u["username"])
                       if mode == "1" and u["username"]
                       else InputPeerUser(u["id"], u["access_hash"]))
                client(InviteToChannelRequest(target_ent, [ent]))
                done += 1
                print(f"✅ @{u['username'] or u['id']} добавлен")
                with open(log_file, "a") as lf:
                    lf.write(f"{u['id']}\n")
                time.sleep(pause_sec)
            except UserNotMutualContactError:
                print(f"🚫 @{u['username'] or u['id']} — not mutual, пропуск.")
            except PeerFloodError:
                print("⛔ Flood-error, Telegram требует паузы. Скрипт остановлен.")
                break
            except UserPrivacyRestrictedError:
                print("🔒 Приватность, пропуск.")
            except Exception:
                traceback.print_exc()
                err += 1
                if err > 10:
                    print("⚠️  Слишком много ошибок, выходим.")
                    break
    except KeyboardInterrupt:
        print("\n⏹️  Остановлено пользователем.")

    print(f"\nИтого: добавлено {done}, пропущено (уже были) {skipped}")

# ──────────────────────────────────────────────────────────────────────────── #
# 3. Показ CSV
# ──────────────────────────────────────────────────────────────────────────── #
def show_csv():
    path = choose([f for f in os.listdir('.') if f.startswith('members-') and f.endswith('.csv')],
                  "Выберите CSV для просмотра")
    if not path:
        return
    with open(path, encoding="utf-8") as f:
        for row in csv.reader(f):
            print(row)

# ──────────────────────────────────────────────────────────────────────────── #
# Главное меню
# ──────────────────────────────────────────────────────────────────────────── #
while True:
    print("\nГлавное меню")
    print("0 — Назад")
    print("1 — Скрап участников")
    print("2 — Добавить из CSV")
    print("3 — Показать CSV")
    print("q — Выход")
    cmd = input("> ").strip().lower()
    if cmd == "q":
        break
    if cmd == "1":
        scrape()
    elif cmd == "2":
        add()
    elif cmd == "3":
        show_csv()
