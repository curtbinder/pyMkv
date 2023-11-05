#!/usr/bin/env python3

"""
Application: app
Author: Curt Binder
"""

import os
import sys
import subprocess
import json

#path = "/home/binder/tmp"
path = ""
subtitle_output = "subtitles"

# collect list of files
all_mkvs = []
# list of mkvs with VOBSUB
vob_mkvs = []

class Subtitle:
    def __init__(self, track_id, codec, codec_id, lang):
        self.track_id = track_id
        self.codec = codec
        self.codec_id = codec_id
        self.lang = lang
        
    def isVobSub(self):
        # Look for codec VobSub or S_VOBSUB, type subtitles
        if self.codec_id == "S_VOBSUB":
            return True
        else:
            return False

    def getFilenameSuffix(self):
        return ".track_" + self.track_id + "." + self.lang + ".sub"

    def __str__(self):
        return "Subtitle: (" + self.track_id + ") " + self.codec + "(" + self.codec_id + ") - " + self.lang


class Mkv:
    # run mkvmerge on each file to get information to process
    # mkvmerge -i -J FILENAME.MKV
    def __init__(self, fullfilename):
        self.fullfilename = fullfilename
        # Get the path it's located
        self.path = os.path.dirname(fullfilename)
        # Get the filename and extension
        (self.name, self.ext) = os.path.splitext(os.path.basename(fullfilename))
        self.title = "Untitled"
        self.subtitles = []

    def loadInfo(self):
        cmd = ["mkvmerge -i -J \"" + self.fullfilename + "\""]
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        json_data, err = proc.communicate()
        json_data = json_data.decode("utf-8")
        ## gets all mkv objects in json format
        json_data = json.loads(json_data)
        
        ## Get the Title
        if "title" in json_data["container"]["properties"]:
            self.title = json_data["container"]["properties"]["title"]

        ## look for subtitles
        ## make sure there is tracks in the file
        if not (json_data.get("tracks") is None):
            ## loop through the tracks, looking for subtitles
            for track in json_data["tracks"]:
                if track["type"] == "subtitles":
                    st = Subtitle(str(track["id"]), track["codec"], track["properties"]["codec_id"], track["properties"]["language"])
                    self.subtitles.append(st)

    def hasSubtitles(self):
        if len(self.subtitles) > 0:
            return True
        else:
            return False

    def hasVobSubtitles(self):
        if self.hasSubtitles():
            for s in self.subtitles:
                if s.isVobSub():
                    # if we find one, break out and return True
                    return True
        return False

    def exportSubtitles(self):
        global subtitle_output
        # Loop through the subtitles
        # if it hasVobSubtitles, then we need to extract them

        if not self.hasSubtitles():
            return;
        
        for s in self.subtitles:
            if s.isVobSub():
                print("Extracting " + self.name + " - track #" + s.track_id)
                # VOB Subtitle, let's extract them
                outfile = os.path.join(subtitle_output, self.name) + s.getFilenameSuffix()
                cmd = ["mkvextract \"" + self.fullfilename + "\" tracks " + s.track_id + ":\"" + outfile + "\""]
                #print(cmd)
                proc = subprocess.call(cmd, shell=True, stdout=subprocess.PIPE)



    def __str__(self):
        s = "Filename: " + self.fullfilename 
        s += "\n  * Name: " + self.name
        s += "\n  * Title: " + self.title
        if self.hasSubtitles:
            s += "\n  * Subtitles: " + str(len(self.subtitles))
            for i in self.subtitles:
                s += "\n    * " + i.__str__()
        return s


##def export_subtitles(file, track, outfile):
##    #print("Export: \n  * " + file + "\n  * " + track + "\n  * " + outfile)
##    cmd = ["mkvextract \"" + file + "\" tracks " + track + ":\"" + outfile + "\""]
##    #print(cmd)
##    proc = subprocess.call(cmd, shell=True, stdout=subprocess.PIPE)

# Scan files
#
# Loop through all mkv's and check for VOBSUB subtitles
# If we find one, add that file to the list of vob_mkvs
# Otherwise, skip the file
def scan_files():
    global all_mkvs
    global vob_mkvs

    for m in all_mkvs:
        #print("Processing %d of %d files..." % (count, total))
        m1 = Mkv(m)
        m1.loadInfo()
        if m1.hasVobSubtitles():
            vob_mkvs.append(m1)

    print("Found %d mkvs with VOBs" % (len(vob_mkvs)))

def extract_subtitles():
    global vob_mkvs

    for m in vob_mkvs:
        m.exportSubtitles()


def main():
    global all_mkvs
    global path
    global vob_mkvs
    global subtitle_output

    if len(sys.argv) > 1:
        if os.path.isdir(sys.argv[1]):
            # valid, so set as default folder
            path = sys.argv[1]
        elif os.path.isdir(os.path.dirname(os.path.abspath(sys.argv[1]))):
            # filepath was sent, use folder from it
            path = os.path.dirname(os.path.abspath(sys.argv[1]))
        else:
            # invalid path, set to current dir where python is
            path = sys.path[0]
    else:
        # no folder set, use current dir
        path = sys.path[0]

    subtitle_output = os.path.join(path, subtitle_output)
    print("Saving subtitles to: " + subtitle_output)
    if not os.path.exists(subtitle_output):
        os.mkdir(subtitle_output)
    if not os.path.exists(subtitle_output):
        print("Cannot create output directory: " + subtitle_output)
        return

    for (root, dirs, file) in os.walk(path):
        for f in file:
            if '.mkv' in f:
                all_mkvs.append(os.path.join(root, f))

    print("Found %d mkvs in: %s" % (len(all_mkvs), path))
    scan_files()
    if len(vob_mkvs) > 1:
       response = input("About to extract subtitles from %d mkvs, proceed? " % (len(vob_mkvs))) 
       if response == 'y':
           extract_subtitles()


if __name__ == "__main__":
    main()
