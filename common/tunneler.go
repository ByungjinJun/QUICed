package common

import (
	"net"
)

// Tunneler connects to a server-proxy through client-proxy
type Tunneler struct {
	Dialer		Dialer
	ProxyAddr	string
}

// Dialer dials and handshakes with the server-proxy over conn
type Dialer interface {
	Dial(addr string) (net.Conn, error)
}

func (t *Tunneler) Dial(addr string) (net.Conn, error) {
	return t.Dialer.Dial(addr)
}

// ConnectProxy connects to the target proxy address.
func (t *Tunneler) ConnectProxy(addr string) (net.Conn, error) {
	// Dial to the server-proxy
	c, err := t.Dial(t.ProxyAddr)
	if err != nil {
		return nil, err
	}

	// Connect to a http server through the connection with the server-proxy
	conn, err := ConnectHTTP(c, addr)
	if err != nil {
		c.Close()
		return nil, err
	}

	return conn, err
}

type tcpDialer struct {}

// DefaultDialer creates a TCP dialer
func DefaultDialer() Dialer {
	return &tcpDialer{}
}

func (dialer *tcpDialer) Dial(addr string) (net.Conn, error) {
	return net.DialTimeout("tcp", addr, DialTimeout)
}
