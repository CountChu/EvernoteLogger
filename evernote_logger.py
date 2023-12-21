#
# FILENAME.
#       evernote_logger.py - Evernote Logger Python App.
#
# FUNCTIONAL DESCRIPTION.
#       The app reads notes from Evernote and generate a daily report into Evernote.
#
#       The app depends on evernote_wrapper.
#
# NOTICE.
#       Author: visualge@gmail.com (CountChu)
#       Created on 2022/2/22
#       Updated on 2023/11/14
#

import argparse
import logging
import sys
import codecs
import datetime
import html
import yaml
import os
import pdb
br = pdb.set_trace

from evernote_wrapper import EvernoteWrapper
import evernote.edam.type.ttypes as Types

def build_args():
    desc = '''
    Usage 1: Generate today's log from Evernote.
        python evernote_logger.py  

    Usage 2: Generate today's log from Evernote and order by notebooks.
        python evernote_logger.py --nb

    Usage 3: Generate a log from Evernote for a certain day.
        python evernote_logger.py --ymd 20210102

    Usage 4: Generate today's log from Evernote with a specific config.
        python evernote_logger.py -c config-YOU.yaml
'''

    #
    # Build an ArgumentParser object to parse arguments.
    #

    parser = argparse.ArgumentParser(
                formatter_class=argparse.RawTextHelpFormatter,
                description=desc)

    parser.add_argument(
            "--ymd",
            dest="yyyymmdd",
            required=False,
            help="E.g., 20220228")

    parser.add_argument(
            "--dt",
            dest="prefix_datetime",
            action='store_true',
            help="E.g., 2022/02/28 09:56 220225 Communication")

    parser.add_argument(
            "--test",
            dest="test",
            action='store_true',
            help="Don't generate a note in Evernote")

    parser.add_argument(
            "-c",
            dest="config",
            default="config.yaml",
            help="Config file.")

    parser.add_argument(
            "--nb",
            dest="notebook",
            action='store_true',
            help="Order by notebooks")

    #
    # Return arguments.
    #

    args = parser.parse_args()  
    return args

def get_last_date(yyyymmdd):
    dt = datetime.datetime.strptime(yyyymmdd, '%Y%m%d')
    last_dt = dt - datetime.timedelta(days=1)
    last_yyyymmdd = last_dt.strftime('%Y%m%d')
    return last_yyyymmdd

def get_day(yyyymmdd):
    dt = datetime.datetime.strptime(yyyymmdd, '%Y%m%d')
    return dt.strftime('%w')

