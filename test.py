#!/usr/bin/python3

import pickle
from datetime import datetime

data = [
0.983058651318658,
0.747032599868739,
0.106200940432131,
0.484574064255626,
0.182605114929373,
0.110053847578471,
0.768835588331604,
0.0979312269590905,
0.424184388921786,
0.664530909547089,
0.753892020019624,
0.447441556932082,
0.206709949995135,
0.803445866165552,
0.0816145880781307,
0.962726959444159,
0.842091010221827,
0.171857762012491,
0.0236676151003407,
0.0267820952751764,
0.279580755113696,
0.185762250008242,
0.905829496025138,
0.390431372424318,
0.556172282156086,
0.371249207925223,
0.255018742361158,
0.328003014907886,
0.656013246732583,
0.328719767254114,
0.728396130771338,
0.690809730796152,
0.536213904812621,
0.552165132854845,
0.0551810490581436,
0.848050472828264,
0.116235698209639,
0.0683244613110357,
0.189001889015015,
0.200091985539479,
0.749202376311219,
0.540395300903586,
0.0327291877640828,
0.339928227205328,
0.948838222031774,
0.0326807442822063,
0.807382277851158,
0.920452012469728,
0.847718927398651,
0.835035809885776,
0.659535647566703,
0.624499822445363,
0.356879904663657,
0.376121859669596,
0.964386109590218,
0.179566394410674,
0.478433188334558,
0.477954966087972,
0.0313390123774007,
0.205570668206455,
0.651654179609579,
0.681645593946744,
0.863952560158145,
0.236885542247641,
0.794962115475693,
0.548702271520245,
0.626134267363322,
0.517309344644538,
0.437875299908031,
0.53901982472057,
0.856594862267945,
0.547605594186268,
0.333004376768045,
0.633860808256145,
0.210518090146797,
0.0792604832128147,
0.119315246456834,
0.647299123613803,
0.404464503454349,
0.63639891470773,
0.261666682212729,
0.816005902917805,
0.455121579423554,
0.575865091205936,
0.662972856727421,
0.297965689007117,
0.653363349699988,
0.71350318466724,
0.649425053022067,
0.205419572569662,
0.319327973769373,
0.612921847193174,
0.0647732587850316,
0.0872578977743028,
0.931433715403832,
0.449741312169059,
0.0660298333233022,
0.00598793938140019,
0.238963438728654,
0.0840169868377717,
0.0273859332241021
]

#constants
def cSINGLEEVENTFILE():
	return 'single_events.txt'

def cAVERAGEDATAFILE():
	return 'pm_hourly_avg.txt'

#variables
idx = 0
noOfVals = 0
avgPM2_5val = 0
avgPM10_val = 0
currPM2_5val = 0
currPM10_val = 0
dateString = ""

tsCurrRunDate = datetime.now() #get timestamp of current script run
#open last processed single event data file or create if not existing
try:
	fRd = open(cSINGLEEVENTFILE(), 'rb')
except IOError:
	#there is no single event file existing
	nOfVals = 0 #no data stored already
	tsPrevRunDate = tsCurrRunDate #there is no previous run time so use the current one
	uiDataStoredThisHour = 0 #indicator that the average result file was already written when 1
	print("IOError")
else:
	#single event file exists and could be opened
	dataToRead = pickle.load(fRd) #read in the file content into a pickled list
	fRd.close() #close the file that was opened for reading
	noOfVals = dataToRead[0]
	tsPrevRunDate = datetime.strptime(dataToRead[1], '%Y-%m-%d %H:%M:%S.%f') #convert the read date string into a timestamp
	avgPM2_5val = dataToRead[2]
	avgPM10_val = dataToRead[3]
	uiDataStoredThisHour = dataToRead[4]
	print("else of try")
idx = noOfVals

#get fictive measurement data
if (idx < 100):
	currPM2_5val = data[idx]
	currPM10_val = data[idx]*5
	idx = idx + 1
	print("idx < 100")
else:
	idx = 0
	currPM2_5val = data[idx]
	currPM10_val = data[idx]*5
	print("else of idx < 100")

#check if previous stored call and current call are in the same hour
prevHr = "{:%H}".format(tsPrevRunDate)
currHr = "{:%H}".format(tsCurrRunDate)
currMin = "{:%M}".format(tsCurrRunDate)
if (tsPrevRunDate == tsCurrRunDate):
	#this happens only if no previous data are stored	
	avgPM2_5val = ((noOfVals * avgPM2_5val) + currPM2_5val)/(noOfVals + 1)
	avgPM10_val = ((noOfVals * avgPM10_val) + currPM10_val)/(noOfVals + 1)
	noOfVals = 1
elif (prevHr == currHr):
	#when the calls are within the same hour average the values
	avgPM2_5val = ((noOfVals * avgPM2_5val) + currPM2_5val)/(noOfVals + 1)
	avgPM10_val = ((noOfVals * avgPM10_val) + currPM10_val)/(noOfVals + 1)
	noOfVals = noOfVals + 1
	print("prevHr == currHr")
else:
	#when the calls are in different hours start the averaging again
	noOfVals = 0 #reset the number of values used for averaging
	uiDataStoredThisHour = 0 #reset the indicator that data of the current hour were written already
	avgPM2_5val = ((noOfVals * avgPM2_5val) + currPM2_5val)/(noOfVals + 1)
	avgPM10_val = ((noOfVals * avgPM10_val) + currPM10_val)/(noOfVals + 1)
#prepare data to be written to result file
dateString = "{:%Y-%m-%d %H:%M:%S.%f}".format(tsCurrRunDate)
if ((int(currMin) >= 49) & (uiDataStoredThisHour == 0)):
	uiDataStoredThisHour = 1
	#prepare data to be written to result file
	avgDataToWrite = [dateString, avgPM2_5val, avgPM10_val]
	#write final result file
	fWr = open(cAVERAGEDATAFILE(), 'wb') #open the hourly average data file for writing
	pickle.dump(avgDataToWrite, fWr, protocol=0)  #write the pickled list to the file
	fWr.close() #close the write file
#prepare data to be written to result file
dataToWrite = [noOfVals, dateString, avgPM2_5val, avgPM10_val, uiDataStoredThisHour]
print(dataToWrite)
#write data to result file
fWr = open(cSINGLEEVENTFILE(), 'wb') #open the single event file for writing
pickle.dump(dataToWrite, fWr)  #write the pickled list to the file
fWr.close() #close the write file


