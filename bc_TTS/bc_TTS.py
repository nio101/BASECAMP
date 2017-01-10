#!/usr/bin/env python
# -*- coding: UTF-8-*-

from bottle import route, run, get, static_file, response, request
import datetime
from comtypes.client import CreateObject
from comtypes.gen import SpeechLib
import sys
import os


@get('/alive')
def do_alive():
    return "OK"


@get('/TTS')
def do_TTS():
    uni_text = request.query.text
    print uni_text
    filename = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")+".wav"
    print "=>", filename
    stream.Open(filename, SpeechLib.SSFMCreateForWrite)
    engine.AudioOutputStream = stream
    engine.speak(uni_text)
    stream.Close()
    return "http://bc-annex.local/wav/"+filename


@route('/wav/<filename>')
def callback(filename):
    return static_file(filename, root='')


engine = CreateObject("SAPI.SpVoice")
stream = CreateObject("SAPI.SpFileStream")
engine.Voice=engine.GetVoices().Item(0)
engine.Rate = 2
os.chdir("C:\\Users\\nio\Desktop\\bc_TTS\\wav")
run(host='bc-annex.local', port=80)
