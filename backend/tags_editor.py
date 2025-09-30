from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3NoHeaderError, ID3, APIC, error

# Регистрация дополнительных текстовых тегов!
EasyID3.RegisterTextKey('albumartist', 'TPE2')
EasyID3.RegisterTextKey('composer', 'TCOM')
EasyID3.RegisterTextKey('discnumber', 'TPOS')
EasyID3.RegisterTextKey('comment', 'COMM')
EasyID3.RegisterTextKey('publisher', 'TPUB')
EasyID3.RegisterTextKey('website', 'WXXX')  # Универсальный URL (может быть WXXX или WOAR)
EasyID3.RegisterTextKey('tracknumber', 'TRCK')

def extract_tags(mp3_path: str) -> dict:
    try:
        audio = EasyID3(mp3_path)
    except ID3NoHeaderError:
        audio = EasyID3()
        audio.save(mp3_path)
        return {}

    fields = [
        "title", "artist", "album", "genre", "date", "composer", "discnumber",
        "comment", "albumartist", "publisher", "website", "tracknumber"
    ]
    result = {field: audio.get(field, [""])[0] for field in fields}
    try:
        tags = ID3(mp3_path)
        apic = tags.getall('APIC')
        result['cover_present'] = bool(apic)
    except Exception:
        result['cover_present'] = False
    return result

def update_tags(mp3_path: str, new_tags: dict, cover_bytes: bytes = None, cover_mime: str = None):
    try:
        audio = EasyID3(mp3_path)
    except ID3NoHeaderError:
        audio = EasyID3()
    allowed_keys = [
        "title", "artist", "album", "genre", "date", "composer", "discnumber",
        "comment", "albumartist", "publisher", "website", "tracknumber"
    ]
    for key in allowed_keys:
        value = new_tags.get(key)
        if value:
            audio[key] = value
    audio.save()
    # --- Add cover if provided
    if cover_bytes and cover_mime:
        tags = ID3(mp3_path)
        tags.delall('APIC')
        tags.add(APIC(
            encoding=3,
            mime=cover_mime,
            type=3,
            desc=u'Cover',
            data=cover_bytes
        ))
        tags.save(mp3_path)