def main():

    #
    # Read arguments
    #

    args = build_args()

    #
    # Load config.yaml
    #

    fn = os.path.join(os.path.dirname(__file__), args.config)
    f = open(fn, 'r', encoding='utf-8')
    cfg = yaml.load(f, Loader=yaml.CLoader)
    f.close()

    #
    # Create an Evernote Wrapper object
    #

    ew = EvernoteWrapper()

    #
    # Specify user name and token for the Evernote.
    #

    user_name = cfg['userName']
    auth_token = cfg['authToken']

    #
    # Connect Evernote service
    #

    ew.connect(user_name, auth_token)

    #
    # Search notebook "C1 - Auto"
    #
    
    auto_nb = ew.get_notebook(cfg['notebook'])

    #
    # Specify yyyymmdd
    #

    if args.yyyymmdd == None:
        yyyymmdd = datetime.datetime.now().strftime('%Y%m%d')
    else:
        yyyymmdd = args.yyyymmdd

    #
    # Check yyyymmdd
    #

    if len(yyyymmdd) != 8:
        print('Error!')
        print(f'yyyymmdd = {yyyymmdd}')
        sys.exit(1)

    #
    # Get day of week.
    #

    day = get_day(yyyymmdd)
    c_day_d = cfg['days']
    c_day = c_day_d[day]


    #
    # Use last_yyyymmdd to query notes to fix time zone issue.
    #     

    last_yyyymmdd = get_last_date(yyyymmdd)

    #
    # guid_note_d[guid] = note
    # note = ('guid', 'dt', 'type', 'title')
    # type = 'create' or 'update'  
    #
    #

    guid_note_d = {}

    print('Created notes:')
    note_meta_list = ew.search_created_notes_by_date(last_yyyymmdd)

    #
    #for note_meta in note_meta_list:
    #    print("%s: [%s]" % (note_meta.created, note_meta.title))
    #

    for note_meta in note_meta_list:
        assert note_meta.guid not in guid_note_d

        created = note_meta.created // 1000
        created_dt = datetime.datetime.fromtimestamp(created)
        if yyyymmdd != created_dt.strftime("%Y%m%d"):
            print('%s: Skip the note [%s].' % (created_dt, note_meta.title))
            continue 

        created_str = created_dt.strftime("%Y/%m/%d %H:%M")

        note = {}
        note['guid'] = note_meta.guid    
        note['notebookGuid'] = note_meta.notebookGuid    
        note['title'] = note_meta.title 
        note['dt'] = created_str
        note['type'] = 'Create'
        guid_note_d[note['guid']] = note

        print("%s: [%s]" % (created_dt, note_meta.title))
    print('')

    print('Updated notes:')
    note_meta_list = ew.search_updated_notes_by_date(last_yyyymmdd)
    for note_meta in note_meta_list:
        if note_meta.guid in guid_note_d:
            print('The note [%s] is in the dict.' % note_meta.title)
            continue

        updated = note_meta.updated
        assert updated != None

        updated = updated // 1000
        updated_dt = datetime.datetime.fromtimestamp(updated)
        if yyyymmdd != updated_dt.strftime("%Y%m%d"):
            print('%s: Skip the note [%s].' % (updated_dt, note_meta.title))
            continue 

        updated_str = updated_dt.strftime("%Y/%m/%d %H:%M")

        note = {}
        note['guid'] = note_meta.guid
        note['notebookGuid'] = note_meta.notebookGuid
        note['title'] = note_meta.title 
        note['dt'] = updated_str
        note['type'] = 'Update'
        guid_note_d[note['guid']] = note

        print("%s: [%s]" % (created_dt, note_meta.title))
    print('-----------------------------------------------------------')

    #
    # Transform guid_note_d in note_ls
    #

    note_ls = []
    for guid, note in guid_note_d.items():
        note_ls.append(note)

    #
    # Sort note_ls by 'dt'
    #

    note_ls = sorted(note_ls, key=lambda x: x['dt'])

    #
    # Build viewLink
    # evernote:///view/[userId]/[shardId]/[noteGuid]/[noteGuid]/
    # evernote:///view/19792815/s172/640f0459-f271-a6f7-22fe-f02588dcf55b/48aa7d36-8a0d-4ba0-b85a-ff3591138f04/"
    #

    for note in note_ls:
        userId = ew.user_info.userId
        shardId = ew.user_info.shardId 
        noteGuid = note['guid']
        notebookGuid = note['notebookGuid'] 
        viewLink = 'evernote:///view/%d/%s/%s/%s/' % (userId, shardId, noteGuid, notebookGuid)
        note['viewLink'] = viewLink

        print(note['dt'], note['type'], note['title'])

    #
    # If --test, exit the program.
    #

    if args.test:
        sys.exit(0)

    #
    # If --nb, group note_ls by notebooks.
    #   name_ls = []
    #   name_notes[name] = note_ls
    #

    name_ls = []
    name_notes = {}

    if args.notebook:
        nb_ls = ew.note_store.listNotebooks()
        guid_name = {}
        for nb in nb_ls:
            guid_name[nb.guid] = nb.name


        for note in note_ls:
            name = guid_name[note['notebookGuid']]
            if name not in name_notes:
                name_notes[name] = []
                name_ls.append(name)
            name_notes[name].append(note)

    else:
        no_name = ''
        name_ls.append(no_name)
        name_notes[no_name] = note_ls

    #
    # Build a note.
    #

    content = ''
    content += '<?xml version="1.0" encoding="UTF-8"?>'
    content += '<!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">'
    content += '<en-note>'
    content += '<h1>%s %s</h1>' % (yyyymmdd[2:], c_day)

    if 'headlines' in cfg:
        for headline in cfg['headlines']:
            content += '<h1>%s</h1>' % (headline)

    for name in name_ls:
        if name != '':
            notebook_name = html.escape(name)
            content += '<h2>%s</h2>' % (notebook_name)

        for note in name_notes[name]:
            title = html.escape(note['title'])
            
            _type = ''
            if note['type'] == 'Update':
                _type = '(U)'
            
            if args.prefix_datetime:
                dt = note['dt']
            else:
                dt = note['dt'][11:]

            print('title: ', title)
            content += '<div>'
            content += '%s&nbsp;&nbsp;<a href="%s">%s</a> %s' % (
                dt, 
                note['viewLink'], 
                title, 
                _type)
            content += '</div>'

    content += '</en-note>'

    note_obj = Types.Note()
    note_obj.title = "Auto - Log - %s" % yyyymmdd[2:]
    note_obj.content = content
    note_obj.notebookGuid = auto_nb.guid
    
    createdNote = ew.note_store.createNote(note_obj)

    print("Successfully created a new note with GUID: ", createdNote.guid)

if __name__ == '__main__':
    main()  
    