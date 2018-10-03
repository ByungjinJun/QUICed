#!/usr/bin/python

import json
from haralyzer import HarParser, HarPage
import argparse
import os 
from pathlib import Path
import csv

def har_filename_parser(path):
	filename = os.path.basename(path).split('.')[0]
	run, website, protocol = filename.split('_')
	return run, website, protocol

parser = argparse.ArgumentParser(description='Extract TTFB and PLT from a bulk collection of HAR files')
parser.add_argument('directory', help='Directory of HAR files')
parser.add_argument('-o', '--output', help='Output path of extracted information. Defaults to the input directory path.', required=False)
args = parser.parse_args()

pathlist = Path(args.directory).glob('**/*.har')
har_paths = [str(p) for p in pathlist]

output_path = args.output if args.output is not None else args.directory

with open(os.path.join(output_path, 'bulk_extract_output.csv'), 'w') as csvfile:
	writer = csv.writer(csvfile)
	writer.writerow(['Website', 'Protocol', 'Run', 'TTFB', 'PLT'])
	for hp in har_paths:
		run, website, protocol = har_filename_parser(hp)
		with open(hp, 'r') as f:
			try:
				har_page = HarPage('page_1', har_data=json.loads(f.read()))
				writer.writerow([har_page.url, protocol.upper(), run, har_page.time_to_first_byte, har_page.page_load_time])
			except:
				print(f'Failed to parse HAR file from {hp}')

# with open('har_files/3.har', 'r') as f:
#     har_page = HarPage('page_1', har_data=json.loads(f.read()))

# print('url', har_page.url)
# print('ttfb', har_page.time_to_first_byte)
# print('plt', har_page.page_load_time)
# # bp()
# # {u'name': u'Firefox', u'version': u'25.0.1'}
