#2022-11-08
#A set of functions to retrieve ID Gap and shift values and drive them

import time
import requests
import urllib.parse as urlparse
import datetime
import json
import epics
import numpy as np

### ID names  ###
IDs={  '1': 'U125/2',
        '2':'U49/2',  
        '3':'U41',
        '4':'UE49/1',
        '5':'UE49',
        '6':'UE52',
        '7':'UE46',
        '8':'U139',
        '9':'UE56/1',
        '10':'U17',
        '11':'UE48',
        '12':'UE112',
        '13':'U56/2'}
#ID PV Heads  ###
PVs={
    '1': 'U125ID2R:',
    '2': 'U49ID3R:',  #U49/2  ID3R
    '3': 'U41IT3R:',
    '4': 'U49ID4R:',  #U49/1  ID4R
    '5': 'UE49IT4R:', #UE49  IT4R
    '6': 'UE52ID5R:',
    '7': 'UE46IT5R:',
    '8': 'U139ID6R:',
    '9': 'UE56ID6R:',  #UE56/1
    '10': 'U17IT6R:',
    '11': 'UE48IT6R:',
    '12': 'UE112ID7R:',
    '13': 'UE56ID8R:'}  #UE56/2

Homepos={'1': 100,'2':100,'3':100,'4':100,'5':100,'6':100,'7':100,'8':100,
         '9':100,'10':20,'11':100,'12':100,'13':100}

maxgap=[190, 187, 175, 190, 190,160, 190, 180, 180, 25, 185, 185, 190]
mingap=[15.8, 15.8, 15.8, 15.64, 16, 16, 15.6, 16.65, 16.7, 6, 16, 24, 21]
Apple={'5','6','7','9','11','12','13'} 
Planer={'1','2','3','4','8','10'}
#only for Apple:
maxshift=[24.5, 26, 23.15, 28, 24, 56,  28]
minshift=[-24.5, -26, -23.15, -28, -24, -56,  -28]

### Create PVs ##

def GAPV(IDNO,ti0):
#A function to read the gap values at timestam ti0 and now:       
    Gapv=PVs[IDNO]+ "CIOC:rdbk0"        
    print (IDs[IDNO])
    GapValue=ReadPV(Gapv,ti0)
    GapValuenow=ReadPvNow(Gapv)
    print ('Gap Value now :', GapValuenow,' ; at timestamp:', GapValue)
    return GapValue
  
##### Function to read ID PV from Archiver using josn ######

def ReadPV(PV0,ti0):
    
    time=ti0
#collect the query parameters, from is the same as to
    query_params = {
        "from": time,
        "to": time,
        "pv": PV0,

    }

##### build the request url:
##For outside of the control room use this URL: 
    url = urlparse.urlunparse(
        (
            "https",
            "www.helmholtz-berlin.de",
            "/archiver/retrieval/data/getData.json",
            "",
            urlparse.urlencode(query_params),
            "",
        )
    )
    
## From control room use this URL:     
#    url = urlparse.urlunparse(
#       (
#            "http",
#            "archiver.bessy.de",
#            "/retrieval/data/getData.json",
#            "",
#            urlparse.urlencode(query_params),
#            "",
#        )
#    )

# make the request
    response = requests.get(url)

    data = json.loads(response.content.decode("utf-8"))

   # print("Value is:",  data[0]["data"][0]["val"])

    data00=data[0]["data"][0]["val"]
    
    #print(f"ٰ Value of {PV0} is, {data00} ")
    
    #print( " Value of", PV0, "at ti0 is", data00 )
    
#[{'meta': {'name': 'UE52ID5R:CIOC:rdbk0', 'EGU': 'mm', 'PREC': '2'}, 'data': [{'secs': 1665766387, 'val': 29.5241172215949, 'nanos': 893679211, 'severity': 0, 'status': 0}]}] .
    return (data00)
    
## Read the PVs in the current time:----------------------

