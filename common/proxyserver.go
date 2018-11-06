package common

import (
	"net"
	"time"
	"log"
	"crypto/tls"
)

// A proxy server for both server-proxy and client-proxy
type Server struct {
	Listener Listener
}

type Listener interface {
	net.Listener
}

type Handler interface {
	Handle(net.Conn)
}

// HandlerOptions has options for Handler. This is required to add the different number of options to different protocol
type HandlerOptions struct {
	Addr      string
	Tunnel    *Tunneler
	TLSConfig *tls.Config
}

// Handler helper functions
type HandlerOption func(opts *HandlerOptions)
func SetHandlerAddr(addr string) HandlerOption {
	return func(opts *HandlerOptions) {opts.Addr = addr}
}
func SetHandlerTunneler(tr *Tunneler) HandlerOption {
	return func(opts *HandlerOptions) {opts.Tunnel = tr}
}
func SetHandlerTLSConfig(config *tls.Config) HandlerOption {
	return func(opts *HandlerOptions) {opts.TLSConfig = config}
}

func (s *Server) Serve(h Handler) error {
	var l Listener
	if s.Listener == nil {
		var err error
		l, err = DefaultListener("")
		if err != nil {
			return err
		}
	} else {
		l = s.Listener
	}

	// If network error happens, wait *connDelay* and retry
	connDelay := 5 * time.Millisecond
	for {
		conn, err := l.Accept()
		if err != nil {
			if nerr, ok := err.(net.Error); ok && nerr.Temporary() {
				if connDelay >= MaxConnDelay {
					connDelay = MaxConnDelay
				} else {
					connDelay *= 2
				}
				log.Println("[SERVER] Accept error:", err, "retrying in", connDelay)
				time.Sleep(connDelay)
				continue
			}
			return err
		}
		connDelay = 0

		go h.Handle(conn)
	}
}

type tcpListener struct {
	*net.TCPListener
}

// DefaultListener creates a TCPListener for the proxy server
func DefaultListener(addr string) (Listener, error) {
	laddr, err := net.ResolveTCPAddr("tcp", addr)
	if err != nil {
		return nil, err
	}

	listener, err := net.ListenTCP("tcp", laddr)
	if err != nil {
		return nil, err
	}

	return &tcpListener{listener}, nil
}

// Use separated Accept for TCP to set keep alive. Better way?
func (l tcpListener) Accept() (net.Conn, error) {
	conn, err := l.AcceptTCP()
	if err != nil {
		return nil, err
	}

	conn.SetKeepAlive(true)
	conn.SetKeepAlivePeriod(TCPKeepAlive)

	return conn, nil
}
