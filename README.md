# Quic/TCP Proxy in Golang

A http/https proxy using [QUIC](https://www.chromium.org/quic) as transport layer, written in Golang.

This creates a QUIC channel between the client and the server like below. 

![](https://ws1.sinaimg.cn/large/44cd29dagy1fpn4yaf2p8j20nd079aae.jpg)

For the test purpose, the proxy can switch between QUIC and TCP. 

## Server

### (optional) Cloud server Setup (only do once per test server)
1. Sign up for AWS or Google Cloud Platform to start a server in the cloud. If AWS spin up an EC2 instance and if Google Cloud Platform, spin up a Compute Engine instance. **Ubuntu 16.04** works with this gracefully.
2. Do IP and port configuration modifying the network security group for the instance so that it can be accessed by the test client. 
3. SSH into server (for EC2 instances the command looks something like `$ ssh -i ~/Downloads/dsce.pem ubuntu@ec2-34-200-255-99.compute-1.amazonaws.com` where the parameter for the `-i` flag is the location of the key for the EC2 security group and the address after `ubuntu` is the public domain of the EC2 instance listed on the AWS console)
4. See the following instructions.

**Running**
Once setup has been completed, the server can be run at any time by navigating to the `quic-proxy` directory and running the `server.sh` script. Use tmux in order to avoid the server process stopping when the terminal times out:

- `tmux`
-  `cd ~/go/src/github.com/feelmyears/quic-proxy/`
-  `./server.sh` (or `bash server.sh`)

To detach from the tmux window, type `Control-B, D`. To re-attach to a tmux window, type `tmux attach -t 0`. (This assumes that the previously created tmux window is named `0`.)

Note that if the instance is not a free tier, you will be charged for **all of the time** that the server is up, and not just when you are running the go program for the quic proxy server. I reccomend that you turn off the instance when you're not using it for tests.

### Install Golang

[Install Golang](https://golang.org/dl/) first to your **client and server**.

**Note**: require go version >= 1.9

### Install `qpserver` on your remote server

`go get -u github.com/ByungjinJun/quic-proxy/qpserver`

### Create certificates for your server if it doesn't have:

Go to quic-proxy/qpserver/cert/keygen and create certificates using the sh file. This sh uses [OpenSSL](https://www.openssl.org).

### Start `qpserver`:

Go to quic-proxy/qpserver directory and edit run_server.sh as you want:

`go run server.go -cert YOUR_CERT_FILE_PATH -key YOUR_KEY_FILE_PATH -v -qport YOUR_SERVER'S_QUIC_PORT -taddr YOUR_SERVER'S_ADDRESS_AND_TCP_PORT`

**Note**: Don't forget to open the port.

Then start the server by running run_server.sh.

You can kill the server at any time by typing `Control+C` 

## Client

Install Golang first.

### Install `qpclient` on your local machine

`go get -u github.com/ByungjinJun/quic-proxy/qpclient`

### Start `qpclient`:

Go to quic-proxy/qpclient directory and edit quic.sh/tcp.sh as you want:

`go run client.go -v -k -proxy http://YOUR_REMOTE_SERVER:3443 -l 127.0.0.1:18443`

### Set proxy for your application on your local machine

- Let's take Chrome with [SwitchyOmega plugin](https://chrome.google.com/webstore/detail/proxy-switchyomega/padekgcemlokbadohgkifijomclgjgif?hl=en) for example:

![](https://ws1.sinaimg.cn/large/44cd29dagy1fpn5c4jng6j21eq0fw40j.jpg)

- For the test, [see this](https://github.com/ByungjinJun/quic-proxy/tree/master/tester) instead.


## TODO

* Resolve weird occasional hangs (30s) in QUIC channel
* No explicit server IP
