package main

import (
	"crypto/tls"
	"net"
	"net/http"

	"github.com/elazarl/goproxy"
	"github.com/lucas-clemente/quic-go"

	"flag"
	"sync"

	log "github.com/liudanking/goutil/logutil"
	"github.com/liudanking/quic-proxy/common"
)

func main() {
	var (
		listenAddr string
		cert       string
		key        string
		verbose    bool
	)
	flag.StringVar(&listenAddr, "l", ":443", "listen addr (udp port only)")
	flag.StringVar(&cert, "cert", "", "cert path")
	flag.StringVar(&key, "key", "", "key path")
	flag.BoolVar(&verbose, "v", false, "verbose")
	flag.Parse()

	log.Info("Log level==verbose: %v", verbose)
	if cert == "" || key == "" {
		log.Error("cert and key can't by empty")
		return
	}

	listener, err := quic.ListenAddr(listenAddr, generateTLSConfig(cert, key), nil)
	if err != nil {
		log.Error("QUIC listen failed:%v", err)
		return
	}


	var wg sync.WaitGroup

	ql := common.NewQuicListener(listener)
	proxy := goproxy.NewProxyHttpServer()
	proxy.Verbose = verbose
	server := &http.Server{Addr: listenAddr, Handler: proxy}
	log.Info("quic\t\tstart serving %v", listenAddr)
	go func() {log.Error("quic\t\tserve error:%v", server.Serve(ql))}()
	

	tcpAddr, err := net.ResolveTCPAddr("tcp", ":80")
	if err != nil {
		log.Error("TCP resolve addr failed:%v", err)
		return
	}

	tcpConn, err := net.ListenTCP("tcp", tcpAddr)
	if err != nil {
		log.Error("TCP listen failed:%v", err)
		return
	}
	
	tlsConn := tls.NewListener(tcpConn, generateTLSConfig(cert, key))

	tcp_proxy := goproxy.NewProxyHttpServer()
	tcp_proxy.Verbose = verbose
	tcp_server := &http.Server{Addr: listenAddr, Handler: tcp_proxy}
	log.Info("tcp\t\t start serving %v", listenAddr)
	go func(){log.Error("tcp\t\tserve error:%v", tcp_server.Serve(tlsConn))}()

	wg.Add(1)
	wg.Wait()
}

func generateTLSConfig(certFile, keyFile string) *tls.Config {
	tlsCert, err := tls.LoadX509KeyPair(certFile, keyFile)
	if err != nil {
		panic(err)
	}
	return &tls.Config{Certificates: []tls.Certificate{tlsCert}}
}
