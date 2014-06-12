import numpy as np
import sys, os
from scikits.audiolab import Sndfile


sys.path.append(os.path.join(os.path.dirname(__file__), 'sms-tools/software/transformations/'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'sms-tools/software/models/'))

import utilFunctions as UF
import sineModel as SM 
import sineTransformations as trans
import karaokeParser as KP


def timeStretchAudio(inputAudio, outputAudio, outputDuration, writeOutput=1):

	originalWav = Sndfile(inputAudio, 'r')
	x = originalWav.read_frames(originalWav.nframes)
	fs = originalWav.samplerate
	nChannel = originalWav.channels
	print fs
	if nChannel >1:
		x = x[0]


	w = np.hamming(801)
	N = 2048
	t = -90
	minSineDur = .005
	maxnSines = 150
	freqDevOffset = 20
	freqDevSlope = 0.02
	Ns = 512
	H = Ns/4
	tfreq, tmag, tphase = SM.sineModelAnal(x, fs, w, N, H, t, maxnSines, minSineDur, freqDevOffset, freqDevSlope)
	inputDur = float(len(tfreq)*H/fs)
	#timeScale = np.array([0.1,0.1, inputDur, inputDur*2])
	timeScale = np.array([0,0, .4,outputDuration])

	ytfreq, ytmag = trans.sineTimeScaling(tfreq, tmag, timeScale)
	y = SM.sineModelSynth(ytfreq, ytmag, np.array([]), Ns, H, fs)
	
	if writeOutput ==1:
		outputWav = Sndfile(outputAudio, 'w', originalWav.format, originalWav.channels, originalWav.samplerate)
		outputWav.write_frames(y)
		outputWav.close()
	else:
		return y, fs, nChannel


def generateHodorTrack(emptyTrack, fs, karaokeData):

	for ii, elem in enumerate(karaokeData['data']):

		duration = elem['end'] - elem['start']
		audio, fs, nChannel = timeStretchAudio(elem['file'], "crap.crap", duration, writeOutput=0)

		sample1 = np.round(elem['start']*fs).astype(np.int)
		emptyTrack[sample1:sample1 + len(audio)] +=  audio

	return emptyTrack

def hodorFileSelection(karaokeData):

	for ii, elem in enumerate(karaokeData['data']):

		karaokeData['data'][ii]['file'] = "HodorSounds/clean5.wav"


	return karaokeData

def cutCenterChannel(audio, fs, karaokeData):

	for ii, elem in enumerate(karaokeData['data']):
		if not elem['syl']=='-':
			sample1 = np.round(elem['start']*fs).astype(np.int)
			sample2 = np.round(elem['end']*fs).astype(np.int)
			diffChannel = audio[sample1:sample2,1]-audio[sample1:sample2,0]
			audio[sample1:sample2,1] = diffChannel
			audio[sample1:sample2,0] = diffChannel

	return audio



def hodorifyIt(inputFile, outputFile, karaokeExt = '.txt'):

	#reading input wave file
	inputAudio = Sndfile(inputFile, 'r')
	audio = inputAudio.read_frames(inputAudio.nframes)
	nframes = inputAudio.nframes
	fs = inputAudio.samplerate
	nChannel = inputAudio.channels

	fname, ext = os.path.splitext(inputFile)
	karaokeFile  = fname + karaokeExt

	karaokeData = KP.parseKaraokeFile(karaokeFile)

	#processHere the logic for Hodor input file for each word
	karaokeData = hodorFileSelection(karaokeData)

	#do center channel cut
	audio = cutCenterChannel(audio, fs, karaokeData)


	emptyTrack  = np.zeros(len(audio))
	emptyTrack = generateHodorTrack(emptyTrack, fs, karaokeData)

	audio[:,1] = audio[:,1] + emptyTrack
	audio[:,0] = audio[:,0] + emptyTrack

	outputWav = Sndfile(outputFile, 'w', inputAudio.format, inputAudio.channels, inputAudio.samplerate)
	outputWav.write_frames(audio)
	outputWav.close()



if __name__ == "__main__":

	inputFile = sys.argv[1]
	outputFile = sys.argv[2]

	hodorifyIt(inputFile, outputFile)

"""
	#This part of code is to just check time transformation
	inputfile = sys.argv[1]
	outputfile = sys.argv[2]
	outDuration = float(sys.argv[3])
	timeStretchAudio(inputfile, outputfile, outDuration)

"""