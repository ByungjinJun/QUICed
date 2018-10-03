import json
from haralyzer import HarParser, HarPage
import argparse
import os 
from pathlib import Path
import csv
import numpy as np
import matplotlib.pyplot as plt
from configs import ProxyConfig, ServiceConfig

class ConfigMeasurement:
	def __init__(self, hostname, proxy_config, ttfb_avg, ttfb_std, plt_avg, plt_std):
		self.hostname = hostname
		self.proxy_config = proxy_config
		self.ttfb_avg = ttfb_avg
		self.ttfb_std = ttfb_std
		self.plt_avg = plt_avg
		self.plt_std = plt_std

	def __str__(self):
		return f'{self.hostname}/{self.proxy_config}: TTFB ({self.ttfb_avg:.2f}, {self.ttfb_std:.2f}), PLT ({self.plt_avg:.2f}, {self.plt_std:.2f})'

	def __repr__(self):
		return self.__str__()

class Measurements:
	def __init__(self):
		self.sites = {}

	def add(self, hostname, proxy_config, ttfb, plt):
		self.sites.setdefault(hostname, []).append([proxy_config, ttfb, plt])

	def reduce(self, limit=-1):
		sites = {}
		for hostname, data in self.sites.items():
			r = {}
			for proxy_config, ttfb, plt in data:
				r.setdefault(proxy_config, []).append((ttfb, plt))

			for proxy_config, datapoints in r.items():
				ttfb = np.asarray([d[0] for d in datapoints])
				plt = np.asarray([d[1] for d in datapoints])

				if limit > -1:
					if limit < len(ttfb):
						ttfb = ttfb[:limit]
						plt = plt[:limit]
					else:
						print(f'Cannot limit number of measurements for {hostname}/{proxy_config} to {limit} because only {len(ttfb)} exist')

				cf = ConfigMeasurement(hostname, proxy_config, np.mean(ttfb), np.std(ttfb), np.mean(plt), np.std(plt))
				sites.setdefault(hostname, {}).setdefault(proxy_config, cf)

		return sites

class HARCollector:
	def __init__(self):
		pass

	def collect_measurements(self, paths):
		measurements = Measurements()
		for p in paths:
			hostname, service_config, proxy_config, run_index = self.parse_path(p)
			ttfb, plt = self.parse_har_file(p)
			if ttfb and plt:
				measurements.add(hostname, proxy_config, ttfb, plt)

		return measurements

	def parse_path(self, path):
		f_path, f_name = os.path.split(path)
		hostname = os.path.split(f_path)[-1]
		service_config, proxy_config, run_index = f_name[:-4].split('-')
		return hostname, service_config, proxy_config, run_index

	def parse_har_file(self, path):
		with open(path, 'r') as f:
			try:
				har_page = HarPage('page_1', har_data=json.loads(f.read()))
				return har_page.time_to_first_byte, har_page.page_load_time
			except:
				print(f'Failed to parse HAR file from {path}')

		return None, None

def write_measurements(path, measurements):
	with open(path, 'w') as f:
		writer = csv.writer(f)
		writer.writerow(['Hostname', 'Proxy Configuration', 'TTFB (avg)', 'TTFB (stddev)', 'PLT (avg)', 'PLT (stddev'])
		for hostname, config_measurements in measurements.items():
			for cf in config_measurements:
				writer.writerow([hostname, cf.proxy_config, cf.ttfb_avg, cf.ttfb_std, cf.plt_avg, cf.plt_std])

