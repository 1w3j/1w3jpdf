#!/usr/bin/env python
"""
1w3j's PDF management tool:
TODO:
    - Fix v@v, tl:q BOOKLEET, ebookTM tags not being removed, needs testing
    - Detect TruePDFs vs converted PDFs
    - Detect _unc and _unc_sed files before processing special annotations to avoid deleting unwanted files
    - Refactor remove_previous_line function to print void characters according to the quantity of chars used on logging
"""
import os
import subprocess
import sys
from argparse import RawDescriptionHelpFormatter, FileType, ArgumentParser
from subprocess import DEVNULL

from termcolor import colored

PARSER = ArgumentParser(
    description='1w3j\'s tool for handling PDFs resulting in cleaner, library-ready, and easy to organize PDFs.\n'
                'This script can:\n'
                '  - Set the \"Title\" metadata attribute of pdf files equal to its filename thus avoiding hard to read'
                ' or search on library software\n'
                '  - Remove annoying annotations or Text Boxes forcefully inserted by book download websites',
    formatter_class=RawDescriptionHelpFormatter,
)
PARSER.add_argument('-r', '-R', '--recursive',
                    action="store_true",
                    help='Make recursive the processing for all the files, directories and links'
                    )
PARSER.add_argument('files',
                    nargs='+',
                    help='The list of files to be modified'
                    )
PARSER.add_argument('--dry-mode', '-D',
                    action="store_true",
                    help='Sort of \'dry run mode\', prints out which commands are going to be used for updating the '
                         'pdfs '
                    )
PARSER.add_argument('--strict', '-s',
                    action="store_true",
                    help='Strict mode for pdf-unstamper.jar, considers text areas as watermarks (annotations) and '
                         'remove them only if the content strictly equals one of the keywords'
                    )
PARSER.add_argument('--clear', '-c',
                    action="store_true",
                    help='Clear all annotations in pages which contains the target textual watermark(s), '
                         'if you encounter bordered frame issues, enable this switch '
                    )
PARSER.add_argument('-A', '--do-not-remove-annotations',
                    action="store_true",
                    help='Do not unstamp those annoying tags or annotations from free downloading '
                         'sites, this process takes time, so if need to rush, then pass this arg '
                    )
PARSER.add_argument('-o', '--output',
                    type=FileType('a'),
                    help='Store stdout in a file'
                    )
PARSER.add_argument('-sa', '--special-annotations',
                    action="store_true",
                    help='USE WITH CAUTION (first test on a duplicated file). If not even pdf-unstamper '
                         'can remove some annotations, try removing those by using sed, '
                         'see which they are at the script variable SPECIAL_ANNOYINGTATIONS '
                    )


def remove_previous_line():
    """Try to wipe the first 150 characters above from the current cursor's position"""
    print("\033[A" + " " * 1 + "\033[A")


def add_keyword(url):
    """Add the keywords as pdf-unstamper.jar -k flags. See pdf-unstamper.jar --help"""
    return ['-k'] + \
           [url]  # -k flag for adding keywords


def add_special_keyword(url):
    """Add the keywords as pdf-unstamper.jar -k flags. See pdf-unstamper.jar --help"""
    return ['-e'] + \
           ['s/' + url + '//i']  # -k flag for adding keywords


