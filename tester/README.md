# Test quic-proxy

## Sanity Test
To make sure that everything is working properly once the client-side and server-side proxies have been started, test with SwitchOmega for Chrome to route traffic through the local client QUIC proxy.

You should be able to access any webpage via it.

## Testing
### Network Emulation Setup
If you are not running tests with network emulation, you can skip this section.

First you need to configure the router with the proper emulation settings.

Connect to the router via wired network. Alternatively, you can connect via Wifi. To connect via WiFi, the router's network is hidden so you need to manually type in the SSID `OpenWrt` and password `password`. 

Once connected to the router, ssh into the router `ssh root@192.168.1.1` and type `password` when prompted for a password. Once in, navigate to the configurations directory `cd /etc/config` and modify the configuration files to your desired settings. To start an emulation, make sure that no other emulation configurations exist by executing the `stop_simulate.sh` script and then execute your desired configuration script.

We use netem for the emulated network. Values for emulation (latency, loss and jitter) are from Scale-up research.

### Testbed Configuration
**Do not try to do below with any network emulation because it will be very slow!**

We use Google Chrome and `chrome-har-capture` for creating HAR files from test. 

Install the `chrome-har-capture` node package by running `npm install` inside the main directory of the repo (instructions to call Node [here](https://nodejs.org/en/download/)). 

Create a list of websites to test and put it in a text file (let's call it `my_list.txt`). Update the `collector_config.ini` file (or whatever configuration file you will be using) so that the `sites` key the value `my_list.txt` (`sites = my_list.txt`). You can also modify other values (explained below) as you see fit:

- `sites`: Path to list of URLs that will be used for testing. Note that the websites are tested in order.
- `chrome`: Path to Chrome
- `repeat`: Number of times to run each test configuration on each URL in `sites`. Repeat has nothing to do with whether or not a test fails. It just is how many times each test is run.
- `max_attempts`: Number of times to re-attempt a failed test. In other words, if a test fails (due to numerous reasons like timeout, connection failure, invalid HAR file, etc.), how many times to try that test again. `max_attempts` should always be at least 1 (because each test should be attempted at least once). Increasing `max_attempts` increases the potential runtime, but if all tests work perfectly on the first try, then a `max_attempts` of 1 will be the same as a `max_attempts` of 10.
- `timeout`: Number of seconds to wait before manually terminating a test (and potentially re-trying it if `max_attempts` is greater than 1).

All `router_*` keys and values are currently irrelevant and can be ignored. (They will only be used if the test collection system is modified to be able to SSH into the router and change the network emulation settings in between tests.)


### Run the test
To run a test, simply navigate the the `dsce_ifc_tester` directory, make sure that the configuration is correct and start the tests with the command: `$ sudo python3 collectoy.py -i collector_config.ini`, where the parameter to the `-i` flag is the path to the configuration file of your choice.

 *Note: the test collection system will store all results in a folder with the same name as the file passed via the `sites` key in the configuration file so it is reccomended that you delete any folder with the same name before running (you will have to use `sudo rm -rf old_folder`)*
 
 **Warning: the test collection currently works by storing the HAR result files for a site in a subfolder named after the hostname of the site. This is problematic when there are two different websites on the test list that share the same hostname (e.g. `https://www.ebay.de` and `https://www.ebay.co.uk`). To avoid overwriting and mixing up test results, the system will simply skip tests sites with previously tested hostnames record the URLs in a `skipped.csv` file. There are generally very few URLs with common hostnames but the collection system should be updated to correctly handle multiple URLs with the same hostname.**
 
### Results Analysis
Once results have been collected, the `plotter.ipynb` Jupyter notebook file can be used to generate ECDF plots for the performance differences between configurations. The analysis assumes that the only two configurations are `BYPASS_PROXY` and `QUIC_PROXY`, so if you want to test another, you'll need to modify the file. Just change the value of the `results_path` variable in the first cell to the path of the folder with the newly generated test results. Then run all cells to produce the plots. You might have the run the last cell twice to get the plots to display. You also might have to update some of the text in the last cell so that the plot titles reflect the testing configuration that you used. *I will try to create a Python script that generates the same ECDFs by just passing in the results folder name as a parameter. But for more advanced analysis, I recommend messing around with the data in a Jupyter Notebook.*

## Todos
- Python script with contents of `plotter.ipynb` for faster generation of ECDF graphs
- Change organization of result files from hostname to URL to enable testing of multiple URLs with the same hostname
