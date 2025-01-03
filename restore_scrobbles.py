print("Скрипт для дозагрузки потерянных яндекс.музыкой скробблов")
print("Если что пишите t.me/Roman_Deev или пингуйте в t.me/yandexvernitescrobbling")
print()
print("Для начала запросите у яндекса архив данных яндекс.музыки: https://id.yandex.ru/personal/data")
print("Распакуйте его и положите в одну папку со скриптом файл history.json")
print()
print("Введите время, когда Яндекс.Музыка в последний раз отправила скроббл")
print("Пример: 2024-12-26T01:47:22+00:00")
print("Обратите внимание, что в last.fm может показываться местное время")
print("Нужно UTC, т.е. если в last.fm московское время, то вычтите 3 часа")
START_TIME = input()
print()

print("Введите время до какого времени нужно восстановить историю.")
print("Например, время вашего перехода на новый скробблер")
print("Пример: 2024-12-28T17:03:00+00:00")
END_TIME = input()

import json
from datetime import datetime
from yandex_music import Client
import os
import pylast

start_time = datetime.fromisoformat(START_TIME)
end_time = datetime.fromisoformat(END_TIME)

filtered = []

with open("history.json") as f:
    history = json.load(f)
    for item in history:
        item_time = datetime.fromisoformat(item["timestamp"].rstrip("Z") + "+00:00")
        if start_time <= item_time < end_time:
            filtered.append(item)

client = Client().init()
rich_results = client.tracks(list(set(list(map(lambda x: x['id'], filtered)))))
ids_map = {x.id: x for x in rich_results}

scrobbles = []
problems = []

for item in filtered:
    try:
        track_info = {"artist": ids_map[item['id']].artists[0].name,
                      "title": ids_map[item['id']].title,
                      "album": ids_map[item['id']].albums[0].title if ids_map[item['id']].albums else None,
                      "timestamp": item['timestamp'],
                      "duration": ids_map[item['id']].duration_ms // 1000
                      if ids_map[item['id']].duration_ms is not None
                      else None,
                      }
        print(list(track_info.values()))
        scrobbles.append(track_info)
    except:
        problems.append(item)

if len(problems):
    with open("problems_tracks.txt", "w") as f:
        for item in problems:
            print(item, ids_map[item['id']].artists[0].name)

print("Проверьте начало и конец списка")
ans = input("Загрузить в Last.fm? [yes/No]\n")

if ans[0] == "y":
    SESSION_KEY_FILE = ".session_key"
    network = pylast.LastFMNetwork("15ea55ecc2d12d5910bd1a56c89fb604",
                                   "2dff873c07e12a590e512c62b86b899c")
    if not os.path.exists(SESSION_KEY_FILE):
        skg = pylast.SessionKeyGenerator(network)
        url = skg.get_web_auth_url()

        print(f"Пожалуйста, авторизуйтесь в last.fm: {url}\n")
        import time
        import webbrowser

        webbrowser.open(url)

        while True:
            try:
                session_key = skg.get_web_auth_session_key(url)
                with open(SESSION_KEY_FILE, "w") as f:
                    f.write(session_key)
                break
            except pylast.WSError:
                time.sleep(1)
    else:
        session_key = open(SESSION_KEY_FILE).read()

    network.session_key = session_key

    print("Начало загрузки")
    for track in scrobbles:
        print("Загружаем ", track, end="")
        timestamp = int(datetime.fromisoformat(track["timestamp"].rstrip("Z") + "+00:00").timestamp())
        lastfm_user = network.get_user(network.username)
        network.scrobble(artist=track["artist"],
                         title=track["title"],
                         album=track['album'],
                         duration=track['duration'],
                         timestamp=timestamp)
        print(" Done!")
    print("Всё загружено")
