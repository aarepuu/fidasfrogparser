# FidasFrogParser
File parser for Fidas® Frog dust monitor

## About

**FidasFrogParser** is a file parsing code snippet for [Fidas® Frog](https://www.palas.de/en/product/fidasfrog) fine dust monitor.

### Requirements

- [Python Pandas](https://pandas.pydata.org/pandas-docs/stable/install.html)

#### to install requirements

``` sh
$ pip install -r requirements.txt
```

### Usage

Use FidasFrogParser from the command line:

``` sh
$ python fidas-parser.py -i <inputpath> [-m <mergeheader>] [-g <gpsfile>] [-o <outputpath>]'
```

- **-i** input path to a file or directory
- **-m** column name for timestamp header in GPS merge file (optional)
- **-g** the actual GPS file (optional)
- **-o** output path (optional)

## Authors
**FidasFrogParser** has been originally developed by:

* Aare Puussaar <a.puussaar2@newcastle.ac.uk>

## TODOs and Ideas

- Write test
	- input checks
	- GPS merging
	- time conversions
- Add more input arguments
	- human readable switch for output files
	- custom output header
- Add comment extraction function
- Add formatting arguments
- ~~Add Fidas Frog v2 support~~
- ~~Add bulk processing~~

## Contributing

Feel free to fork, download, modify and reuse this parser.

## License

FidasFrogParser is provided under the [MIT](https://github.com/aarepuu/fidasparser/blob/master/LICENSE):

	Copyright (c), 2017 Open Lab Newcastle University, UK. Aare Puussaar