# Annoying annotations, they must have sed patterns format
ANNOYINGTATIONS = add_keyword('www.allitebooks.com') + \
                  add_keyword('www.allitebooks.org') + \
                  add_keyword('www.it-ebooks.info/') + \
                  add_keyword('www.it-ebooks.info') + \
                  add_keyword('www.ebook3000.com') + \
                  add_keyword('it-ebooks.info') + \
                  add_keyword('WOW! eBook\nwww.wowebook.org') + \
                  add_keyword('Free ebooks ==>   www.Ebook777.com') + \
                  add_keyword('free ebooks ==>   www.ebook777.com') + \
                  add_keyword('free ebooks ==> www.ebook777.com') + \
                  add_keyword("free ebooks ==>") + \
                  add_keyword('http://free-pdf-books.com') + \
                  add_keyword('http://www.freepdf-books.com') + \
                  add_keyword('http://freepdf-books.com') + \
                  add_keyword('www.freepdf-books.com') + \
                  add_keyword('www.ebook777.com') + \
                  add_keyword('WWW.EBOOK777.COM') + \
                  add_keyword('www.Ebook777.com') + \
                  add_keyword('http://www.itbookshub.com') + \
                  add_keyword('http://itbookshub.com') + \
                  add_keyword('www.itbookshub.com') + \
                  add_keyword('itbookshub.com') + \
                  add_keyword('www.it-ebooks.directory') + \
                  add_keyword('it-ebooks.director') + \
                  add_keyword('www.dbebooks.com - Free Books & magazines') + \
                  add_keyword('Licensed to   <null>') + \
                  add_keyword('Download at Boykma.Com') + \
                  add_keyword('Download at Boykma.com') + \
                  add_keyword('Download at WoweBook.Com') + \
                  add_keyword('Download at Wowebook.com') + \
                  add_keyword('Download at WoweBook.com') + \
                  add_keyword('boykma.com') + \
                  add_keyword('ebookee.org') + \
                  add_keyword('ebook3000.com') + \
                  add_keyword('From the Library of Wow! eBook') + \
                  add_keyword('Download from Wow! eBook <www.wowebook.com>') + \
                  add_keyword('Wow eBook') + \
                  add_keyword('www.wowebook.org') + \
                  add_keyword('WOW! eBook') + \
                  add_keyword('Wow! eBook') + \
                  add_keyword('WWW.WOWEBOOK.COM') + \
                  add_keyword('https://sci101web.wordpress.com') + \
                  add_keyword('Download from Join eBook (www.joinebook.com)') + \
                  add_keyword(':: Collected by PhaKaKrong ::') + \
                  add_keyword(':: Cllected by PhaKaKrong ::') + \
                  add_keyword('BOOKLEET ©') + \
                  add_keyword('BOOKLEET') + \
                  add_keyword('WOW!') + \
                  add_keyword('Apago PDF Enhancer!') + \
                  add_keyword('More free ebooks  :  http://fast-file.blogspot.com') + \
                  add_keyword('www.dbebooks.com - Free Books & magazines') + \
                  add_keyword('Download from www.eBookTM.com') + \
                  add_keyword('www.eBookTM.com') + \
                  add_keyword('eBook from Wow! eBook dot com') + \
                  add_keyword('© Osprey Publishing • www.ospreypublishing.com') + \
                  add_keyword('http://librosysolucionarios.net/') + \
                  add_keyword('http://librosysolucionarios.net') + \
                  add_keyword('http://librosysolucionarios.org/') + \
                  add_keyword('http://librosysolucionarios.org') + \
                  add_keyword('www.FreeLibros.me') + \
                  add_keyword('www.free-ebooks-download.org') + \
                  add_keyword('www.sharexxx.net - free books & magazines') + \
                  add_keyword('Download from finelybook www.finelybook.com') + \
                  add_keyword('Team-Fly®') + \
                  add_keyword('Team LRN') + \
                  add_keyword('TLFeBOOK') + \
                  add_keyword('www.journal-plaza.net & www.freedowns.net') + \
                  add_keyword('TEAM LinG - Live, Informative, Non-cost and Genuine !') + \
                  add_keyword('TEAM LinG') + \
                  add_keyword('www.GFX.0fees.net') + \
                  add_keyword('laba-ws.blogspot.com') + \
                  add_keyword('From <www.wowebook.com>') + \
                  add_keyword('https://avxhm.se/blogs/hill0') + \
                  add_keyword('v@v')
# _e('s/\/URI//') # This will erase all hyperlinks on the document including TOCs

