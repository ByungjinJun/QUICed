#!/usr/bin/python

import os
import argparse
import subprocess
from time import sleep
from urllib.parse import urlparse
from pdb import set_trace as bp

def read_sites(path):
	with open(path, 'r') as f:
		return [url.strip() for url in f.readlines()]

def start_chrome(chrome_path, proxy_port, remote_debugging_port, enable_quic=True):
#	cmd = f'/Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --user-data-dir=/tmp/chrome  --proxy-server="localhost:8080"  --enable-quic --remote-debugging-port={remote_debugging_port} --headless  --proxy-server="quic://rodrigo918.hopto.org:443"'
	# cmd = f'/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --user-data-dir=/tmp/chrome --enable-quic --proxy-server="127.0.0.1:18443" www.google.com'
	quic_flag = ""
	if enable_quic:
		quic_flag = '--enable-quic'

	cmd = f'{chrome_path} --user-data-dir=/tmp/chrome  --headless {enable_quic} --proxy-server="localhost:{proxy_port}" --remote-debugging-port={remote_debugging_port}'
	p  = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
#	p.communicate()
	return p

def capture_har(har_path, site):
	cmd = f'node node_modules/chrome-har-capturer/bin/cli.js -o {har_path} {site}'
	p  = subprocess.Popen(cmd, shell=True)
	return p

def ensure_dir(file_path):
	directory = os.path.dirname(file_path)
	if not os.path.exists(directory):
		os.makedirs(directory)

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument('--sites', '-s', help="Path to txt file of sites", type=str)
	parser.add_argument('--chrome', '-c', help="Path to Chrome installation", type=str)
	parser.add_argument('--output', '-o', help="Dir to save har files", type=str)
	parser.add_argument('--repeat', '-r', help="Dir to save har files", type=int, default=5)
	args = parser.parse_args()s

	# output_dir = args.output
	output_dir = "output/"
	ensure_dir(output_dir)

	test_urls = read_sites(args.sites)
	test_protocols = [('quic', 18443), ('tcp', 18080)]
	# test_protocols = [('tcp', 18080)]
	for i, url in enumerate(test_urls):
		for r in range(1, args.repeat+1):
			for protocol, port in test_protocols:
				hostname_parts = urlparse(url).hostname.split('.')
				hostname = None
				if len(hostname_parts) > 2:
					hostname = hostname_parts[1]
				else:
					hostname = hostname_parts[0]

				p_browser = start_chrome(args.chrome, port, 9222)
				sleep(3)
				print(f"Capturing HAR for {hostname} using protocol {protocol}")
				p_har = capture_har(os.path.join(output_dir, f'{r}_{hostname}_{protocol}.har'), url)
				p_har.wait()

				p_browser.kill()
				sleep(5)
