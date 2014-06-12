#import numpy as np
import sys

tagKeys = ['TITLE', 'ARTIST', 'LANGUAGE', 'MP3', 'COVER', 'BACKGROUND', 'BPM', 'GAP', 'EDITION']

class MyError(Exception):
	def __init__(self, value):
		self.value = value
	def __str__(self):
		return repr(self.value)


def parseKaraokeFile(karaokeTxtFile):

	lines = open(karaokeTxtFile,'r').readlines()

	fileContent = {}
	fileContent['data'] = []

	Offset = -1
	durPBeat = -1

	for line in lines:
		if line.startswith("E"):
			break
		#Parsing tags
		if line.startswith('#'):
			try: 
				tag, content = parseTagLine(line)
				fileContent[tag] = content
				if tag == 'GAP':
					Offset = content
				if tag == 'BPM':
					durPBeat = 60.0/(4*float(content))
				continue
			except MyError as e:
				print e.value
				continue

		#Parse the data
		if not fileContent.has_key('BPM'):
			print "BPM tag not parsed correctly"
			raise MyError('BPM_Not_Parsed')

		lineSplt = line.split()

		if len(lineSplt) == 5: #normal frame
			start_time = Offset + float(lineSplt[1])*durPBeat
			end_time = start_time + float(lineSplt[2])*durPBeat
			fileContent['data'].append({'type': lineSplt[0], 'start': start_time, 'end': end_time, 'tone':int(lineSplt[3]), 'syl':lineSplt[4]})		
		else:
			if lineSplt[0] == '-':
				fileContent['data'].append({'type': lineSplt[0], 'start': -1, 'end': -1, 'tone':-1, 'syl':'-'})
			else:
				print line
				print "This is something really wierd happening here X1"
				raise MyError('ParsingError')

	# in addition filling start and end point of the silence regions as well
	for ii, elem in enumerate(fileContent['data']):
		if elem['type'] == '-':
			fileContent['data'][ii]['start'] = fileContent['data'][ii-1]['end']
			fileContent['data'][ii]['end'] = fileContent['data'][ii+1]['start']

	#print Offset, durPBeat
	#print fileContent
	dumpSonicVisualizerAnnotFile('Test.txt', fileContent['data'])

def dumpSonicVisualizerAnnotFile(fileOut, data):
	
	fid = open(fileOut, "w")

	for elem in data:
		fid.write("%f\t%f\t%s\n"%(elem['start'], elem['end'], elem['syl']))

	fid.close()


def parseTagLine(tagline):

	tagline = tagline.strip('#')
	for tag in tagKeys:
		if tagline.startswith(tag):
			content = tagline.strip(tag).strip(':').strip()
			if tag == 'BPM':
				content = float(content.replace(',', '.'))
			if tag == 'GAP':
				content = float(content)/1000.0
			return tag, content

	raise MyError("InvalidTag")







#TITLE:Liebeslied
#ARTIST:Bodo Wartke
#LANGUAGE:English
#MP3:Bodo Wartke - Liebeslied.mp3
#COVER:Bodo Wartke - Liebeslied [CO].jpg
#BACKGROUND:Bodo Wartke - Liebeslied [BG].jpg
#BPM:313,7
#GAP:14330	


if __name__ == "__main__":

	karaokeTxtFile = sys.argv[1]
	parseKaraokeFile(karaokeTxtFile)