# SPECIAL_ANNOYINGTATIONS = add_special_keyword('.*Download \).*\(at\)')  # Download at Boykma.Com -> problem is,
# it also searches for 'Download ' text on actual document paragraphs
SPECIAL_ANNOYINGTATIONS = add_special_keyword('.*Boykma\.Com') + \
                          add_special_keyword('WOW\! eBook') + \
                          add_special_keyword('WOW\!') + \
                          add_special_keyword('www\.wowebook\.org') + \
                          add_special_keyword('www\.allitebooks\.com') + \
                          add_special_keyword('More free ebooks  :  http:\/\/fast\-file\.blogspot\.com') + \
                          add_special_keyword('Download from Wow! eBook <www.wowebook.com>') + \
                          add_special_keyword('www\.dbebooks\.com \- Free Books \& magazines') + \
                          add_special_keyword('Download[[:blank:]]*from[[:blank:]]*www\.eBookTM\.Com') + \
                          add_special_keyword('[\s\S](www\.eBookTM\.Com)$') + \
                          add_special_keyword('eBook from Wow! eBook dot com') + \
                          add_special_keyword('Download from Join eBook (www.joinebook.com)') + \
                          add_special_keyword('Apago PDF Enhancer') + \
                          add_special_keyword('www\.free-ebooks-download\.org') + \
                          add_special_keyword('Download from finelybook www\.finelybook\.com') + \
                          add_special_keyword('BOOKLEET ©') + \
                          add_special_keyword('www.EliteBook.net') + \
                          add_special_keyword('.*joinebook\.com') + \
                          add_special_keyword('Team\-Fly®') + \
                          add_special_keyword('Team LRN') + \
                          add_special_keyword('TLFeBOOK') + \
                          add_special_keyword('www\.sharexxx\.net \- free books \& magazines') + \
                          add_special_keyword('- Live, Informative, Non-cost and Genuine!') + \
                          add_special_keyword('TEAM LinG - Live, Informative, Non-cost and Genuine!') + \
                          add_special_keyword('TEAM LinG - Live, Informative, Non-cost and Genuine !') + \
                          add_special_keyword('TEAM LinG') + \
                          add_special_keyword('From \<www\.wowebook\.com\>') + \
                          add_special_keyword('Download from www\.eBookTM\.com') + \
                          add_special_keyword('.*WoweBook\.Com')  # Download at WoweBook.Com

ARGS = PARSER.parse_args()
PASSED_FILES = ARGS.files[:]
ACTUAL_FILES = []

# Filling up the array with the file paths to be processed
# Checking first if needs to be recursive
if ARGS.recursive:
    print(colored('***Attention*** Recursive mode detected:', "yellow"))
    for arg_file in PASSED_FILES:
        if os.path.exists(arg_file):
            for root, dirs, recursive_files in os.walk(arg_file):
                for file in recursive_files:
                    if os.path.splitext(file)[1] == ".pdf":  # if the file is a PDF, then append to main array
                        ACTUAL_FILES.append(os.path.join(root, file))
        else:
            print(colored("(x) File: " + arg_file + " does not exist", "red"))

if len(ACTUAL_FILES) == 0:
    for file in PASSED_FILES:
        if os.path.isfile(file):
            # if it wasn't recursive, check once again those files are PDFs
            if os.path.splitext(file)[1] == ".pdf":
                ACTUAL_FILES.append(file)
            else:
                print(colored("(x) File: " + file + " is not a pdf", "yellow"))
        else:
            print(colored("(x) " + file + " is not a file or does not exist", "red"))

# at this point `actual_files` should be filled with the paths
if len(ACTUAL_FILES) == 0:
    print(colored("(.) No pdf files detected, nothing to do, exiting...", "yellow"))
    sys.exit()
else:
    print(colored("(.) " + str(len(ACTUAL_FILES)) + " PDFs detected", "green"))
    # If recursive mode on, then show the PDFs detected to be processed
    if len(ACTUAL_FILES) > 0 and ARGS.recursive:
        print(colored("(.) Showing first 10:", "green"))
        COUNT = 0
        for file in ACTUAL_FILES:
            COUNT += 1
            filename = os.path.splitext(os.path.basename(file))[0]
            print("\t" + str(COUNT) + ") " + filename)
            if COUNT == 10:
                break

# show recursive warning
if ARGS.recursive:
    input('Press ENTER to continue or Ctrl-C the shit out')

# begin the actual processing
COUNT = 0
EXIFTOOL_LOG = ""

