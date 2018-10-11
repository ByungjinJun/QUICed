package main

import (
	"log"
	"flag"

	"github.com/ByungjinJun/quic-proxy/common"
)

func main() {
	// Process tunnel args
	listenAddr := flag.String("l", ":18443", "listenAddr")
	proxyUrl := flag.String("proxy", "", "upstream proxy url")
	tcp := flag.Bool("tcp", false, "Use TCP (instead of default QUIC)")
	flag.Parse()

	//TODO: URL validator
	if *proxyUrl == "" {
		log.Fatal("[ERROR] proxy url cannot be empty")
		return
	}

	var dialer common.Dialer
	if *tcp {	// TCP tunnel
		dialer = common.DefaultDialer()

		log.Println("serving TCP on", *listenAddr)
	} else {	// QUIC tunnel
		config := &common.QuicConfig{
			KeepAlive: true,
		}

		dialer = common.QUICDialer(config)

		log.Println("serving QUIC on", *listenAddr)
	}

	tunnel := &common.Tunneler{
		Dialer:           dialer,
		ProxyAddr:        *proxyUrl,
	}

	Run(tunnel, *listenAddr)

	select {}
}

// Run listens and handles local connections through *Tunneler*.
// *laddr is the address to listen
func Run(tunnel *common.Tunneler, laddr string) {
	listener, err := common.DefaultListener(laddr)
	if err != nil {
		log.Println(err)
	}

	handler := &common.HttpHandler{
		Addr: laddr,
		Tunnel: tunnel,
	}

	server := &common.Server{Listener: listener}
	go server.Serve(handler)
}
