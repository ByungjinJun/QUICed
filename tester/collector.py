from enum import Enum
import itertools
import random
import subprocess
from subprocess import call
from urllib.parse import urlparse
import os
import argparse
import configparser
from time import sleep
import csv
from time import time as get_time
import datetime

def time_to_str(time):
    return datetime.datetime.fromtimestamp(int(time)).strftime('%m-%d %H:%M:%S')

# class ProxyConfig(Enum):
# 	BYPASS_PROXY_HTTPS 	= 0		# Client 				->  (bypass)ProxyClient -> ***  HTTPS  ***  ->  (bypass)ProxyServer -> WebServer
# 	BYPASS_PROXY_QUIC 	= 1		# Client(QUIC Request) 	->  (bypass)ProxyClient -> ***  QUIC   ***  ->  (bypass)ProxyServer -> WebServer
# 	HTTP_PROXY_HTTPS 	= 2		# Client 				->          ProxyClient -> ***  HTTPS  ***  ->          ProxyServer -> WebServer
# 	QUIC_PROXY_QUIC 	= 3		# Client(QUIC Request) 	->  		ProxyClient -> ***  QUIC   ***  ->          ProxyServer -> WebServer
# 	HTTP_PROXY_QUIC 	= 4		# Client 				->          ProxyClient -> ***  QUIC   ***  ->          ProxyServer -> WebServer



class ProxyConfig(Enum):
	BYPASS_PROXY 		= 0		# Client 				->  (bypass)ProxyClient -> ***  QUIC  ***  ->  (bypass)ProxyServer -> WebServer
	QUIC_PROXY 	 		= 1 	# Client 				->          ProxyClient -> ***  QUIC  ***  ->          ProxyServer -> WebServer
	HTTP_PROXY_HTTPS 	= 2 	# Client 				->          ProxyClient -> ***  HTTPS  ***  ->          ProxyServer -> WebServer




class ServiceConfig(Enum):
	# NORMAL 	= 0		# No service degredation
	DA2GC 	= 1		# Direct Air to Ground Connection
	# MSS 	= 2		# Mobile Satellite Service

class TestConfig:
	# PROXY_PORTS = {
	# 	ProxyConfig.BYPASS_PROXY_HTTPS 	: 80,
	# 	ProxyConfig.BYPASS_PROXY_QUIC	: 443,
	# 	ProxyConfig.HTTP_PROXY_HTTPS 	: 18080,
	# 	ProxyConfig.QUIC_PROXY_QUIC 	: 18443,
	# 	ProxyConfig.HTTP_PROXY_QUIC 	: 18443,
	# }

	PROXY_PORTS = {
		# ProxyConfig.BYPASS_PROXY 	    : 80,
		ProxyConfig.QUIC_PROXY			: 18443,
		# ProxyConfig.HTTP_PROXY_HTTPS 	: 18000,
	}

	# PROXY_PORTS = {
	# 	ProxyConfig.BYPASS_PROXY_HTTPS 	: 80,
	# 	ProxyConfig.BYPASS_PROXY_QUIC	: 443,
	# 	ProxyConfig.HTTP_PROXY_HTTPS 	: 18000,
	# 	ProxyConfig.QUIC_PROXY_QUIC 	: 18443,
	# 	ProxyConfig.HTTP_PROXY_QUIC 	: 18443,
	# }



	def __init__(self, proxy_config, service_config):
		self.proxy_config = proxy_config
		self.service_config = service_config

	def configure_router(self, router):
		# SSH into router
		# Reset service degradation  settings
		# Set service degration to desired settings
		# if self.service_config == ServiceConfig.NORMAL:
			# pass
		# elif self.service_config == ServiceConfig.DA2GC:
			# pass
		# elif self.service_config == ServiceConfig.MSS:
			# pass
		# else:
			# raise Exception('Unrecognized router configuration provided!')

		pass


	def configure_chrome(self, chrome_path, remote_debugging_port):

		cmd = f'{chrome_path} --user-data-dir=/tmp/chrome --headless --crash-dumps-dir=/tmp --remote-debugging-port=9222'
		proxy_port = self.PROXY_PORTS[self.proxy_config]

		if   self.proxy_config == ProxyConfig.BYPASS_PROXY:
			pass
		elif self.proxy_config == ProxyConfig.QUIC_PROXY:
			cmd += f' --enable-quic --proxy-server="localhost:18443"'
		elif self.proxy_config == ProxyConfig.HTTP_PROXY_HTTPS:
			cmd += f' --proxy-server="localhost:18000"'

		print(cmd)
		p  = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
		return p

class Router:
	def __init__(self, address, user, password):
		self.address = address
		self.user = user
		self.password = password