# perform exiftool processing for changing the 'Title' metadata of the file
for file in ACTUAL_FILES:
    uncompressed_file = file + '_unc'
    sed_file = file + '_unc_sed'
    COUNT += 1
    filename = os.path.splitext(os.path.basename(file))[0]  # getting the basename without the extension (.pdf)
    exiftcmd = ["exiftool", "-Title=" + filename, file]  # put filename to title
    unstamp_cmd = ['java', '-jar',  # the below '+'s because we want all to append into a big array
                   os.getenv('HOME') + '/1w3j/bin/pdf-unstamper.jar'] + \
                  (['-c'] if ARGS.clear else ['']) \
                  + (['-s'] if ARGS.strict else ['']) \
                  + ANNOYINGTATIONS \
                  + ['-d', '-i', file]  # direct output onto file
    unstamp_cmd = [param for param in unstamp_cmd if param]  # cleaning empty elements like ['']
    uncompress_cmd = ['pdftk', file, 'output', uncompressed_file, 'uncompress']
    unstamp_specials_cmd = ['sed'] + SPECIAL_ANNOYINGTATIONS + [uncompressed_file]
    compress_cmd = ['pdftk', sed_file, 'output', file, 'compress']
    exiftool = None

    if not ARGS.dry_mode:
        exiftool = subprocess.Popen(exiftcmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)  # shell=True
        exiftout, exifterr = exiftool.communicate()
        had_warnings = bytes.decode(exifterr).startswith("Warning:")
        remove_previous_line()

        if not ARGS.do_not_remove_annotations and not ARGS.special_annotations and exiftool.wait() == 0:
            print(colored(str(COUNT) + ") Removing annotations on '" + filename[0:60] + "...'", "yellow"))
            unstamp = subprocess.call(unstamp_cmd, stdout=DEVNULL)
            remove_previous_line()

            if unstamp != 0:
                print(colored("Error on removing annotations with exit code " + str(unstamp), "red"))
                sys.exit(unstamp)

        elif ARGS.special_annotations:
            print(colored(str(COUNT) + ") Uncompressing '" + filename[0:60] + "'...", "yellow"))
            uncompress = subprocess.call(uncompress_cmd)
            remove_previous_line()

            if uncompress == 0:
                print(colored(str(COUNT) + ") Removing special annotations on '" + filename[0:60] + "'...", "yellow"))
                unstamp_specials = subprocess.call(unstamp_specials_cmd, stdout=open(sed_file, 'w+'))
                remove_previous_line()

                if unstamp_specials == 0:
                    os.remove(uncompressed_file)
                    print(colored(str(COUNT) + ") Compressing '" + filename[0:60] + "'...", "yellow"))
                    compress = subprocess.call(compress_cmd)
                    remove_previous_line()

                    if compress != 0:
                        print(colored("Error on compressing with exit code " + str(compress), "red"))
                        sys.exit(compress)
                    else:
                        os.remove(sed_file)
                else:
                    print(
                        colored("Error on removing special annotations with exit code " + str(unstamp_specials), "red"))
                    sys.exit(unstamp_specials)
            else:
                print(colored("Error on uncompressing with exit code " + str(uncompress), "red"))
                sys.exit(uncompress)

        if len(bytes.decode(exifterr)) != 0 and not had_warnings:
            EXIFTOOL_LOG = colored(str(COUNT) + ") " + filename[0:60] + ": " + bytes.decode(exifterr), "red")
        elif had_warnings:
            EXIFTOOL_LOG = colored(str(COUNT) + ") " + filename[0:60] + ": " + bytes.decode(exifterr), "yellow")
        else:
            EXIFTOOL_LOG = colored(str(COUNT) + ") " + filename[0:60] + " ✓", "green")

        print(EXIFTOOL_LOG)

        if os.path.exists(file + '_original'):
            os.remove(file + '_original')  # pdf_original file created by exiftool

        if ARGS.output is not None:
            ARGS.output.write(EXIFTOOL_LOG + "\n")
    else:
        print(" ".join(exiftcmd))
        print(" ".join(unstamp_cmd))
        if len(ACTUAL_FILES) == COUNT:
            print(colored(str(COUNT) + " PDF" + ("s are" if COUNT > 1 else " is") + " going to be modified", "green"))
            if ARGS.output is not None:
                print(colored("Output written on " + ARGS.output.name, "green"))
