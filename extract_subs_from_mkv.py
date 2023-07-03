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

# collect list of files
all_mkvs = []
# list of mkvs with VOBSUB
vob_mkvs = []


def export_subtitles(file, track, outfile):
    #print("Export: \n  * " + file + "\n  * " + track + "\n  * " + outfile)
    cmd = ["mkvextract \"" + file + "\" tracks " + track + ":\"" + outfile + "\""]
    #print(cmd)
    proc = subprocess.call(cmd, shell=True, stdout=subprocess.PIPE)

# Process files
#
# Loop through all mkv's and check for VOBSUB subtitles
# If we find one, add that file to the list of vob_mkvs
# Otherwise, skip the file
def process_files():
    global all_mkvs
    global vob_mkvs

    # run mkvmerge on each file to get information to process
    # mkvmerge -i -J FILENAME.MKV
    # Look for codec VobSub or S_VOBSUB, type subtitles

    for m in all_mkvs:
        cmd = ["mkvmerge -i -J \"" + m + "\""]
        #print(cmd)
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        json_data, err = proc.communicate()
        json_data = json_data.decode("utf-8")
        ## gets all mkv objects in json format
        json_data = json.loads(json_data)
        
        path = os.path.dirname(m)
        (name, ext) = os.path.splitext(os.path.basename(m))

        ## look for subtitles
        ## make sure there is tracks in the file
        if not (json_data.get("tracks") is None):
            if "title" in json_data["container"]["properties"]:
                print("Name: " + json_data["container"]["properties"]["title"])
            #print("Name: " + json_data["container"]["properties"]["title"] + " (" + json_data["file_name"] + ")")
            ## loop through the tracks, looking for subtitles
            for track in json_data["tracks"]:
                if track["type"] == "subtitles":
                    track_codec = track["codec"]
                    track_type_id = track["properties"]["codec_id"]
                    track_id = str(track["id"])
                    track_lang = track["properties"]["language"]
                    if track_type_id == "S_VOBSUB":
                        sub_track_filename = name + ".track_" + track_id + "." + track_lang + ".sub"
                        print(" * Subtitle: (" + track_id + ") " + track_codec + "(" + track_type_id + ") - " + track_lang)
#                        export_subtitles(m, track_id, path + "/" + sub_track_filename)

    

def main():
    global all_mkvs
    global path

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

    for (root, dirs, file) in os.walk(path):
        for f in file:
            if '.mkv' in f:
                all_mkvs.append(os.path.join(root, f))

    print("Found %d mkvs in: %s" % (len(all_mkvs), path))
#    for i in all_mkvs:
#        n = os.path.basename(i)
#        (name, ext) = os.path.splitext(n)
#        print("  * " + name + " (" + ext + ") - DIR: " + os.path.dirname(i))
    process_files()



if __name__ == "__main__":
    main()