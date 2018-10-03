package main

import (
	"log"
	"flag"
	"net/http"
	"net/url"
	"time"
	"sync"

	"github.com/elazarl/goproxy"
	"github.com/feelmyears/quic-proxy/common"
)

func main() {
	// Process client args
	var (
		listenAddr	string
		proxyUrl	string
		skipCertVerify	bool
		verbose		bool
		tcp		bool
	)
	flag.StringVar(&listenAddr, "l", ":18080", "listenAddr")
	flag.StringVar(&proxyUrl, "proxy", "", "upstream proxy url")
	flag.BoolVar(&skipCertVerify, "k", false, "skip Cert Verify")
	flag.BoolVar(&verbose, "v", false, "verbose")
	flag.BoolVar(&tcp, "tcp", false, "Use TCP (instead of default QUIC)")
	flag.Parse()

	// Validate the URL
	serverProxy, err := url.Parse(proxyUrl)
	if err != nil {
			log.Println("[Proxy client error]: %v", err)
			return
	}
	//log.Println(proxyUrl)

	// Set waitgroup for the main goroutine
	var wg sync.WaitGroup
	wg.Add(1)

	// Initialize the client proxy server
	clientProxy := goproxy.NewProxyHttpServer()
    clientProxy.Verbose = verbose

	// Set args in http transport
    clientProxy.Tr.Proxy = func(req *http.Request) (*url.URL, error) {
		return clientProxy, nil
	}
    clientProxy.Tr.MaxIdleConns = 90
    clientProxy.Tr.IdleConnTimeout = 30 * time.Second

	if !tcp {	// QUIC
		//if Url.Scheme == "https" {
		//	log.Error("quic-clientproxy only support http clientproxy")
		//	return
		//}

		// Set Quic Dialer
		dialer := common.NewQuicDialer(skipCertVerify)
		clientProxy.Tr.Dial = dialer.Dial

		// Run the client proxy
		clientProxy.ConnectDial = clientProxy.NewConnectDialToProxy(proxyUrl)
		log.Println("serving QUIC proxy at", listenAddr)
		go func() {
			log.Fatal(http.ListenAndServe(listenAddr, clientProxy))
			defer wg.Done()
		}()
	} else {	// TCP
		// Run the client proxy
		clientProxy.ConnectDial = clientProxy.NewConnectDialToProxy(proxyUrl)
		log.Println("serving TCP proxy at", listenAddr)
		go func() {
			http.ListenAndServe(listenAddr, clientProxy)
			defer wg.Done()
		}()

	}
	wg.Wait()
}

