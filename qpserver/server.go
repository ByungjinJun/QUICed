package main

import (
	"log"
	"net/http"
	"flag"
	"sync"
	"crypto/tls"

	"github.com/lucas-clemente/quic-go"
	"github.com/elazarl/goproxy"
	"github.com/feelmyears/quic-proxy/common"
)

func main() {
	// Process server args
	var (
		// listenAddr string
		cert		string
		key			string
		verbose		bool
		quicPort	int
		tcpAddr		string
	)
	// flag.StringVar(&listenAddr, "l", ":443", "listen addr (udp port only)")
	flag.StringVar(&cert, "cert", "", "cert path")
	flag.StringVar(&key, "key", "", "key path")
	flag.BoolVar(&verbose, "v", false, "verbose")
	flag.IntVar(&quicAddr, "qport", 6121, "quic port")
	flag.StringVar(&tcpAddr, "taddr", "165.124.183.118:10000", "tcp address and port")
	flag.Parse()

	// Set waitgroup for the main go routines
	var wg sync.WaitGroup
	wg.Add(2)


	// SERVE QUIC

	// Check certificate
	if cert == "" || key == "" {
		log.Fatal("cert and key can't by empty")
		return
	}

	// Create QUIC listener
	listener, err := quic.ListenAddr(quicAddr, generateTLSConfig(cert, key), nil)
	if err != nil {
		log.Fatal("listen failed:%v", err)
		return
	}
	ql := common.NewQuicListener(listener)

	// Initialize the proxy
	quicProxy := goproxy.NewProxyHttpServer()
	quicProxy.Verbose = verbose

	// Run QUIC proxy
	server := &http.Server{Addr: quicPort, Handler: quicProxy}
	log.Println("serving QUIC proxy at", quicPort)
	go func() {
		log.Fatal(server.Serve(ql))
		defer wg.Done()
	}()


	// SERVE TCP

	// Initialize the proxy
	tcpProxy := goproxy.NewProxyHttpServer()
	tcpProxy.Verbose = verbose

	// Run TCP proxy
	log.Println("serving TCP proxy at", tcpAddr)
	go func() {
		log.Fatal(http.ListenAndServe(tcpAddr, tcpProxy))
		defer wg.Done()
	}()

	wg.Wait()
}

func generateTLSConfig(certFile, keyFile string) *tls.Config {
	tlsCert, err := tls.LoadX509KeyPair(certFile, keyFile)
	if err != nil {
		panic(err)
	}
	return &tls.Config{Certificates: []tls.Certificate{tlsCert}}
}

