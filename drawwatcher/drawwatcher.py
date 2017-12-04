#!/usr/bin/python3.6

import psycopg2
import os
import logging
import inotify.adapters
import glob
import collections
import subprocess
import shutil

PROCESS_DIR = os.path.expanduser('~') + '/draws/to_process'
SERVE_DIR = os.path.expanduser('~') + '/draws/distribute'
ERROR_DIR = os.path.expanduser('~') + '/draws/error'
THUMBNAIL_DIR = SERVE_DIR + '/thumbnails/'
PG_PREFIX = 'distribute/'  # TODO: think of something & fix

PG_PASSWORD = str(os.environ['NEWDRAWS_PG_PASSWORD'])
CONN_STRING = 'dbname=newdraws ' + \
    'user=drawwatcher ' + \
    'host=localhost ' + \
    f'password={PG_PASSWORD} ' + \
    'port=5432 '


def _thumbnail_outfile(infile):
    if len(infile.split('.')) == 1:
        return THUMBNAIL_DIR + \
            os.path.basename(infile) + \
            '.jpg'
    else:
        return THUMBNAIL_DIR + \
            os.path.basename(infile).split('.')[-2] + \
            '.jpg'


def _ensure_dirs_exist():
    os.makedirs(PROCESS_DIR, exist_ok=True)
    os.makedirs(SERVE_DIR, exist_ok=True)
    os.makedirs(ERROR_DIR, exist_ok=True)
    os.makedirs(THUMBNAIL_DIR, exist_ok=True)


def _move_file_error(infile):
    filename = os.path.basename(infile)

    error_filename = ERROR_DIR + '/' + filename
    if os.path.exists(error_filename):
        print('this file has failed before! overwriting... ',
              error_filename)
        os.remove(error_filename)
    shutil.move(infile, ERROR_DIR)


def _main():
    _ensure_dirs_exist()

    #
    # inotify 'write_close' directory

    i = inotify.adapters.Inotify()

    i.add_watch(PROCESS_DIR.encode('UTF-8'))

    try:
        for event in i.event_gen():
            if event is not None:
                (header, type_names, watch_path, filename) = event
                what_happened = set(type_names)
                care_for = set(('IN_CLOSE_WRITE', 'IN_MOVED_TO'))
                if any(what_happened.intersection(care_for)):
                    files = []
                    files.extend(glob.glob(PROCESS_DIR + '/*'))

                    for infile in files:
                        # check supported file types
                        if not infile.split('.')[-1] in ('png', 'jpg', 'gif'):
                            print(
                                f'unsupported file extension! {infile} -> error')
                            _move_file_error(infile)
                            continue

                        #
                        # autorotate (uses metadata)... only works for jpg
                        subprocess.run(["jhead",
                                        "-autorot",
                                        infile])

                        #
                        # wipe metadata
                        subprocess.run(["exiftool",
                                        "-all=",
                                        "-overwrite_original",
                                        infile])

                        #
                        # run thumbnailer imagemagick command on file
                        outfile = _thumbnail_outfile(infile)
                        print(f'THUMBNAIL: {infile} ...', end='')
                        subprocess.run(["convert",
                                        infile,
                                        "-background",
                                        "white",
                                        "-alpha",
                                        "remove",
                                        "-colorspace",
                                        "RGB",
                                        "-thumbnail",
                                        "300x300",
                                        "-colorspace",
                                        "sRGB",
                                        "-auto-orient",
                                        outfile])

                        # TODO: check if thumbnailing failed? (move ->
                        # error/...)

                        print(f'DONE ({outfile})')

                        #
                        # insert file into db
                        db_infile = PG_PREFIX + os.path.basename(infile)
                        cur = conn.cursor()

                        # callproc no returnval? tsk tsk...
                        cur.execute(
                            "SELECT * FROM add_draw(%s);", (db_infile,))
                        didInsert = cur.fetchone()[0]
                        conn.commit()

                        if didInsert:
                            print('POSTGRES: thumbnailed & inserted ' + db_infile)
                            shutil.move(infile, SERVE_DIR)
                        else:
                            print(
                                'ERROR inserting into DB (probably attempted to insert duplicate filepath!)')
                            _move_file_error(infile)

    finally:
        i.remove_watch(PROCESS_DIR.encode('UTF-8'))


if __name__ == '__main__':
    conn = psycopg2.connect(CONN_STRING)
    _main()