class Plotter:
	def __init__(self, measurements, output_dir, dpi=300):
		self.measurements = measurements
		self.hostnames = list(measurements.keys())
		self.output_dir = output_dir
		self.dpi = dpi

	def plot_ttfb(self, name):
		proxy_configs = [c.name for c in ProxyConfig]

		combined_ttfb_avg = {}
		combined_ttfb_std = {}

		for h in self.hostnames:
			site_measurements = self.measurements[h]
			for pc in proxy_configs:
				if pc in site_measurements:
					combined_ttfb_avg.setdefault(pc, []).append(site_measurements[pc].ttfb_avg)
					combined_ttfb_std.setdefault(pc, []).append(site_measurements[pc].ttfb_std)
				else:
					combined_ttfb_avg.setdefault(pc, []).append(0)
					combined_ttfb_std.setdefault(pc, []).append(0)

			
		ttfb_avg = []
		ttfb_std = []

		for pc in proxy_configs:
			ttfb_avg.append(combined_ttfb_avg[pc])
			ttfb_std.append(combined_ttfb_std[pc])

		num_sites = len(self.hostnames)
		index = np.arange(num_sites)
		bar_width = 0.15
		opacity = 0.75

		fig, ax = plt.subplots()

		colors = ['r', 'g', 'b', 'orange', 'pink']
		for i, pc in enumerate(proxy_configs):
			r = ax.bar(index + bar_width*i, ttfb_avg[i], bar_width, color=colors[i], label=pc, alpha=opacity, align='edge')
		ax.set_title('TTFB')
		ax.set_ylabel('TTFB (ms)')
		ax.set_xticks(index + bar_width/5)
		ax.set_xticklabels(self.hostnames)
		ax.legend()
		
		ax.autoscale(tight=True)
		plt.xticks(rotation=45)
		plt.tight_layout()
		fig.savefig(os.path.join(self.output_dir, name), dpi = self.dpi)
		# plt.show()


	def plot_plt(self, name):
		proxy_configs = [c.name for c in ProxyConfig]

		combined_plt_avg = {}
		combined_plt_std = {}

		for h in self.hostnames:
			site_measurements = self.measurements[h]
			for pc in proxy_configs:
				if pc in site_measurements:
					combined_plt_avg.setdefault(pc, []).append(site_measurements[pc].plt_avg)
					combined_plt_std.setdefault(pc, []).append(site_measurements[pc].plt_std)
				else:
					combined_plt_avg.setdefault(pc, []).append(0)
					combined_plt_std.setdefault(pc, []).append(0)

			
		plt_avg = []
		plt_std = []

		for pc in proxy_configs:
			plt_avg.append(combined_plt_avg[pc])
			plt_std.append(combined_plt_std[pc])

		num_sites = len(self.hostnames)
		index = np.arange(num_sites)
		bar_width = 0.15
		opacity = 0.75

		fig, ax = plt.subplots()

		colors = ['r', 'g', 'b', 'orange', 'pink']
		for i, pc in enumerate(proxy_configs):
			r = ax.bar(index + bar_width*i, plt_avg[i], bar_width, color=colors[i], label=pc, alpha=opacity, align='edge')
		ax.set_title('PLT')
		ax.set_ylabel('PLT (ms)')
		ax.set_xticks(index + bar_width/5)
		ax.set_xticklabels(self.hostnames)
		ax.legend()
		
		ax.autoscale(tight=True)
		plt.xticks(rotation=45)
		plt.tight_layout()
		fig.savefig(os.path.join(self.output_dir, name), dpi = self.dpi)


if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='Extract TTFB and PLT from a bulk collection of HAR files')
	parser.add_argument('directory', help='Directory of HAR files')
	args = parser.parse_args()

	pathlist = Path(args.directory).glob('**/*/*.har')
	har_paths = [str(p) for p in pathlist]
	hc = HARCollector()
	measurements = hc.collect_measurements(har_paths)
	limit = 3
	for i in range(1,limit):
		print(i)
		combined = measurements.reduce(limit=i)

		# write_measurements(os.path.join(args.directory, 'measurements.csv'), combined)

		p = Plotter(combined, args.directory)
		p.plot_ttfb(f'ttfb_{i}.png')
		p.plot_plt(f'plt_{i}.png')

	