def ReadPvNow(PVn0):
    PVn=epics.PV(PVn0)
    PVnValue=PVn.get()   #value for Pv NOw:PVn
    return(PVnValue)

####### Function to Drive the ID Gap ###########################

def GapDrive(GapValue, IDNO):
    
#Destination is the Gapvalue(from the archiver)
    
#Critical Gap    
    IDn=IDs[IDNO]
    if IDn == 'UE112':
        critgap = 30
    elif IDn == 'U17':
        critgap = 9
    else: 
        critgap = 22
    print(" Critical gap is", critgap )   
    
## Create PVS for stop, speed, destination, execute and status :

    stopkey= epics.PV(PVs[IDNO]+ "BaseCmnUsrStop")
    speedva= epics.PV(PVs[IDNO]+ "DiagPhyVelSet")
    
    destina= epics.PV(PVs[IDNO]+ "BaseParGapsel.B")
    
    execute= epics.PV(PVs[IDNO]+ "BaseCmdCalc.PROC")
    istatus= epics.PV(PVs[IDNO]+ "BaseCmdMcmd")

#Release the brakes, if they are engaged  
    brk=stopkey.get()    # Stopped =1, Not stopped = 0 = brakes not enganged
    if brk==1:
       brk.put(0)

#set the status of the ID
    istatus.put(5)   #start =5 

#set the velocity:

    if GapValue>critgap+0.1 and GapValue>critgap+0.1:
       velocity=200    #mm/s
    else:
       velocity=20       #0.05        #mm/s
    speedva.put(velocity)

#Set the destination

    destina.put(GapValue)
    time.sleep(0.1) #Sleep for command

# Execute the Gap drive ...

    execute.put(1)

#Sleep until destination is reached

#    rstm=5    # "Rest" time for after the gap is arrived 
        
#    tisp=(  abs (gprdbk-dest)/velocity ) + rstm
    
#    print("time sleep = ", tisp)
# time.sleep(tisp)


## Check if any ID is runnig:###############
def runcheck():
    allrun=epics.PV('SUM:CIOC:stat2')
    IDstatus=allrun.get()
    while IDstatus==1:
        print('Some IDs are running')
        time.sleep(5)
        IDstatus=allrun.get()
    else:
        print('No ID is running, Gap drive is ready, Horizontal (shift) drive can be started')

######### Function to read and Drive the ID Horizontal axis ###########################
#To drive shift we need to choose the destination and the drive mode: PArallel or Antiparallel; 0-5:
 #if the Undulator is already in the desired mode
#If the undulator is not in the desired mode, the shift axes are first set to zero, and then the mode changed.
    
