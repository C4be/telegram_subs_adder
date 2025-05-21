# auto-add.py
from telethon.sync import TelegramClient
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputPeerEmpty, InputPeerChannel, InputPeerUser
from telethon.tl.functions.channels import InviteToChannelRequest
from telethon.errors.rpcerrorlist import PeerFloodError, UserPrivacyRestrictedError, ChatAdminRequiredError
import csv, traceback, time, random, re, os, sys

# заполните своими значениями или через переменные окружения
api_id   = int(os.getenv('TG_API_ID', '0'))
api_hash = os.getenv('TG_API_HASH', '')
phone    = os.getenv('TG_PHONE', '')
PAUSE_SEC = 60

client = TelegramClient(phone, api_id, api_hash)
client.start()

last_csv = None

def list_dialogs(include_channels=True):
    chats = client(GetDialogsRequest(offset_date=None, offset_id=0,
                                     offset_peer=InputPeerEmpty(), limit=200, hash=0)).chats
    res = []
    for c in chats:
        if getattr(c, 'left', False): continue
        if getattr(c, 'megagroup', False):
            res.append(c)
        elif include_channels and getattr(c, 'broadcast', False):
            res.append(c)
    return res

def choose(items, title):
    while True:
        print('\n' + title)
        for i, it in enumerate(items, 1):
            print(f'{i} — {it.title if hasattr(it, "title") else it}')
        print('0 — Назад   |   q — Выход')
        s = input('> ').strip().lower()
        if s == 'q': sys.exit()
        if s == '0': return None
        if s.isdigit() and 1 <= int(s) <= len(items):
            return items[int(s) - 1]

def scrape():
    global last_csv
    dlg = choose(list_dialogs(include_channels=False), 'Группа/чат для скрапа')
    if not dlg: return
    try:
        users = client.get_participants(dlg, aggressive=True)
    except ChatAdminRequiredError:
        print('Нужны права админа.')
        return
    fn = f"members-{re.sub('-+','-',re.sub('[^a-zA-Z]','-',dlg.title.lower()))}.csv"
    with open(fn, 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f)
        w.writerow(['username','user id','access hash','name','group','group id'])
        for u in users:
            w.writerow([u.username or '', u.id, u.access_hash,
                        f"{u.first_name or ''} {u.last_name or ''}".strip(),
                        dlg.title, dlg.id])
    last_csv = fn
    print(f'Сохранено {len(users)} участников в {fn}')

def add():
    global last_csv
    csv_path = last_csv if last_csv and os.path.exists(last_csv) else \
        choose([f for f in os.listdir('.') if f.startswith('members-') and f.endswith('.csv')], 'CSV-файл')
    if not csv_path: return
    with open(csv_path, encoding='utf-8') as f:
        rows = list(csv.reader(f))[1:]
    users = [{'username': r[0], 'id': int(r[1]), 'access_hash': int(r[2])} for r in rows]
    random.shuffle(users)

    target = choose(list_dialogs(include_channels=True), 'Куда добавлять')
    if not target: return
    target_ent = InputPeerChannel(target.id, target.access_hash)

    mode = input('1 — username, 2 — id  > ').strip()
    if mode not in ('1', '2'): return

    log_file = f"added-{target.id}.txt"
    added_ids = set()
    if os.path.exists(log_file):
        with open(log_file) as lf:
            added_ids = {int(x.strip()) for x in lf if x.strip().isdigit()}

    skipped = done = err = 0
    for u in users:
        if u['id'] in added_ids:
            skipped += 1
            continue
        try:
            ent = client.get_input_entity(u['username']) if mode == '1' and u['username'] \
                  else InputPeerUser(u['id'], u['access_hash'])
            client(InviteToChannelRequest(target_ent, [ent]))
            done += 1
            with open(log_file, 'a') as lf:
                lf.write(f"{u['id']}\n")
            time.sleep(PAUSE_SEC)
        except PeerFloodError:
            print('Flood error, стоп.')
            break
        except UserPrivacyRestrictedError:
            print('Приватность, skip')
        except Exception:
            traceback.print_exc()
            err += 1
            if err > 10:
                print('Много ошибок, выходим.')
                break
    print(f'Добавлено {done}, пропущено {skipped}')

def show_csv():
    path = choose([f for f in os.listdir('.') if f.startswith('members-') and f.endswith('.csv')], 'Показ CSV')
    if not path: return
    with open(path, encoding='utf-8') as f:
        for r in csv.reader(f): print(r)

while True:
    print('\nГлавное меню\n0 — Назад\n1 — Скрап участников\n2 — Добавить из CSV\n3 — Показать CSV\nq — Выход')
    cmd = input('> ').strip().lower()
    if cmd == 'q': break
    if cmd == '1': scrape()
    elif cmd == '2': add()
    elif cmd == '3': show_csv()
