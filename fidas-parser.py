#!/usr/bin/env python

# -*- coding: utf-8 -*-
"""Fidas Frog dataparser.

Code for cleaning up fidas frog files of medatata and converting them to plain csv files
and merging with GPS files

Example:
        $ python fidas-parser.py -i <inputpath> [-m <mergeheader>] [-g <gpsfile>] [-o <outputpath>]'


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
__version__ = "0.6.1"
__status__ = "Development"


import sys, getopt, datetime, os, glob
import pandas as pd
from datetime import datetime, timedelta


def addGPS(readings,gps,gheader,tformat="%Y-%m-%d %H:%M:%S"):
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

def processFile(filepath,gpsfile,gpsheader,outputpath):
    """Function for processing the sensor file

        TODO - needs testing

    Args:
        filepath: filepath to the sensor file
        gpsfile: filepath to the GPS file
        gpsheader: header column of GPS data file to index by
        outputpath: filepath to of the output directory

    """
    print('Working on ' + filepath)
    start,loc,deviceid = getStarts(filepath)
    data = pd.read_csv(filepath, skiprows=loc, error_bad_lines=False, index_col=False, sep='\t', header=0, encoding='ISO-8859-1')
    data = convertTime(data,start)
    #add deviceid
    data["device_id"] = deviceid;
    if gpsheader is not None:
        gps=pd.read_csv(gpsfile,sep=',',header=0)
        data = addGPS(data,gps,gpsheader)
        #data = addGPS(data,gps,"YYYY-MO-DD HH-MI-SS_SSS")
    #clean up column names
    data.columns = data.columns.str.lower().str.replace(":","").str.strip().str.replace(" ", "_")
    #custom header
    header = ["timestamp","pm_1","pm_2.5","pm_4","pm_10","pm_tot.","dcn", "latitude", "longitude"]
    if outputpath is None:
        outputpath = os.path.basename(filepath) + '_id-' + deviceid + '.csv'
    else:
        outputpath = outputpath + '/' + os.path.basename(filepath) + '_id-' + deviceid + '.csv'
    data.to_csv(outputpath, index=False, columns = header, encoding='utf-8',date_format='%Y-%m-%d %H:%M:%S')
    print("Successfully written", outputpath)

def main(argv):
    inputpath = None
    outputpath = None
    gpsheader = None
    gpsfile = None
    if(len(argv)<1):
        print('usage: fidas-parser.py -i <inputpath> [-m <mergeformat>] [-g <gpsfile>] [-o <outputpath>]')
        sys.exit(2);
    try:
        opts, args = getopt.getopt(argv,"hi:m:g:o:",["ipath=","mform=","gfile=","ofile="])
    except getopt.GetoptError:
        print('usage: fidas-parser.py -i <inputpath> [-m <mergeformat>] [-g <gpsfile>] [-o <outputpath>]')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('python fidas-parser.py -i <inputpath> [-m <mergeformat>] [-g <gpsfile>] [-o <outputpath>]')
            sys.exit()
        elif opt in ("-i", "--ipath"):
            inputpath = arg
        elif opt in ("-o", "--ofpath"):
            outputpath = arg
        elif opt in ("-m","mform="):
            gpsheader= arg
        elif opt in ("-g","gpsfile="):
            gpsfile = arg
    if (os.path.isdir(inputpath)):
        for filename in os.listdir(inputpath):
            if filename.endswith(".txt"):
                filepath = os.path.join(inputpath, filename)
                processFile(filepath,gpsfile,gpsheader,outputpath)
                continue
        #Merge files
        if outputpath is None:
            allFiles = glob.glob("*.csv")
        else:
            allFiles = glob.glob(outputpath + "/*.csv")
        frame = pd.DataFrame()
        list_ = []
        for file_ in allFiles:
            df = pd.read_csv(file_,index_col=None, header=0)
            list_.append(df)
            frame = pd.concat(list_)
        if outputpath is None:
            frame.to_csv('combined.csv',index=False)
        else:
            frame.to_csv(outputpath +'/combined.csv',index=False)
    elif (os.path.isfile(inputpath)):
        processFile(inputpath,gpsfile,gpsheader,outputpath)
    else:
        print("Please provide correct path to a file or folder containing readings.")
        print('usage: fidas-parser.py -i <inputpath> [-m <mergeformat>] [-g <gpsfile>] [-o <outputpath>]')
if __name__ == "__main__":
   main(sys.argv[1:])
