package common

import (
	"bufio"
	"fmt"
	"net"
	"net/http"
	"net/url"
	"strings"
	"log"
	"io"
)

//TODO: HTTP2 handler
type httpHandler struct {
	options *HandlerOptions
}

// HTTPHandler creates a server Handler for HTTP proxy server.
func HTTPHandler(opts ...HandlerOption) Handler {
	h := &httpHandler{
		options: &HandlerOptions{},
	}
	for _, opt := range opts {
		opt(h.options)
	}
	return h
}

//Handle read requests from conn and pass it to *handleRequest*
func (h *httpHandler) Handle(conn net.Conn) {
	defer conn.Close()

	req, err := http.ReadRequest(bufio.NewReader(conn))
	if err != nil {
		log.Println("[HTTP ERR]", conn.RemoteAddr(), "->", conn.LocalAddr(), "\n", err)
		return
	}
	if req == nil {
		log.Println("[HTTP]: empty request")
		return
	}
	defer req.Body.Close()

	// for debugging
	//dump, _ := httputil.DumpRequest(req, false)
	//log.Println("[HTTP LOG]", conn.RemoteAddr(), "->", req.Host, "\n", string(dump))

	h.handleRequest(conn, req)
}

// handleRequest deliver the request to the next hop
func (h *httpHandler) handleRequest(conn net.Conn, req *http.Request) {
	host := req.Host
	if !strings.Contains(host, ":") {
		host += ":80"
	}

	// The next hop is ...
	// the target server if this is the server-proxy
	// the server-proxy if this is the client-proxy
	var cNextHop net.Conn
	var err error
	if h.options.Tunnel == nil {
		cNextHop, err = net.DialTimeout("tcp", host, DialTimeout)
	} else {
		cNextHop, err = h.options.Tunnel.ConnectProxy(host)
	}
	if err != nil {
		log.Println("[HTTP ERR]", conn.RemoteAddr(), "->", host, "\n", err)

		// If *Connect* fails, send the error msg to the previous hop
		b := []byte("HTTP/1.1 503 Service unavailable\r\n\r\n")
		conn.Write(b)
		return
	}
	defer cNextHop.Close()

	// If *Connect* succeeds, send the success msg to the previous hop
	// After the connection established, write the request to the next hop
	if req.Method == http.MethodConnect {
		b := []byte("HTTP/1.1 200 Connection established\r\n\r\n")
		conn.Write(b)
	} else {
		req.Header.Del("Proxy-Connection")

		err = req.Write(cNextHop)
		if err != nil {
			log.Println("[HTTP ERR]", conn.RemoteAddr(), "->", host, "\n", err)
			return
		}
	}

	log.Println("[HTTP] established:", cNextHop.LocalAddr(), "-", host)
	transfer(conn, cNextHop)
	log.Println("[HTTP] closed:", cNextHop.LocalAddr(), "-", host)
}

// ConnectHTTP sends the connect msg to the target
func ConnectHTTP(conn net.Conn, addr string) (net.Conn, error) {
	req := &http.Request{
		Method:     http.MethodConnect,
		URL:        &url.URL{Host: addr},
		Host:       addr,
		ProtoMajor: 1,
		ProtoMinor: 1,
		Header:     make(http.Header),
	}
	req.Header.Set("Proxy-Connection", "keep-alive")

	err := req.Write(conn)
	if err != nil {
		return nil, err
	}

	resp, err := http.ReadResponse(bufio.NewReader(conn), req)
	if err != nil {
		return nil, err
	}

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("%s", resp.Status)
	}

	return conn, nil
}

// transfer passes actual data through the tunnel
func transfer(rw1, rw2 io.ReadWriter) error {
	e := make(chan error, 1)
	go func() {
		_, err := io.Copy(rw1, rw2)
		e <- err
	}()

	go func() {
		_, err := io.Copy(rw2, rw1)
		e <- err
	}()

	err := <-e
	if err == io.EOF {
		err = nil
	}
	return err
}
