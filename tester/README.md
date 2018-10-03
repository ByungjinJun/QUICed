#Proxy Instructions

##Server
### Setup (only do once per test server)
1. Sign up for AWS or Google Cloud Platform to start a server in the cloud. If AWS spin up an EC2 instance and if Google Cloud Platform, spin up a Compute Engine instance. I reccomending using an **Ubuntu 16.04** image for the instance because we have been using it successfully (all previous tests on my  home server, AWS servers, and GCP server have all been on Ubuntu 16.04).
2. Modify the network security group for the instance so that it can be accessed by the test client. I've just allowed all IPs for all ports but you could probably get away with just allowing the NU IP address over TCP/UDP ports. 
2. SSH into server (for EC2 instances the command looks something like `$ ssh -i ~/Downloads/dsce.pem ubuntu@ec2-34-200-255-99.compute-1.amazonaws.com` where the parameter for the `-i` flag is the location of the key for the EC2 security group and the address after `ubuntu` is the public domain of the EC2 instance listed on the AWS console)
3. Install go ([installation tutorial for Ubuntu 16.04](https://medium.com/@patdhlk/how-to-install-go-1-9-1-on-ubuntu-16-04-ee64c073cd79)). If you follow the default installation instructions (you should) you'll also need to add `export GOROOT=$GOPATH` after `export PATH=$PATH:/usr/local/go/bin` in the `.profile` file.
4. Pull the [proxy server code](https://github.com/feelmyears/quic-proxy): `$
go get -u github.com/feelmyears/quic-proxy/qpserver`
5. Go to proxy server directory: `cd ~/go/src/github.com/feelmyears/quic-proxy/`
6. Build the proxy server binary: `cd qpserver; go build; go install; cd ..;`
7. Modify the contents of `server.sh` to contain new path of `qpserver` binary: `echo 'sudo ~/go/bin/qpserver -cert cert/leaf_cert.pem -key cert/leaf_cert.key' > server.sh`
8. Test quic proxy server: `./server.sh`. The output should look like:

```
ubuntu@ip-172-31-13-114:~/go/src/github.com/feelmyears/quic-proxy$ ./server.sh
2018-06-19 21:08:14 INFO goroutine:1/1 main.go main.main:31 ▶ Log level==verbose: false

2018-06-19 21:08:14 INFO goroutine:1/3 main.go main.main:51 ▶ quic		start serving :443

2018-06-19 21:08:14 INFO goroutine:1/4 main.go main.main:73 ▶ tcp		 start serving :80

```
You can kill the server at any time by typing `Control+C` 

### Running
Once setup has been completed, the server can be run at any time by navigating to the `quic-proxy` directory and running the `server.sh` script. I reccomend that you run it inside of a tmux window in order to avoid the server process stopping when the terminal times out:

- `tmux`
-  `cd ~/go/src/github.com/feelmyears/quic-proxy/`
-  `./server.sh` (or `bash server.sh`)

To detach from the tmux window, type `Control-B, D`. To re-attach to a tmux window, type `tmux attach -t 0`. (This assumes that the previously created tmux window is named `0`.)

Note that if the instance is not a free tier, you will be charged for **all of the time** that the server is up, and not just when you are running the go program for the quic proxy server. I reccomend that you turn off the instance when you're not using it for tests.

##Client
###Setup
1. Install go (using method of choice for your given platform)
2. Pull the [proxy client code](https://github.com/feelmyears/quic-proxy): `$
go get -u github.com/feelmyears/quic-proxy/qpclient`
3. Modify the address in the `quic.sh` file to be the public IP address of the proxy server. EC2 addresses typically look like `ec2-34-205-28-242.compute-1.amazonaws.com` while GCE address look like `104.154.149.5`. Whatever the public address is (lets call it `0.0.0.0`), the protocol should always be `http` and the port `443`, so you should always have something like `http:\\0.0.0.0:443`. (The entire command would be `go run qpclient/main.go -v -k -proxy http://0.0.0.0:443 -l 127.0.0.1:18443`).
4. **Optional:** If you are also testing one of the TCP proxy configurations, you can perform similar changes to the `tcp.sh` file but make sure that `https` and port `80` are used instead. 

###Running
To run, simply navigate to the `github.com/feelmyears/quic-proxy` directory and start the `quic.sh` script (`./quic.sh` or `bash quic.sh`). 

## Sanity Test
To make sure that everything is working properly once the client-side and server-side proxies have been started, use the [SwitchyOmega plugin](https://chrome.google.com/webstore/detail/proxy-switchyomega/padekgcemlokbadohgkifijomclgjgif?hl=en) for Chrome to route traffic through the local client QUIC proxy. You should be able to access any webpage via it.

##Testing
### Network Emulation Setup
If you are not running tests with network emulation, you can skip this section. Otherwise, first you need to configure the router with the proper emulation settings. To connect via WiFi, the router's network is hidden so you need to manually type in the SSID `OpenWrt` and password `password`. Alternatively, you can connect to the router directly via Ethernet. 

Once connected to the router, ssh into the router `ssh root@192.168.1.1` and type `password` when prompted for a password. Once in, navigate to the configurations directory `cd /etc/config` and modify the configuration files to your desired settings. To start an emulation, make sure that no other emulation configurations exist by executing the `stop_simulate.sh` script and then execute your desired configuration script.


### Testbed Configuration
Pull the [dsce\_ifc\_tester](https://github.com/feelmyears/dsce_ifc_tester) repo onto the local testbed machine. Once the repo has been pulled, you need to install the `chrome-har-capture` node package by running `npm install` inside the main directory of the repo (instructions to call Node [here](https://nodejs.org/en/download/)). **Do not try to do this with any network emulation beacuse it will be very slow!**

Create a list of websites to test and put it in a text file (let's call it `my_list.txt`). Update the `collector_config.ini` file (or whatever configuration file you will be using) so that the `sites` key the value `my_list.txt` (`sites = my_list.txt`). You can also modify other values (explained below) as you see fit:

- `sites`: Path to list of URLs that will be used for testing. Note that the websites are tested in order.
- `chrome`: Path to Chrome
- `repeat`: Number of times to run each test configuration on each URL in `sites`. Repeat has nothing to do with whether or not a test fails. It just is how many times each test is run.
- `max_attempts`: Number of times to re-attempt a failed test. In other words, if a test fails (due to numerous reasons like timeout, connection failure, invalid HAR file, etc.), how many times to try that test again. `max_attempts` should always be at least 1 (because each test should be attempted at least once). Increasing `max_attempts` increases the potential runtime, but if all tests work perfectly on the first try, then a `max_attempts` of 1 will be the same as a `max_attempts` of 10.
- `timeout`: Number of seconds to wait before manually terminating a test (and potentially re-trying it if `max_attempts` is greater than 1).

All `router_*` keys and values are currently irrelevant and can be ignored. (They will only be used if the test collection system is modified to be able to SSH into the router and change the network emulation settings in between tests.)



### Test Running
To run a test, simply navigate the the `dsce_ifc_tester` directory, make sure that the configuration is correct and start the tests with the command: `$ sudo python3 collectoy.py -i collector_config.ini`, where the parameter to the `-i` flag is the path to the configuration file of your choice.

 *Note: the test collection system will store all results in a folder with the same name as the file passed via the `sites` key in the configuration file so it is reccomended that you delete any folder with the same name before running (you will have to use `sudo rm -rf old_folder`)*
 
 **Warning: the test collection currently works by storing the HAR result files for a site in a subfolder named after the hostname of the site. This is problematic when there are two different websites on the test list that share the same hostname (e.g. `https://www.ebay.de` and `https://www.ebay.co.uk`). To avoid overwriting and mixing up test results, the system will simply skip tests sites with previously tested hostnames record the URLs in a `skipped.csv` file. There are generally very few URLs with common hostnames but the collection system should be updated to correctly handle multiple URLs with the same hostname.**
 
### Results Analysis
Once results have been collected, the `plotter.ipynb` Jupyter notebook file can be used to generate ECDF plots for the performance differences between configurations. The analysis assumes that the only two configurations are `BYPASS_PROXY` and `QUIC_PROXY`, so if you want to test another, you'll need to modify the file. Just change the value of the `results_path` variable in the first cell to the path of the folder with the newly generated test results. Then run all cells to produce the plots. You might have the run the last cell twice to get the plots to display. You also might have to update some of the text in the last cell so that the plot titles reflect the testing configuration that you used. *I will try to create a Python script that generates the same ECDFs by just passing in the results folder name as a parameter. But for more advanced analysis, I recommend messing around with the data in a Jupyter Notebook.*

##Todos
- Python script with contents of `plotter.ipynb` for faster generation of ECDF graphs
- Change organization of result files from hostname to URL to enable testing of multiple URLs with the same hostname





