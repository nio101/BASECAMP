# coding: utf-8

from comtypes.client import CreateObject
from comtypes.gen import SpeechLib

engine = CreateObject("SAPI.SpVoice")
stream = CreateObject("SAPI.SpFileStream")

outfile = "test.wav"
stream.Open(outfile, SpeechLib.SSFMCreateForWrite)
engine.AudioOutputStream = stream

print engine.GetVoices().Count
engine.Voice=engine.GetVoices().Item(1)
engine.Rate = 2

engine.speak(u'La température extérieure est de 4,7°Centigrades.')
engine.speak(u"Bonsoir Nicolas... Est-ce que ta journée de travail s'est bien passée?")
engine.speak(u"La factrice est passée, ce matin. Et on a sonné deux fois à la porte, à 17h34 et 18h27, en ton absence.")

stream.Close()
