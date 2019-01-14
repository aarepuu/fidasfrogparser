#!/usr/bin/env python

# -*- coding: utf-8 -*-
"""Fidas Frog dataparser.

Code for cleaning up fidas frog files of medatata and converting them to plain csv files
and merging with GPS files

Example:
        $ python fidas-parser.py -i <inputfile> [-m <mergeheader>] [-g <gpsfile>] -o <outputfile>'


Todo:
    * Test GPS merging properly 
    * Add more input arguments: human readable switch for outputfile
    * Add comment extraction function
    * Add formating arguments
    * Add custom headers
    * Add fidas frog v2 support


  Copyright (c) 2017, Open Lab Newcastle University, UK. 
  All rights reserved.
  
  Redistribution and use in source and binary forms, with or without 
  modification, are permitted provided that the following conditions are met: 
  1. Redistributions of source code must retain the above copyright notice, 
     this list of conditions and the following disclaimer.
  2. Redistributions in binary form must reproduce the above copyright notice, 
     this list of conditions and the following disclaimer in the documentation 
     and/or other materials provided with the distribution.
 
  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" 
  AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE 
  IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE 
  ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE 
  LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR 
  CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF 
  SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS 
  INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN 
  CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) 
  ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE 
  POSSIBILITY OF SUCH DAMAGE. 

"""


__author__ = "Aare Puussaar"
__copyright__ = "Copyright (c) 2017, Newcastle University, UK."

__license__ = "MIT"
__maintainer__ = "Aare Puussaar"
__email__ = "a.puussaar2@ncl.ac.uk"
__version__ = "0.52"
__status__ = "Development"


import sys, getopt, datetime
import pandas as pd
from datetime import datetime, timedelta


def addGPS(readings,gps,gheader,tformat):
    """Function for getting nearest timestamp gps location

        TODO - needs testing

    Args:
        readings: pandas dataframe object of readings
        gps: pandas dataframe object of gps coordinates
        rheader: header column of readings to index by
        gheader: header column of gps data to index by

    Returns:
        starttime: starttime of readings
        loc: data start location in the file

    """
    
    #if readings are in epoch
    #Timezone issues with the parser
    #readings.timestamp = readings.timestamp.astype("datetime64[s]") - timedelta(hours=1)
    readings.timestamp = readings.timestamp.astype("datetime64[s]")
    gps[gheader] = pd.to_datetime(gps[gheader],format=tformat)
    #remove millis
    gps[gheader] = gps[gheader].values.astype('datetime64[s]')
    #remove dublicates
    gps = gps.drop_duplicates(gheader,keep='last')
    gps_dt = pd.Series(gps[gheader].values, gps[gheader])
    #gps_dt.reindex(readings["timestamp"], method="nearest")
    readings["nearest"] = gps_dt.reindex(readings["timestamp"], method="nearest").values
    merged_df = pd.merge(readings, gps,  how='left', left_on=['nearest'], right_on = [gheader])
    return merged_df

def getStarts(source):
    """Function for getting the startdate and data start location

    Args:
        source: input file.    

    Returns:
        starttime: starttime of readings
        loc: data start location in the file
        deviceid: device id of the sensor
    """
    loc = 0
    with open(source, encoding='ISO-8859-1') as f:
        for line in f:          
            if line.startswith('Start at:'):
                s=line
            if line.startswith('Operator:'):
                deviceid = line
            if line.startswith('timestamp'):
                break
            loc+=1     
    #extract datetime from string
    #starttime = pd.to_datetime(str(s.split(":", 1)[1].strip()).replace("-", "").replace("/", "-"))
    starttime = pd.to_datetime(str(s.split(":", 1)[1].strip()),format="%d/%m/%Y - %H:%M:%S")
    deviceid = str(deviceid.split(":", 1)[1].strip())
    #convert from nanoseconds
    starttime = starttime.value/10**9 
    return starttime, loc, deviceid

def convertTime(data,starttime,human=True):
    """Function for adding start time for readings

    Args:
        data: pandas dataframe object of readings
        starttime: starttime of readings
        human: boolean for converting to human readable time from epoch

    Returns:
        data: converted pandas dataframe object of readings
    """
    data.timestamp = (data.timestamp+starttime).astype(int)
    if(human):
        data.timestamp = data.timestamp.astype("datetime64[s]")
    return data

def privacyZone(data,minutes):
    """Function for cutting off start end of dataset

    Args:
        data: pandas dataframe object of readings
        minutes: minutes to cut off

    Returns:
        data: converted pandas dataframe object of readings
    """
    data2 = data.set_index("timestamp")
    tmin = pd.to_datetime(data2.index.min() + timedelta(minutes=minutes))
    tmax = pd.to_datetime(data2.index.max() - timedelta(minutes=minutes))
    data = data[data.timestamp.apply(lambda x: x > tmin) & data.timestamp.apply(lambda x: x < tmax)]
    return data

def main(argv):
    inputfile = None
    outputfile = None
    gpsheader = None
    gpsfile = None
    if(len(argv)<1):
        print('usage: fidas-parser.py -i <inputfile> [-m <mergeformat>] [-g <gpsfile>] [-o <outputfile>]')
        sys.exit(2);
    try:
        opts, args = getopt.getopt(argv,"hi:m:g:o:",["ifile=","mform=","gfile=","ofile="])
    except getopt.GetoptError:
        print('usage: fidas-parser.py -i <inputfile> [-m <mergeformat>] [-g <gpsfile>] -o <outputfile>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('python fidas-parser.py -i <inputfile> [-m <mergeformat>] [-g <gpsfile>] -o <outputfile>')
            sys.exit()
        elif opt in ("-i", "--ifile"):
            inputfile = arg
        elif opt in ("-o", "--ofile"):
            outputfile = arg
        elif opt in ("-m","mform="):
            gpsheader= arg
        elif opt in ("-gps","gpsfile="):
            gpsfile = arg
    start,loc,deviceid = getStarts(inputfile)
    data = pd.read_csv(inputfile, skiprows=loc, error_bad_lines=False, index_col=False, sep='\t', header=0, encoding='ISO-8859-1')
    data = convertTime(data,start)
    if gpsheader:
        gps=pd.read_csv(gpsfile,sep=',',header=0)
        data = addGPS(data,gps,gpsheader)
        #data = addGPS(data,gps,"YYYY-MO-DD HH-MI-SS_SSS")      
    #clean up column names
    data.columns = data.columns.str.lower().str.replace(":","").str.strip().str.replace(" ", "_")       
    #custom header
    header = ["timestamp","pm_1","pm_2.5","pm_4","pm_10","pm_tot.","dcn", "latitude", "longitude"]
    if outputfile is None:
        outputfile = inputfile
    data.to_csv(outputfile + '_id-' + deviceid + '.csv',index=False, columns = header, encoding='utf-8',date_format='%Y-%m-%d %H:%M:%S')
    print("Successfully written",outputfile)

if __name__ == "__main__":
   main(sys.argv[1:])