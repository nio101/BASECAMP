#!/usr/bin/env python
# -*- coding: UTF-8-*-

# clean *.wav files older than 3 days

import glob
import os
import time


now = time.time()
os.chdir("C:\\Users\\nio\Desktop\\bc_TTS\\wav")
for filename in glob.glob("*.wav"):
	if (os.stat(filename).st_mtime < (now - 1*86400)):
		print "removing:", filename
		os.remove(filename)
