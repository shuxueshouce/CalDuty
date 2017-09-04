# DutyData:
# All the data processing work for the project.

import numpy as np
import os

##
# DutydFhsDecode: Decode fhs data
# dRaw: fhs data with coding form
# (return): fhs data with decoding form
def DutyDataFhsDecode(dRaw):
    lenRaw = len(dRaw)
    for i in range(lenRaw):
        dRaw[i] = dRaw[i] - 2048
    return dRaw
##
# DutyAccerationDecode: Decode acceleration data
# dRaw: acceleration data with coding form
# (return): acceleration data with decoding form
def DutyDataAccelerationDecode(dRaw):
    lenRaw = len(dRaw)
    for i in range(lenRaw):
        dRaw[i] = dRaw[i] - 18432
    return dRaw
    
##
# DutyGetData: Obtain fhs(Fetal heart signal) and acceleration signal from the file of fnFhs, as well as fhr(Fetal heart rate) from fnFhr
# input:
#   fnFhs: filename of fetal heart signal
#   fnFhr: filename of fetal heart rate
# output:
#   dFhr: array of fhr
#   dFhs: array of fhs signal, fs = 500Hz, 1 channel
#   dAcc: array of acceleration signal, fs = 25Hz, 3 channels
#   infoDec, including:
#     fhsLost: number of lost fhs packages
#     accLost: number of lost acceleration packages
#     fhsIncomplete: number of incomplete fhs packages
#     accIncomplete: number of incomplete acceleration packages
def DutyDataDecode(fnFhs, fnFhr):
    # Check files
    fExistFhs = os.path.exists(fnFhs)
    fExistFhr = os.path.exists(fnFhr)
    if(not (fExistFhs and fExistFhr)):
        return (np.array([], dtype=np.short), np.array([], dtype=np.short), np.array([], dtype=np.short), np.array([[], [], []], dtype=np.short))
    # Load files
    dFhr = np.loadtxt(fnFhr, dtype=np.short)
    dRaw = np.loadtxt(fnFhs, dtype=np.short)    
    lenFhr = dFhr.size
    lenRaw = dRaw.size
    # Allocate memory for output arrays  
    fsAcc = 75
    fsFhs = 500
    lenFhs = lenFhr*fsFhs
    lenAcc = lenFhr*fsAcc
    dFhs = np.zeros(lenFhs, dtype=np.short)
    dAcc = np.zeros(lenAcc, dtype=np.short)
    infoDec = np.zeros(4, dtype=np.short)
    fhsLost = 0     # counter for lost fhs packages
    accLost = 0     # counter for lost acceleration packages
    fhsIncomplete = 0   # counter for incomplete fhs packages
    accIncomplete = 0   # counter for incomplete acceleration packages    
    # The first package is a fhs package or an acceleration package, which is almost impossible to be complete.
    # So, the first complete fhs package should be identified before decoding. 
    pStart = 0    # the starting position for decoding 
    if dRaw[0] < 10000:  #
        tmpInd = 1
        while (tmpInd < lenRaw) and (dRaw[tmpInd] < 10000):
            tmpInd += 1
        #tmpInd -= 1
        if tmpInd >= 500:
            while tmpInd >= 500:
                tmpInd -= 500
            pStart = tmpInd
        else:
            pStart = tmpInd + 75
    else:
        tmpInd = 1
        while (tmpInd < lenRaw) and (dRaw[tmpInd] > 10000):
            tmpInd += 1
        pStart = tmpInd
    # pStart has been set to point the first complete fhs package.
    t = -1           # counter based on fhr data
    curStart = pStart    # the first index of the current access data
    curEnd = 0      # the last index of the current access data
    cntFhs = 0      # counter for fhs packages
    cntAcc = 0      # counter for acceration packages    
    # Check data before the first complete fhs package  
    if pStart > 0:        
        for tmpInd in range(pStart):
            if dRaw[tmpInd] < 10000:
                t += 1
                fhsIncomplete += 1
                cntFhs += 1
                break;
    # Decoding starts
    while curStart <= lenRaw:
        # fhs data
        if dRaw[curStart] < 10000: 
            # Update indices for dFhs
            t += 1
            if t >= lenFhr:
                break       # Duration of fhs is longer than that of fhr
            indFhs0 = t * fsFhs
            indFhs1 = indFhs0 + fsFhs            
            # Fhs decoding and update indices                       
            curEnd = curStart+fsFhs
            if curEnd >= lenRaw:    # EXCEPTION: not a complete package
                break
            cntFhs += 1
            tmpRaw = np.array(dRaw[curStart:curEnd]);
            ind = 0
            while ind < fsFhs:
                if(tmpRaw[ind] > 10000):
                    break
                ind += 1
            if ind != fsFhs:
                fhsIncomplete += 1
                curEnd = curStart+ind
                tmpRaw.setfield(2048, dtype=np.short)   #2048----decode----->0 
            tmpFhs = DutyDataFhsDecode(tmpRaw)
            curStart = curEnd
            # Copy decoding result to dFhs
            dFhs[indFhs0:indFhs1] = tmpRaw           
        # acceleration data
        else: 
            # Update indices for dFhs
            indAcc0 = t * fsAcc
            indAcc1 = indAcc0 + fsAcc
            # Acc decoding and update indices
            curEnd = curStart+fsAcc
            if curEnd >= lenRaw:    # EXCEPTION: not a complete package
                break
            cntAcc += 1
            accLost += cntFhs - cntAcc
            tmpRaw = np.array(dRaw[curStart:curEnd])
            ind = 0
            while ind < fsAcc:
                if(tmpRaw[ind] < 10000):
                    break
                ind += 1            
            if ind != fsAcc:
                accIncomplete += 1
                curEnd = curStart+ind
                tmpRaw.setfield(18432, dtype=np.short)  #18432----decode----->0           
            tmpAcc = DutyDataAccelerationDecode(tmpRaw)
            cntAcc = cntFhs
            curStart = curEnd
            # Copy decoding result to dAcc
            dAcc[indAcc0:indAcc1] = tmpAcc
    # Decoding Loop ends        
    # Update stat info  
    accLost += cntFhs - cntAcc     # duration of fhs data and that of acceleration data should be the same 
    nLost = lenFhr - cntFhs
    if nLost > 0:
        fhsLost = nLost
        accLost += nLost
    infoDec[0] = fhsLost
    infoDec[1] = accLost
    infoDec[2] = fhsIncomplete
    infoDec[3] = accIncomplete
    print(dAcc.size)
    return (dFhr, dFhs, dAcc, infoDec)

##
# DutyDataCorr: Autocorrelation of fhs signal
# dFhs: fhs signal, fs = 500Hz, 1 channel
# dAcc: autocorrelation result
#def DutyDataCorr(dFhs):
    #lenFhs = len(dFhs)
    #fsFhs = 500
    #duration = lenFhs/fsFhs
    #for t in range(duration):
    
    #return