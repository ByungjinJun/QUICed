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
	tcpAddr := flag.String("taddr", "10.95.137.54:8080", "tcp address")
	tcp := flag.Bool("tcp", false, "use TCP instead QUIC")
	flag.Parse()

	//TODO: auto implementation of rootCA into the client?
	// Check certificates and create TLS config
	if *cert == "" || *key == "" {
		log.Fatal("[ERROR] cert and key can't by empty")
		return
	}
	tlsCfg:= generateTLSConfig(*cert, *key)

	var listener common.Listener
	var err error
	var handler *common.HttpHandler
	if *tcp {	// Listen on TCP
		listener, err = common.DefaultListener(*tcpAddr)
		if err != nil {
			log.Println(err)
		}

		handler = &common.HttpHandler{
			Addr: *tcpAddr,
			TLSConfig: tlsCfg,
		}

		log.Println("listening to TCP on", *tcpAddr)
	} else {	// Listen on QUIC
		config := &common.QuicConfig{
			KeepAlive:   true,
			TLSConfig:   tlsCfg,
		}

		listener, err = common.QUICListener(*quicAddr, config)
		if err != nil {
			log.Println(err)
		}

		handler = &common.HttpHandler{
			Addr: *quicAddr,
			TLSConfig: tlsCfg,
		}

		log.Println("listening to QUIC on", *quicAddr)
	}

	server := &common.Server{Listener: listener}
	go server.Serve(handler)

	select {}
}

func generateTLSConfig(certFile, keyFile string) *tls.Config {
	tlsCert, err := tls.LoadX509KeyPair(certFile, keyFile)
	if err != nil {
		panic(err)
	}

	return &tls.Config{Certificates: []tls.Certificate{tlsCert}}
}
