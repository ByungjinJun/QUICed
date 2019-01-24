package main

import (
	"log"
	"flag"
	"crypto/tls"

	"github.com/ByungjinJun/quic-proxy/common"
)

func main() {
	// Process server args
	cert := flag.String("cert", "", "cert path")
	key := flag.String("key", "", "key path")
	quicAddr := flag.String("qaddr", "10.95.137.54:443", "quic address")
	tcpAddr := flag.String("taddr", "10.95.137.54:10000", "tcp address")
	flag.Parse()

	//TODO: auto implementation of rootCA into the client?
	// Check certificates and create TLS config
	if *cert == "" || *key == "" {
		log.Fatal("[ERROR] cert and key can't by empty")
		return
	}
	tlsCfg:= generateTLSConfig(*cert, *key)


	// ----------- SERVE TCP -----------
	tcpListener, err := common.DefaultListener(*tcpAddr)
	if err != nil {
		log.Println(err)
	}

	var tcpHandlerOptions []common.HandlerOption
	tcpHandlerOptions = append(tcpHandlerOptions,
		common.SetHandlerAddr(*tcpAddr),
		common.SetHandlerTLSConfig(tlsCfg),
	)
	tcpHandler := common.HTTPHandler(tcpHandlerOptions...)

	log.Println("listening to TCP on", *tcpAddr)
	ts := &common.Server{Listener: tcpListener}
	go ts.Serve(tcpHandler)

	// ----------- SERVE QUIC -----------
	config := &common.QuicConfig{
		KeepAlive:   false,
		TLSConfig:   tlsCfg,
	}

	quicListener, err := common.QUICListener(*quicAddr, config)
	if err != nil {
		log.Println(err)
	}

	var quicHandlerOptions []common.HandlerOption
	quicHandlerOptions = append(tcpHandlerOptions,
		common.SetHandlerAddr(*quicAddr),
		common.SetHandlerTLSConfig(tlsCfg),
	)
	quicHandler := common.HTTPHandler(quicHandlerOptions...)
	//quicHandler := common.HTTP2Handler(*quicAddr, tlsCfg)

	log.Println("listening to QUIC on", *quicAddr)
	qs := &common.Server{Listener: quicListener}
	go qs.Serve(quicHandler)

	select {}
}

func generateTLSConfig(certFile, keyFile string) *tls.Config {
	tlsCert, err := tls.LoadX509KeyPair(certFile, keyFile)
	if err != nil {
		panic(err)
	}

	return &tls.Config{Certificates: []tls.Certificate{tlsCert}}
}
