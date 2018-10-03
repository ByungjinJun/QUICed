# Quic/TCP Proxy in Golang

A http/https proxy using [QUIC](https://www.chromium.org/quic) as transport layer, written in Golang.

![](https://ws1.sinaimg.cn/large/44cd29dagy1fpn4yaf2p8j20nd079aae.jpg)

For the test purpose, the proxy can switch between QUIC and TCP. 

## Installation & Usage

[Install Golang](https://golang.org/dl/) first to your client and server.

**Note**: require go version >= 1.9

### Install `qpserver` on your remote server

`go get -u github.com/ByungjinJun/quic-proxy/qpserver`

### Start `qpserver`:

`qpserver -v -l :3443 -cert YOUR_CERT_FILA_PATH -key YOUR_KEY_FILE_PATH`

### Install `qpclient` on your local machine

`go get -u github.com/liudanking/quic-proxy/qpclient`

### Start `qpclient`:

`qpclient -v -k -proxy http://YOUR_REMOTE_SERVER:3443 -l 127.0.0.1:18080`

### Set proxy for your application on your local machine

- Let's take Chrome with SwitchyOmega for example:

![](https://ws1.sinaimg.cn/large/44cd29dagy1fpn5c4jng6j21eq0fw40j.jpg)

- For the test, 


## TODO

* Using custom congestion control
* Basic Authentication
