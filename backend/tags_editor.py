from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3NoHeaderError

def extract_tags(mp3_path: str) -> dict:
    try:
        audio = EasyID3(mp3_path)
    except ID3NoHeaderError:
        audio = EasyID3()
        audio.save(mp3_path)
        return {
            "title": "", "artist": "", "album": "", "genre": "", "date": ""
        }

    return {
        "title": audio.get("title", [""])[0],
        "artist": audio.get("artist", [""])[0],
        "album": audio.get("album", [""])[0],
        "genre": audio.get("genre", [""])[0],
        "date": audio.get("date", [""])[0]
    }

def update_tags(mp3_path: str, new_tags: dict):
    try:
        audio = EasyID3(mp3_path)
    except ID3NoHeaderError:
        audio = EasyID3()
    for key, value in new_tags.items():
        if value and key in ['title', 'artist', 'album', 'genre', 'date']:
            audio[key] = value
    audio.save()
