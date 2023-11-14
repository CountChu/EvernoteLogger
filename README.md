# evernote_logger.py
The app reads notes from Evernote and generate a daily report into Evernote.

The app depends on the package, [EvernoteLogger](https://github.com/CountChu/EvernoteWrapper).

Usage 1: Generate today's log from Evernote.
```
python evernote_logger.py  
```

Usage 2: Generate a log from Evernote for a certain day.
```
python evernote_logger.py --ymd 20210102
```

Usage 3: Generate today's log from Evernote with a specific config.
```
python evernote_logger.py -c config-YOU.yaml
```