import numpy as np
import sys, os
from scikits.audiolab import Sndfile


sys.path.append(os.path.join(os.path.dirname(__file__), 'sms-tools/software/transformations/'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'sms-tools/software/models/'))

import utilFunctions as UF
import sineModel as SM 
import sineTransformations as trans
import karaokeParser as KP

root_HodorPath = "HodorSoundsAll"
baseHodorName = "HodorSounds/Hodor1"
toneMappFile = "toneMapping.csv"

def createToneMappFiles(mappFile):

	lines = open(mappFile, 'r').readlines()

	toneMapp={}
	toneMapp['hodor'] = [[] for x in range(12)]
	toneMapp['ho'] = [[] for x in range(12)]
	toneMapp['dor'] = [[] for x in range(12)]

	for line in lines:
		lineSplt = line.split()
		basename = lineSplt[0].strip()
		num1 = lineSplt[1].strip()
		num2 = lineSplt[2].strip()
		num1 = int(num1)
		num2 = int(num2)
		toneMapp['hodor'][num1].append(basename)
		toneMapp['ho'][num1].append(basename+"_ho")
		toneMapp['dor'][num2].append(basename + "_dor")

	return toneMapp



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


def generateHodorTrack(emptyTrack, fs, karaokeData, repMTX):

	for ii, elem in enumerate(karaokeData['data']):

		if elem['syl'] == '-':
			continue

		if elem['processed']==0:#process only when its already not processed
			mtxInd = (elem['durBeats'], elem['tone'])

			duration = elem['end'] - elem['start']
			audio, fs, nChannel = timeStretchAudio(elem['file'], "crap.crap", duration, writeOutput=0)

			for index in repMTX[elem['sylType']][mtxInd[0]][mtxInd[1]]:

				sample1 = np.round(karaokeData['data'][index]['start']*fs).astype(np.int)
				emptyTrack[sample1:sample1 + len(audio)] +=  audio
				karaokeData['data'][index]['processed'] = 1 

	return emptyTrack

def hodorFileSelection(karaokeData, toneMapp):

	for ii, elem in enumerate(karaokeData['data']):

		if elem['syl'] == '-':
			continue

		karaokeData['data'][ii]['file'] = os.path.join(root_HodorPath , "Clean5" + ".wav")

		"""
		tone = elem['tone']-12
		toneDiff = tone - 53
		if abs(toneDiff) > 24:
			karaokeData['data'][ii]['file'] = os.path.join(root_HodorPath , "Hodor1" + ".wav")
			continue
		if toneDiff > 0:
			karaokeData['data'][ii]['file'] = os.path.join(root_HodorPath , "Hodor1" + "P" + str(toneDiff) + "_" + elem['sylType'] + ".wav")
		if toneDiff < 0:
			karaokeData['data'][ii]['file'] = os.path.join(root_HodorPath , "Hodor1" + "M" + str(abs(toneDiff)) + "_" + elem['sylType'] + ".wav")
		if toneDiff  == 0:
			karaokeData['data'][ii]['file'] = os.path.join(root_HodorPath , "Hodor1" + "_" + elem['sylType'] + ".wav")
		"""
		"""
		if elem['end'] - elem['start'] > 0.3:
			karaokeData['data'][ii]['file'] = os.path.join(root_HodorPath , toneMapp['hodor'][np.mod(elem['tone'],12)][0] + ".wav")
		else:
			karaokeData['data'][ii]['file'] = os.path.join(root_HodorPath , toneMapp['ho'][np.mod(elem['tone'],12)][0] + ".wav")
		"""
		"""
		if ii%2 == 0:
			karaokeData['data'][ii]['file'] = os.path.join(root_HodorPath , toneMapp['ho'][np.mod(elem['tone'],12)][0] + ".wav")
		else:
			karaokeData['data'][ii]['file'] = os.path.join(root_HodorPath , toneMapp['dor'][np.mod(elem['tone'],12)][0] + ".wav")
		"""

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


def estimateRepetitiveHodors(karaokeData):

	repMTX_s = np.empty((100,100)).tolist()#dur,tone

	totalHodors = 0
	totalProcessHodors = 0

	for ii in range(100):
		for jj in range(100):
			repMTX_s[ii][jj]=[]

	repMTX = {}
	repMTX['ho'] = repMTX_s
	repMTX['dor'] = repMTX_s

	for ii,elem in enumerate(karaokeData['data']):
		if not elem['syl'] == '-':
			repMTX[elem['sylType']][elem['durBeats']][elem['tone']].append(ii)
			totalHodors+=1

	for ii in range(100):
		for jj in range(100):
			if len(repMTX['ho'][ii][jj])>0:
				totalProcessHodors+=1
			if len(repMTX['dor'][ii][jj])>0:
				totalProcessHodors+=1

	print "I have to process %d hodors out of %d hodors"%(totalProcessHodors, totalHodors)

	return repMTX

def hodorifyIt(inputFile, outputFile, karaokeExt = '.txt'):

	#reading input wave file
	inputAudio = Sndfile(inputFile, 'r')
	audio = inputAudio.read_frames(inputAudio.nframes)
	nframes = inputAudio.nframes
	fs = inputAudio.samplerate
	nChannel = inputAudio.channels

	fname, ext = os.path.splitext(inputFile)
	karaokeFile  = fname + karaokeExt

	#parse the karaoke file
	karaokeData = KP.parseKaraokeFile(karaokeFile)


	#assign which syllable to use ho and which ones to use dor
	toogle = 0
	sylType = ['ho', 'dor']
	for ii,elem in enumerate(karaokeData['data']):
		if elem['syl'] == '-':
			toogle =0
			continue
		karaokeData['data'][ii]['sylType'] = sylType[toogle]
		toogle = (toogle +1)%2

	dumpSonicVisualizerAnnotFile("tryHODOR.txt", karaokeData['data'])

	#initialize all the hodor locations with not processed flag (later to be for exploiting repetitive hodors)
	for ii,elem in enumerate(karaokeData['data']):
		karaokeData['data'][ii]['processed']=0

	#creating mapping between file names and tones
	toneMapp = createToneMappFiles(toneMappFile)

	#processHere the logic for Hodor input file for each word
	karaokeData = hodorFileSelection(karaokeData, toneMapp)

	#do center channel cut
	audio = cutCenterChannel(audio, fs, karaokeData)

	#estimate the possible repetitions in the karaoke data, i.e. output with same note and duration
	print len(karaokeData['data'])
	repMTX = estimateRepetitiveHodors(karaokeData)

	emptyTrack  = np.zeros(len(audio))
	emptyTrack = generateHodorTrack(emptyTrack, fs, karaokeData, repMTX)

	audio[:,1] = audio[:,1] + emptyTrack
	audio[:,0] = audio[:,0] + emptyTrack

	outputWav = Sndfile(outputFile, 'w', inputAudio.format, inputAudio.channels, inputAudio.samplerate)
	outputWav.write_frames(audio)
	outputWav.close()

def dumpSonicVisualizerAnnotFile(fileOut, data):
	
	fid = open(fileOut, "w")

	for elem in data:
		if elem['syl'] == '-':
			fid.write("%f\t%f\t%s\n"%(elem['start'], elem['end'], '-'))
		else:
			fid.write("%f\t%f\t%s\n"%(elem['start'], elem['end'], elem['sylType']))

	fid.close()


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