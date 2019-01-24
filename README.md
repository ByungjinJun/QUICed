# QUIC/TCP Tunnel (proxy) in Golang

A http/https tunnel using [QUIC](https://www.chromium.org/quic) as transport layer, written in Golang.

This creates **a QUIC/TCP tunnel** between your client proxy and your server proxy to connect the target server. 

## (Prerequisite) Install Golang

[Install Golang](https://golang.org/dl/) first to your **client and server**.

**Note**: requires go version >= 1.9

## Server

### Install `qpserver` on your remote server

Optionally, you can create your server instance in AWS. See below.

`go get -u github.com/ByungjinJun/quic-proxy/qpserver`

### Create certificates for your server if it doesn't have:

Go to quic-proxy/qpserver/cert/keygen and create certificates using the sh file. This sh uses [OpenSSL](https://www.openssl.org).

**Note** When you create certificates, country name has to be 2 characters in leaf.cnf

Locate certificates (leaf_cert.key, leaf_cert.pem) created into cert directory and register root certificate (2048-sha256-root.pem) to your *CLIENT* if your OS is MacOS.

### Start `qpserver`:

Go to quic-proxy/qpserver directory and edit run_server.sh as you want:

`go run server.go -cert YOUR_CERT_FILE_PATH -key YOUR_KEY_FILE_PATH -qaddr YOUR_SERVER'S_QUIC_IP&PORT -taddr YOUR_SERVER'S_TCP_IP&PORT`

**Note**: Don't forget to open the port on your system (varied by OS).

**Note**: If you want to see QUIC packets in **Wireshark**, you have to use 443 as the port for QUIC (10/4/2018). When you do this, to run go with sudo -to bind with 443-, you may want to [check this](https://github.com/hypriot/golang-armbuilds/issues/6#issuecomment-244233589).

Then start the server by running run_server.sh

You can kill the server at any time by typing `Control+C` 

## Client

### Install `qpclient` on your local machine

`go get -u github.com/ByungjinJun/quic-proxy/qpclient`

### Start `qpclient`:

Go to quic-proxy/qpclient directory and edit quic.sh/tcp.sh as you want:

`go run client.go -proxy YOUR_REMOTE_SERVER_IP:443 -l :18443 (-tcp)`

Note that set only port number (with :) for local listening address.

### Set proxy for your application on your local machine

- Let's take Chrome with [SwitchyOmega plugin](https://chrome.google.com/webstore/detail/proxy-switchyomega/padekgcemlokbadohgkifijomclgjgif?hl=en) for example:

![](https://ws1.sinaimg.cn/large/44cd29dagy1fpn5c4jng6j21eq0fw40j.jpg)

- For the test, [see this](https://github.com/ByungjinJun/quic-proxy/tree/master/tester) instead.


## (optional) Cloud server Setup (only do once per test server)
1. Sign up for AWS or Google Cloud Platform to start a server in the cloud. If AWS spin up an EC2 instance and if Google Cloud Platform, spin up a Compute Engine instance. **Ubuntu 16.04** works with this gracefully.
2. Do IP and port configuration modifying the network security group for the instance so that it can be accessed by the test client. 
3. SSH into server (for EC2 instances the command looks something like `$ ssh -i YOUR_CERT_PATH ubuntu@ec2-34-200-255-99.compute-1.amazonaws.com` where the parameter for the `-i` flag is the location of the key for the EC2 security group and the address after `ubuntu` is the public domain of the EC2 instance listed on the AWS console)
4. See the following instructions.

**Running**
Once setup has been completed, the server can be run at any time by navigating to the `quic-proxy` directory and running the `server.sh` script. Use tmux in order to avoid the server process stopping when the terminal times out:

- `tmux`
-  `cd YOUR_PATH_TO_QUIC_PROXY`
-  `./run_server.sh` (or `bash run_server.sh`)

To detach from the tmux window, type `Control-b, d`. To re-attach to a tmux window, type `tmux attach -t 0`. (This assumes that the previously created tmux window is named `0`.)

Note that if the instance is not a free tier, you will be charged for **all of the time** that the server is up, and not just when you are running the go program for the quic proxy server. I reccomend that you turn off the instance when you're not using it for tests.


## TODO

* Clear server cache for every connection (for testing purpose)
* QUIC proxy slows down after 100~150 connections (congestion problem?) 
* HTTP2 support
* Automated client-side setup (e.g., root CA)
* Server selection on cloud based on client's location (DA2GC, MSS)
