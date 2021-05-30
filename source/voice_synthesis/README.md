# BASECAMP TTS

## Purpose

This source code create a TTS server to easily generate wav files from unicode text.<br>
It will be used by Basecamp to make vocal announcements.

## Install

1) Install a fresh Windows 7 OS
2) Install a SAPI voice. I personnaly recommend the Best-Of-vox windows voices from https://best-of-vox.com/windows (_40€ each, very good voices_)
3) Install this source code along with python 2.7 and pip (I didn't test under python 3, but that should be easily adapted)
4) run `create_speechlib.py` to generate the Speechlib module
5) modify `bc_TTS.py` and `cleanup.py` for the `os.chdir` parameter to match your own absolute local path (here you should replace `bc-annex.local` with your hostname).
6) run `bc_TTS.py` and open a browser to http://<yourhostname>/alive, that should bring an '_OK_' answer.
7) open a browser to http://<yourhostname>/TTS?text=Hello%20my%20dear and then get the wav file using the returned URL. Play it, it should match your text...
8) run the windows task scheduler: `Taskschd.msc` and create two tasks, one that will run `bc_TTS.py` at boot, and the other to run `bc_TTS.py` every day (it will wipe the previous day's wav files)

Enjoy! (^_^)

_Nicolas._