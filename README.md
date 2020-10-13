# note_everything2keep
NoteEverything to Google Keep export

## usage
Create a backup of notes in NoteEverything.
Extract notes.db file from root of the created zip file.
If script fails to connect check gkeepapi faq: https://gkeepapi.readthedocs.io/en/latest/#faq
```bash
git clone https://github.com/glebbash/note_everything2keep.git
python3 note_everything2keep/ne2keep.py <PATH_TO_DB>
```
