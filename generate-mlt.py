#!/opt/homebrew/opt/python@3.9/libexec/bin/python
import sys
import os
from os import path
import glob
import wave, contextlib
import uuid
import time, math
import xml.etree.ElementTree as ET
from xml.dom.minidom import parseString
import subprocess

def seconds_to_hms(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:02}:{m:02}:{s:06.3f}"

def get_label_in_out(filename):
    FRAME_RATE = 24

    def seconds_to_frames(value):
        # Truncate to 3 decimals, then convert to frames (round down)
        truncated = math.trunc(value * 1000) / 1000.0
        frames = int(truncated * FRAME_RATE)
        return round(frames / FRAME_RATE, 3)

    in_out_list = []
    with open(filename) as f:
        lines = [line.strip() for line in f if line.strip() and line[0].isdigit()]
    for line in lines:
        parts = line.split()
        if len(parts) == 2:
            val0 = seconds_to_frames(float(parts[0]))
            val1 = seconds_to_frames(float(parts[1]))
            if val0 == val1:
                in_out_list.append(val0)
            else:
                in_out_list.append((val0, val1))
        elif len(parts) == 1:
            val = seconds_to_frames(float(parts[0]))
            in_out_list.append(val)
    # If single column, convert to (in, out) pairs
    if in_out_list and isinstance(in_out_list[0], float):
        times = in_out_list
        in_times = [0.0] + times[:-1]
        out_times = times
        return list(zip(in_times, out_times))
    else:
        return in_out_list

#
# Main Code Starts
#
ASTRING='BKS'

wavefilename="/Users/rajaramaniyer/Downloads/" + ASTRING + ".wav"
if not os.path.exists(wavefilename):
    input(wavefilename + " does not exists")
    sys.exit()

duration="00:00:00.000"
durationSeconds=0.0
with contextlib.closing(wave.open(wavefilename,'r')) as f:
    frames = f.getnframes()
    rate = f.getframerate()
    durationSeconds = float(frames) / float(rate)
    duration = seconds_to_hms(durationSeconds)

labelTrackFile="/Users/rajaramaniyer/Downloads/" + ASTRING + '.txt'
if not os.path.exists(labelTrackFile):
    input(labelTrackFile + " does not exists")
    sys.exit()

labelTrack = get_label_in_out(labelTrackFile)

audioHash=uuid.uuid4().hex

tractor_id=0
transition_id=0

block1=[]
block2=[]
block3=[]
block4=[]
block2.append('  <playlist id="main_bin">\n')
block2.append('    <property name="xml_retain">1</property>\n')
block2.append('    <entry producer="chain0" in="00:00:00.000" out="{}"/>\n'.format(duration))
#
block4.append('  <playlist id="playlist0">\n')
block4.append('    <property name="shotcut:video">1</property>\n')
block4.append('    <property name="shotcut:name">V1</property>\n')

id=0
files=sorted(glob.glob("/Users/rajaramaniyer/Downloads/" + ASTRING + "/" + ASTRING + "-Slide????.png"))

if len(files) == 0:
    print("Slides are missing. run generate-ppt")
    input ("Press enter to continue...")

equalslideduration=float(durationSeconds/len(files))
if len(labelTrack) > 0 and len(files)-1 != len(labelTrack):
    print("WARNING: labelTrack and slideCount are Not in sync.")
    print("There are %d labels while there are %d slides" %(len(labelTrack), len(files)))
    input ("Press enter to continue...")

