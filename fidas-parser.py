#!/usr/bin/env python

# -*- coding: utf-8 -*-
"""Fidas Frog dataparser.

Code for cleaning up fidas frog files of medatata and converting them to plain csv files
and merging with GPS files

Example:
        $ python fidas-parser.py -i <inputfile> -o <outputfile>


Todo:
    * Implement GPS merging properly 
    * Add more input arguments: human readable switch for outputfile
    * Add comment extraction function


  Copyright (c) 2017, Newcastle University, UK. 
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
__version__ = "0.3"
__status__ = "Development"

import sys, getopt, datetime
import pandas as pd




def addGPS(readings,gps,rheader,gheader):
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
    #readings = readings.set_index(rheader)
    #gps = gps.set_index(gheader, drop=False)
    #gps.reindex(reading.index, method='nearest')
    
    gps_dt = pd.Series(gps[gheader].values, gps[gheader])
    #gps_dt.reindex(readings[rheader], method="nearest")
    readings["nearest"] = gps_dt.reindex(readings[rheader], method="nearest").values
    merged_df = pd.merge(readings, gps,  how='left', left_on=['nearest'], right_on = [gheader])
    return merged_df

def getStarts(source):
    """Function for getting the startdate and data start location

    Args:
        source: input file.    

    Returns:
        starttime: starttime of readings
        loc: data start location in the file

    """
    loc = 0
    with open(source) as f:
        for line in f:
            if line.startswith('Start at:'):
                s=line
            if line.startswith('timestamp'):
                break
            loc+=1
    #extract datetime from string
    starttime = pd.to_datetime(str(s.split(":", 1)[1].strip()).replace("-", "").replace("/", "-"))
    #convert from nanoseconds
    starttime = starttime.value/10**9 
    return starttime, loc

def convertTime(data,starttime,human=False):
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

def main(argv):
    inputfile = ''
    outputfile = ''
    if(len(argv)<1):
        print 'usage: fidas-parser.py -i <inputfile> -o <outputfile>'
        sys.exit(2);
    try:
        opts, args = getopt.getopt(argv,"hi:o:",["ifile=","ofile="])
    except getopt.GetoptError:
        print 'usage: fidas-parser.py -i <inputfile> -o <outputfile>'
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print 'fidas-parser.py -i <inputfile> -o <outputfile>'
            sys.exit()
        elif opt in ("-i", "--ifile"):
            inputfile = arg
        elif opt in ("-o", "--ofile"):
            outputfile = arg
    start,loc = getStarts(inputfile)
    data = pd.read_csv(inputfile, skiprows=loc, error_bad_lines=False, index_col=False, sep='\t', header=0)
    data = convertTime(data,start,True)
    data.to_csv(outputfile,index=False)
    print "Successfully written",outputfile
    

if __name__ == "__main__":
   main(sys.argv[1:])