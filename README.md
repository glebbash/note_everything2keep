# note_everything2keep
NoteEverything to Google Keep export

# prerequisites

* python3
* pip3

## usage
```bash
git clone https://github.com/glebbash/note_everything2keep.git
```
Create a backup in NoteEverything.\
Extract notes.db file from root of the created zip file into note_everything2keep folder.
```bash
python3 note_everything2keep/ne2keep.py notes.db
```
If script fails to connect check gkeepapi faq: https://gkeepapi.readthedocs.io/en/latest/#faq
