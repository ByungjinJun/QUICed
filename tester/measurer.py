#!/usr/bin/python

import os
import argparse
from subprocess import Popen, PIPE
from threading import Timer
import shlex
from time import sleep
from urllib.parse import urlparse
from pdb import set_trace as bp
from random import *
import copy


def read_sites(path):
	with open(path, 'r') as f:
		return [url.strip() for url in f.readlines()]


'''

Type can be one of:

1) Client 				->  (bypass)ProxyClient -> ***  HTTPS  ***  ->  (bypass)ProxyServer -> WebServer
2) Client(QUIC Request) ->  (bypass)ProxyClient -> ***  QUIC   ***  ->  (bypass)ProxyServer -> WebServer
3) Client 				->          ProxyClient -> ***  HTTPS  ***  ->          ProxyServer -> WebServer
4) Client(QUIC Request) ->  		ProxyClient -> ***  QUIC   ***  ->          ProxyServer -> WebServer
5) Client 				->          ProxyClient -> ***  QUIC   ***  ->          ProxyServer -> WebServer

'''


def start_chrome(chrome_path, proxy_port, remote_debugging_port, type):

	if   type == 1:
		cmd = f'{chrome_path} --user-data-dir=/tmp/chrome  --headless --remote-debugging-port={remote_debugging_port}'
	elif type == 2:
		cmd = f'{chrome_path} --user-data-dir=/tmp/chrome  --headless --enable-quic --remote-debugging-port={remote_debugging_port}'
	elif type == 3:
		cmd = f'{chrome_path} --user-data-dir=/tmp/chrome  --headless --proxy-server="localhost:{proxy_port}" --remote-debugging-port={remote_debugging_port} --crash-dumps-dir=/tmp'
	elif type == 4:
		cmd = f'{chrome_path} --user-data-dir=/tmp/chrome  --headless --enable-quic --proxy-server="localhost:{proxy_port}" --remote-debugging-port={remote_debugging_port} --crash-dumps-dir=/tmp'
	elif type == 5:
		cmd = f'{chrome_path} --user-data-dir=/tmp/chrome  --headless --proxy-server="localhost:{proxy_port}" --remote-debugging-port={remote_debugging_port}'
#ipc-connection-timeout

	p  = Popen(cmd, shell=True)
	return p


def capture_har(har_path, site):
	cmd = f'node node_modules/chrome-har-capturer/bin/cli.js -o {har_path} {site}'# -u 5000 -g 1000'
	proc = Popen(shlex.split(cmd))

	# timeout for webpage hangs (e.g., with a pop-up freezes screen)
	timer = Timer(80, proc.kill)
	try:
		timer.start()
		proc.communicate()
	finally:
		timer.cancel()

	#p.terminate()
	#return return_code


def ensureDir(file_path):
	directory = os.path.dirname(file_path)
	if not os.path.exists(directory):
		os.makedirs(directory)


if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument('--sites', '-s', help="Path to txt file of sites", type=str)
	parser.add_argument('--chrome', '-c', help="Path to Chrome installation", type=str)
	parser.add_argument('--output', '-o', help="Dir to save har files", type=str)
	parser.add_argument('--repeat', '-r', help="Number of times to repeat the call", type=int, default=5)
	args = parser.parse_args()


	# Hardcoded for now but can be modified to user needs by uncommenting the following line
	# output_dir = args.output
	mainOutputDir = "output/"
	ensureDir(mainOutputDir)

	#randomArray = [1,2,3,4,5]
	# randomArray = [1,2]
	randomArray = [4]

	# ProxyPort selection based on Type. Defined on top.
	proxyPort ={
	1:80,
	2:443,
	3:18080,
	4:18443,
	5:18443
	}


	# # proxyPorts to test when server setup is switched off
	# proxyPort ={
	# 1:80,
	# 2:443,
	# 3:80,
	# 4:443,
	# 5:443
	# }

	urlParser = read_sites(args.sites)
	for i, url in enumerate(urlParser):
		randomize = copy.deepcopy(randomArray)
		for j in randomArray:
			tempType = randomize.pop(randint(0,len(randomize)-1))
			for r in range(1, args.repeat+1):
				p_browser = start_chrome(args.chrome, proxyPort[tempType], 9222, tempType)
				sleep(1)

				hostname_parts = urlparse(url).hostname.split('.')
				hostname = None
				if len(hostname_parts) > 2:
					hostname = hostname_parts[1]
				else:
					hostname = hostname_parts[0]

				outputDir = mainOutputDir + f'{i}_{hostname}/'
				ensureDir(outputDir)
				
				capture_har(os.path.join(outputDir, f'type{tempType}_run{r}_{hostname}.har'), url)
				#print ("CHC returns " + str(p_har))

				p_browser.kill()
				sleep(1)







	# Randomize tester.

	# print(randomArray.pop(randint(0,len(randomArray)-1)))
	# print(randomArray)
	# print(randomArray.pop(randint(0,len(randomArray)-1)))
	# print(randomArray)
	# print(randomArray.pop(randint(0,len(randomArray)-1)))
	# print(randomArray)
	# print(randomArray.pop(randint(0,len(randomArray)-1)))
	# print(randomArray)
	# print(randomArray.pop(randint(0,len(randomArray)-1)))
	# print(randomArray)










#
# # TVP
# if __name__ == "__main__":
#
# 	start_chrome("test",99, 11, 1)
# 	start_chrome("test",99, 11, 2)
# 	start_chrome("test",99, 11, 3)
# 	start_chrome("test",99, 11, 4)
# 	start_chrome("test",99, 11, 5)









# def typeSelecter(type):
# 	switcher = {
#
# 	     1:  f'{chrome_path} --user-data-dir=/tmp/chrome  --headless {enable_quic} --proxy-server="localhost:{proxy_port}" --remote-debugging-port={remote_debugging_port}',
#
#          2:  f'{chrome_path} --user-data-dir=/tmp/chrome  --headless {enable_quic} --proxy-server="localhost:{proxy_port}" --remote-debugging-port={remote_debugging_port}',
#
#          3:  f'{chrome_path} --user-data-dir=/tmp/chrome  --headless {enable_quic} --proxy-server="localhost:{proxy_port}" --remote-debugging-port={remote_debugging_port}',
#
#          4:  f'{chrome_path} --user-data-dir=/tmp/chrome  --headless {enable_quic} --proxy-server="localhost:{proxy_port}" --remote-debugging-port={remote_debugging_port}',
#
#          5:  f'{chrome_path} --user-data-dir=/tmp/chrome  --headless {enable_quic} --proxy-server="localhost:{proxy_port}" --remote-debugging-port={remote_debugging_port}',
# 	}
#
# 	return switcher.get(type, "default")
#
#
#
#
# if __name__ == "__main__":
#
# 	print typeSelecter (0)










# 	p  = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
# #	p.communicate()
# 	return p









'''

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
	args = parser.parse_args()

	# output_dir = args.output
	output_dir = "output/"
	ensure_dir(output_dir)

	test_urls = read_sites(args.sites)
	test_protocols = [('quic', 443)]
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

'''