def SHIFTV(IDNO,ti0):
    #PVs
    print (IDs[IDNO] ,':') 
    Shiftv=PVs[IDNO]+"CIOC:rdbk2"   
    aShiftv=PVs[IDNO]+"CIOC:rdbk3" 
    Hdmode=PVs[IDNO]+ "SBaseCmdDriveMode"
    
    #These readbak PVs are not saved in the Archiver, but are/should the same with aboves
    #Shiftv=PVs[IDNO]+ 'SBaseIPmGap.E'  #readback of parallel shift:
    #aShiftv=PVs[IDNO]+ 'SBaseIPmGap.F'  #readback of aparallel shift:
    
    # Archiver---------------ti0 -----------------------
    
    #Parallel Shift
    Shiftvalue=ReadPV(Shiftv,ti0)
    
    #Anti parallel Shift
    if IDNO =='9':
        aShiftvalue=0
    else:
        aShiftvalue=ReadPV(aShiftv,ti0)
    
    #Drive Mode
    shiftModeti0=ReadPV(Hdmode,ti0)  #Horizontal Drive Mode
    
    #shiftmax0=abs(max(Shiftvalue,aShiftvalue))
    shifts=[Shiftvalue,aShiftvalue]
    shiftsab=np.array([abs(Shiftvalue),abs(aShiftvalue)])
    arrmax=np.argmax(shiftsab)
    shiftmax0=shifts[arrmax]
            
    # NOW-----------------------------------------------
       
    #Shift Value enow:
    Shiftvaluenow = ReadPvNow(Shiftv)
        
    #aShif value now:
    if IDNO =='9':
        aShiftvaluenow=0
    else:
        aShiftvaluenow=ReadPvNow(aShiftv)
    
    #Shiftmodenow:
    Shiftmodenow = ReadPvNow(Hdmode)
           
    print ('Shift Value now : ' , Shiftvaluenow,   ' ; at timestamp: ', Shiftvalue)
    print ('aShift Value now: ' , aShiftvaluenow,  '; at timestamp: ', aShiftvalue)
    print ('SHift mode  now : ' , Shiftmodenow,  '  ; at timestamp:  ', shiftModeti0)
    
    shiftmax=abs(max(Shiftvaluenow,aShiftvaluenow))  
    print('shift max', shiftmax)
    
    # Shift drive if the mode is different
    if Shiftmodenow== shiftModeti0:
        print('ID already in mode ' , shiftModeti0)
    else:
            shiftmax=abs(max(Shiftvaluenow,aShiftvaluenow))
            if shiftmax>0.0029999999999954525:
                print('shift axes resetting to 0 before mode change')
                ShiftDrive(0,IDNO)
                while shiftmax>0.0029999999999954525:
                    time.sleep(1)
                    Shifvaluenow=ReadPvNow(PV0s)
                    aShiftvaluenow=ReadPvNow(PV0a)
                    shiftmax=abs(max((Shiftvaluenow,aShiftvaluenow)))
            ShiftDrivemod.put(shiftModeti0)
            print('Mode changed to mode ' , shiftModeti0)
    return(shiftmax0)                       

def ShiftDrive(Shiftvalue,IDNO):
    
    Hstopkey= epics.PV(PVs[IDNO]+ "BaseCmnUsrStop")      
    Hdestina= epics.PV(PVs[IDNO]+ "SBaseParGapsel.B")    
    Hdrivmod= epics.PV(PVs[IDNO]+ "SBaseCmdDriveMode")   
    Hexecute= epics.PV(PVs[IDNO]+ "SBaseCmdCalc.PROC")  
    Histatus= epics.PV(PVs[IDNO]+ "SBaseCmdMcmd")       
    
#Release the brakes, if they are engaged  
# The same with the gap brakes...
    brk=Hstopkey.get()    # Stopped =1, Not stopped = 0 = brakes not enganged
    if brk==1:
        Hstopkey.put(0)

#set the status of the ID
    Histatus.put(5)   #start =5 , Putting Shift axis of ID in Start Mode

#Set the Horizontal drive destination

    Hdestina.put(Shiftvalue)
    time.sleep(0.1) #Sleep for command

# Execute the Shift drive ...

    Hexecute.put(1)
        
####### Call Parameters #########...............................
#def callparam:
 #   a=7

#### Return + Home + Unlock + Lock-Stop : ####

def returnhome(IDNO):
    #Change the Return position to home position:
    returnpos= epics.PV(PVs[IDNO]+ "BaseHomeRPos.A")     #single IDs:
    returnpos.put(Homepos[IDNO])
    
def unlockall():    
    PVunlock= epics.PV("SUM:CIOC:cmd")             # All IDs together
    PVunlock.put(0)                                # unlock all IDs
def returnall():    
    PVunlock.put(0)    
    
#     PVIDcontrol = epics.PV(PVs[IDNO] + 'BaseCmdLswitch')
#     PVservice =  epics.PV(PVs[IDNO]+'BaseCmdSMode')
    
#     #Remove from service mode
#     PVservice.put(1)  
#     #Lock+stop (2) then Home(2)
#     PVunlock.put(2)
#     PVunlock.put(4)
#     #Make remote control control
#     PVIDcontrol.put(0)
    