class TestRunner:
	def __init__(self, websites, chrome_path, remote_debugging_port, output, repeat, timeout, max_attempts):#, router):
		"""
			websites 		list of websites to test
			chrome_path		path to installation of chrome
			debugging_port	remote debugging port for chrome
			output			path of output directory where results are saved
			repeat			number of times to repeat each test
			timeout			timeout for each test
			max_attempts	maximum number of times to try after a timeout
			router 			Router class for service emulation
		"""

		self.websites = websites
		self.chrome_path = chrome_path
		self.output = output
		self.repeat = repeat
		self.max_attempts = max(1, max_attempts)
		# self.router = router
		self.remote_debugging_port = remote_debugging_port
		self.timeout = timeout
		self.failure_path = os.path.join(self.output, 'failures.csv')
		self.success_path = os.path.join(self.output, 'successes.csv')
		self.skipped_path = os.path.join(self.output, 'skipped.csv')
		ensure_exists(self.failure_path)
		ensure_exists(self.success_path)

	def run_tests(self):
		hostnames = set()
		configs = [pc for pc in TestConfig.PROXY_PORTS]#ProxyConfig]
		headers = ['Website', 'Timestamp']
		for c in configs:
			for i in range(1, self.repeat + 1):
				headers.append(f'{c.name}_{i} Result')
				headers.append(f'{c.name}_{i} Start Time')
				headers.append(f'{c.name}_{i} Failure Time')

		with open(self.failure_path, 'w') as f:
			writer = csv.writer(f)
			writer.writerow(headers)

		with open(self.success_path, 'w') as f:
			writer = csv.writer(f)
			writer.writerow(['Website', 'Start Time'])

		# run_time = get_time()

		for i, website in enumerate(self.websites):
			# if (get_time() - run_time) > 60*60:
			# 	sleep(60*1)
			# 	run_time = get_time()

			hostname_parts = urlparse(website).hostname.split('.')
			hostname = None
			if len(hostname_parts) > 2:
				hostname = hostname_parts[1]
			else:
				hostname = hostname_parts[0]

			if hostname in hostnames:
				with open(self.skipped_path, 'a') as f:
					f.write(f'{website}\n')
				continue

			hostnames.add(hostname)

			results = {}
			success = True
			start_time = time_to_str(get_time())

			for test_config in self.randomize_configs():
				config_results = []
				for run_index in range(repeat):
					r, t_start, t_duration = self.run(website, hostname, test_config, run_index)
					t_start = time_to_str(t_start)
					config_results.append((r, t_start, t_duration))

				success = success and all([cr[0] for cr in config_results])
				results[test_config.proxy_config] =  config_results

			if success:
				self.record_success(hostname, start_time)
			else:
				self.record_failure(configs, hostname, start_time, results)

	def run_

	def record_success(self, site, time):
		with open(self.success_path, 'a') as f:
			writer = csv.writer(f)
			writer.writerow([site, time])

	def record_failure(self, proxy_configs, site, time, results):
		with open(self.failure_path, 'a') as f:
			writer = csv.writer(f)
			row = [site, time]
			for pc in proxy_configs:
				config_results = results[pc]
				for c in config_results:
					row.extend(c)

			writer.writerow(row)

	def run(self, site, hostname, test_config, run_index):
		service = test_config.service_config.name
		proxy = test_config.proxy_config.name
		output_path = self.get_run_output_path(hostname, service, proxy, run_index)

		for attempt in range(self.max_attempts):
			# test_config.configure_router(self.router)
			call("sudo killall -HUP mDNSResponder".split())
			call("sudo killall mDNSResponderHelper".split())
			call("sudo dscacheutil -flushcache".split())

			chrome = test_config.configure_chrome(self.chrome_path, self.remote_debugging_port)
			sleep(1)

			success = False
			t_start = get_time()
			har_capturer = self.capture_har(site, output_path)

			try:
				har_capturer.wait()
				success = True
			except:
				print(f'Failed attempt #{attempt} for test <{service}, {proxy}, {run_index}>')

			t_duration = get_time() - t_start

			# To make sure everything has been killed before start another test
			har_capturer.kill()
			sleep(1)
			call(["killall", "-9", "Google Chrome"])
			sleep(1)

			if os.path.exists(output_path) and os.path.getsize(output_path) <= 5000:
				success = False
				os.remove(output_path)

			if success is not True:
				continue
			else:
				return True, t_start, t_duration

		return False, t_start, t_duration

	def capture_har(self, site, output_path):
		cmd = f'~/node_modules/chrome-har-capturer/bin/cli.js -r 3 -u 300000 -e 1000 -o {output_path} {site} '
		p  = subprocess.Popen(cmd, shell=True)
		return p

	def get_run_output_path(self, hostname, service, proxy, run_index):
		ensure_exists(os.path.join(self.output, hostname) + '/')
		return os.path.join(self.output, hostname, f'{service}-{proxy}-{run_index}.har')

	def randomize_configs(self):
		configs = [TestConfig(pc, sc) for (pc, sc) in itertools.product(TestConfig.PROXY_PORTS, ServiceConfig)]
		random.shuffle(configs)
		return configs

	def record_test_failure(self, site, test_config, run_index):
		with open(os.path.join(self.failure_path), 'a') as f:
			writer = csv.writer(f)
			writer.writerow([site, test_config.service_config.name, test_config.proxy_config.name, run_index, self.max_attempts])

def ensure_exists(file_path):
	print('ensuring exists', file_path)
	directory = os.path.dirname(file_path)
	print(directory)
	if not os.path.exists(directory):
		print('directory dne')
		os.makedirs(directory)


def read_sites(path):
	with open(path, 'r') as f:
		return [url.strip() for url in f.readlines()]

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument('--config', '-c', help="Configuration file", required=True)
	parser.add_argument('--mode', '-m', help="Configuration section in config file", default='DEFAULT')
	args = parser.parse_args()

	config = configparser.ConfigParser()
	config.read(args.config)

	default_config = config[args.mode]
	output_dir = default_config['sites'].split('.')[0]
	ensure_exists(output_dir  + '/.')

	router_addr = str(default_config['router_addr'])
	router_user = str(default_config['router_user'])
	router_password = str(default_config['router_password'])
	router = Router(router_addr, router_user, router_password)

	urls = read_sites(default_config['sites'])
	chrome = default_config['chrome']
	print(chrome)
	repeat = int(default_config['repeat'])
	max_attempts = int(default_config['max_attempts'])
	timeout = int(default_config['timeout'])

	remote_debugging_port = 9222
	tr = TestRunner(urls, chrome, remote_debugging_port, output_dir, repeat, timeout, max_attempts)
	tr.run_tests()