id=0
prevmarker=0
prevlabelpos=0.0
for slidename in files:
    if id < len(labelTrack):
        in_times, out_times = labelTrack[id]
        slideduration = out_times - in_times
    else:
        slideduration = equalslideduration
    tstart = slideduration - 0.6
    #
    hashvalue=uuid.uuid4().hex
    #
    block1.append('  <producer id="producer{id}" in="00:00:00.000" out="03:59:59.960">\n'.format(id=id))
    block1.append('    <property name="length">04:00:00.000</property>\n')
    block1.append('    <property name="eof">pause</property>\n')
    block1.append('    <property name="resource">{slidename}</property>\n'.format(slidename=slidename))
    block1.append('    <property name="ttl">1</property>\n')
    block1.append('    <property name="aspect_ratio">1</property>\n')
    block1.append('    <property name="progressive">1</property>\n')
    block1.append('    <property name="seekable">1</property>\n')
    block1.append('    <property name="mlt_service">qimage</property>\n')
    block1.append('    <property name="creation_time">{currentTime}</property>\n'.format(currentTime=time.strftime("%Y-%m-%dT%H:%M:%S",time.localtime())))
    block1.append('    <property name="shotcut:hash">{hashvalue}</property>\n'.format(hashvalue=hashvalue))
    block1.append('    <property name="xml">was here</property>\n')
    block1.append('  </producer>\n')

    if 'Slide0001' not in slidename:
        block1.append('  <tractor id="tractor{tractor_id}" in="00:00:00.000" out="00:00:00.600">\n'.format(tractor_id=tractor_id))
        block1.append('    <property name="shotcut:transition">lumaMix</property>\n')
        block1.append('    <track producer="producer{id}" in="{tstart}" out="{slideduration}"/>\n'.format(id=id-1,tstart=seconds_to_hms(tstart),slideduration=seconds_to_hms(slideduration)))
        block1.append('    <track producer="producer{id}" in="00:00:00.000" out="00:00:00.600"/>\n'.format(id=id))
        block1.append('    <transition id="transition{transition_id}" out="00:00:00.600">\n'.format(transition_id=transition_id))
        block1.append('      <property name="a_track">0</property>\n')
        block1.append('      <property name="b_track">1</property>\n')
        block1.append('      <property name="factory">loader</property>\n')
        block1.append('      <property name="mlt_service">luma</property>\n')
        block1.append('      <property name="alpha_over">1</property>\n')
        block1.append('    </transition>\n')
        block1.append('    <transition id="transition{transition_id}" out="00:00:00.600">\n'.format(transition_id=transition_id+1))
        block1.append('      <property name="a_track">0</property>\n')
        block1.append('      <property name="b_track">1</property>\n')
        block1.append('      <property name="start">-1</property>\n')
        block1.append('      <property name="accepts_blanks">1</property>\n')
        block1.append('      <property name="mlt_service">mix</property>\n')
        block1.append('    </transition>\n')
        block1.append('  </tractor>\n')
        tractor_id+=1
        transition_id+=2

    #
    block2.append('    <entry producer="producer{id}" in="00:00:00.000" out="00:00:03.960"/>\n'.format(id=id))
    #
    block3.append('  <producer id="producer{id}" in="00:00:00.000" out="03:59:59.960">\n'.format(id=id+len(files)))
    block3.append('    <property name="length">04:00:00.000</property>\n')
    block3.append('    <property name="eof">pause</property>\n')
    block3.append('    <property name="resource">{slidename}</property>\n'.format(slidename=slidename))
    block3.append('    <property name="ttl">1</property>\n')
    block3.append('    <property name="aspect_ratio">1</property>\n')
    block3.append('    <property name="progressive">1</property>\n')
    block3.append('    <property name="seekable">1</property>\n')
    block3.append('    <property name="mlt_service">qimage</property>\n')
    block3.append('    <property name="shotcut:hash">{hashvalue}</property>\n'.format(hashvalue=hashvalue))
    block3.append('    <property name="creation_time">2021-07-10T13:27:34</property>\n')
    block3.append('    <property name="xml">was here</property>\n')
    block3.append('    <property name="shotcut:caption">{slidename}</property>\n'.format(slidename=slidename))
    block3.append('  </producer>\n')
    #
    block4.append('    <entry producer="producer{id}" in="00:00:00.000" out="{tstart}"/>\n'.format(id=id+len(files),tstart=seconds_to_hms(tstart)))
    block4.append('    <entry producer="tractor{tractor_id}" in="00:00:00.000" out="00:00:00.600"/>\n'.format(tractor_id=tractor_id))
    #
    id=id+1
#
block2.append('  </playlist>\n')
block2.append('  <producer id="black" in="00:00:00.000" out="{duration}">\n'.format(duration=duration))
block2.append('    <property name="length">{duration}</property>\n'.format(duration=duration))
block2.append('    <property name="eof">pause</property>\n')
block2.append('    <property name="resource">0</property>\n')
block2.append('    <property name="aspect_ratio">1</property>\n')
block2.append('    <property name="mlt_service">color</property>\n')
block2.append('    <property name="mlt_image_format">rgba</property>\n')
block2.append('    <property name="set.test_audio">0</property>\n')
block2.append('  </producer>\n')
block2.append('  <playlist id="background">\n')
block2.append('    <entry producer="black" in="00:00:00.000" out="{duration}"/>\n'.format(duration=duration))
block2.append('  </playlist>\n')
#
block4.append('  </playlist>\n')
block4.append('  <chain id="chain1" out="{duration}">\n'.format(duration=duration))
block4.append('    <property name="length">{duration}</property>\n'.format(duration=duration))
block4.append('    <property name="eof">pause</property>\n')
block4.append('    <property name="resource">{wavefilename}</property>\n'.format(wavefilename=wavefilename))
block4.append('    <property name="mlt_service">avformat-novalidate</property>\n')
block4.append('    <property name="seekable">1</property>\n')
block4.append('    <property name="audio_index">0</property>\n')
block4.append('    <property name="video_index">-1</property>\n')
block4.append('    <property name="mute_on_pause">0</property>\n')
block4.append('    <property name="shotcut:hash">{audioHash}</property>\n'.format(audioHash=audioHash))
block4.append('    <property name="shotcut:caption">{wavefilename}</property>\n'.format(wavefilename=os.path.basename(wavefilename)))
block4.append('  </chain>\n')
block4.append('  <playlist id="playlist1">\n')
block4.append('    <property name="shotcut:audio">1</property>\n')
block4.append('    <property name="shotcut:name">A1</property>\n')
block4.append('    <entry producer="chain1" in="00:00:00.000" out="{duration}"/>\n'.format(duration=duration))
block4.append('  </playlist>\n')
block4.append('  <tractor id="tractor{tractor_id}" title="Shotcut version 21.10.31" in="00:00:00.000" out="{duration}">\n'.format(tractor_id=tractor_id,duration=duration))
block4.append('    <property name="shotcut">1</property>\n')
block4.append('    <property name="shotcut:projectAudioChannels">2</property>\n')
block4.append('    <property name="shotcut:projectFolder">0</property>\n')
block4.append('    <track producer="background"/>\n')
block4.append('    <track producer="playlist0"/>\n')
block4.append('    <track producer="playlist1" hide="video"/>\n')
block4.append('    <transition id="transition{transition_id}">\n'.format(transition_id=transition_id))
block4.append('      <property name="a_track">0</property>\n')
block4.append('      <property name="b_track">1</property>\n')
block4.append('      <property name="mlt_service">mix</property>\n')
block4.append('      <property name="always_active">1</property>\n')
block4.append('      <property name="sum">1</property>\n')
block4.append('    </transition>\n')
block4.append('    <transition id="transition{transition_id}">\n'.format(transition_id=(transition_id+1)))
block4.append('      <property name="a_track">0</property>\n')
block4.append('      <property name="b_track">1</property>\n')
block4.append('      <property name="version">0.9</property>\n')
block4.append('      <property name="mlt_service">frei0r.cairoblend</property>\n')
block4.append('      <property name="threads">0</property>\n')
block4.append('      <property name="disable">1</property>\n')
block4.append('    </transition>\n')
block4.append('    <transition id="transition{transition_id}">\n'.format(transition_id=(transition_id+2)))
block4.append('      <property name="a_track">0</property>\n')
block4.append('      <property name="b_track">2</property>\n')
block4.append('      <property name="mlt_service">mix</property>\n')
block4.append('      <property name="always_active">1</property>\n')
block4.append('      <property name="sum">1</property>\n')
block4.append('    </transition>\n')
block4.append('  </tractor>\n')
block4.append('</mlt>\n')

dir_path = os.path.dirname(os.path.realpath(__file__)).replace("\\","/")
filename="/Users/rajaramaniyer/Downloads/" + ASTRING + ".mlt"
f = open(filename, "w")

f.write('<?xml version="1.0" standalone="no"?>\n')
f.write('<mlt LC_NUMERIC="C" version="7.1.0" title="Shotcut version 21.10.31" producer="main_bin">\n')
f.write('  <profile description="PAL 4:3 DV or DVD" width="1920" height="1080" progressive="1" sample_aspect_num="1" sample_aspect_den="1" display_aspect_num="16" display_aspect_den="9" frame_rate_num="24" frame_rate_den="1" colorspace="709"/>\n')
f.write('  <chain id="chain0" out="{duration}">\n'.format(duration=duration))
f.write('    <property name="length">{duration}</property>\n'.format(duration=duration))
f.write('    <property name="eof">pause</property>\n')
f.write('    <property name="resource">{wavefilename}</property>\n'.format(wavefilename=wavefilename))
f.write('    <property name="mlt_service">avformat-novalidate</property>\n')
f.write('    <property name="seekable">1</property>\n')
f.write('    <property name="audio_index">0</property>\n')
f.write('    <property name="video_index">-1</property>\n')
f.write('    <property name="mute_on_pause">0</property>\n')
f.write('    <property name="xml">was here</property>\n')
f.write('    <property name="shotcut:hash">{audioHash}</property>\n'.format(audioHash=audioHash))
f.write('  </chain>\n')

for block in block1:
    f.write(block)
for block in block2:
    f.write(block)
for block in block3:
    f.write(block)
for block in block4:
    f.write(block)
f.close();

