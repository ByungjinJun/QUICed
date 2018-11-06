package common

import (
	"crypto/tls"
	"errors"
	"net"
	"sync"
	"log"
	"math"

	quic "github.com/lucas-clemente/quic-go"
)

// gQUIC version consts are copied from quic-go due to the multiplexing error in gQUIC version 44.
// Although DialAddr seems okay with multiplexing, SupportedVersions is required in quic listener
// to avoid malformed packets in wireshark (this also causes unnecessary additional packets)
//------------------------------------------------------------------------------------------------
// gQUIC version range as defined in the wiki: https://github.com/quicwg/base-drafts/wiki/QUIC-Versions
const (
	gquicVersion0   = 0x51303030
	maxGquicVersion = 0x51303439
)
// The version numbers, making grepping easier
const (
	Version39       quic.VersionNumber = gquicVersion0 + 3*0x100 + 0x9
	Version43       quic.VersionNumber = gquicVersion0 + 4*0x100 + 0x3
	//Version44       quic.VersionNumber = gquicVersion0 + 4*0x100 + 0x4
	VersionTLS      quic.VersionNumber = 101
	VersionWhatever quic.VersionNumber = 0 // for when the version doesn't matter
	VersionUnknown  quic.VersionNumber = math.MaxUint32
)
// SupportedVersions lists the versions that the server supports must be in sorted descending order
var SupportedVersions = []quic.VersionNumber{
	//Version44,
	Version43,
	Version39,
}
//------------------------------------------------------------------------------------------------

// QuicConfig is the config for QUIC client and server
type QuicConfig struct {
	TLSConfig   *tls.Config
	KeepAlive   bool
}

// CLIENT FEATURES
//------------------------------------------------------------------------------------------------
type quicConn struct {
	quic.Stream
	localAddr  net.Addr
	remoteAddr net.Addr
}

// net.Conn requirements
func (c *quicConn) LocalAddr() net.Addr {
	return c.localAddr
}
func (c *quicConn) RemoteAddr() net.Addr {
	return c.remoteAddr
}

// quicDialer functions as an address multiplexer (quic-go has con multiplexer)
type quicDialer struct {
	config   *QuicConfig
	Mutex    sync.Mutex
	sessions map[string]quic.Session
}

// QUICDialer creates a QUIC Dialer with QuicConfig
func QUICDialer(config *QuicConfig) Dialer {
	if config == nil {
		config = &QuicConfig{}
	}

	if config.TLSConfig == nil {
		config.TLSConfig = &tls.Config{InsecureSkipVerify: true}
	}

	return &quicDialer{
		config: config,
		sessions: make(map[string]quic.Session),
	}
}

func (dr *quicDialer) Dial(addr string) (net.Conn, error) {
	// set quic-go config for DialAddr
	qConfig := &quic.Config{
		//Versions:		  SupportedVersions,
		HandshakeTimeout: QUICHandshakeTimeout,
		IdleTimeout:      QUICIdleTimeout,
		KeepAlive:        dr.config.KeepAlive,
	}

	dr.Mutex.Lock()
	defer dr.Mutex.Unlock()

	session, ok := dr.sessions[addr]
	// Initially quicDialer has no quic session
	if !ok || session == nil {
		// quic.DialAddr Resolves UDP addr and Listen
		s, err := quic.DialAddr(addr, dr.config.TLSConfig, qConfig)
		if err != nil {
			log.Println("[QUIC CL ERR] dial session failed:", err)
		}
		session = s
		dr.sessions[addr] = session
	}

	stream, err := session.OpenStreamSync()
	if err != nil {
		log.Println("[1/2] open stream from session no success:", err, "\ntry to open new session")
		session.Close()
		s, err := quic.DialAddr(addr, dr.config.TLSConfig, qConfig)
		if err != nil {
			log.Println("[2/2] dial new session failed:", err)
			delete(dr.sessions, addr)
			return nil, err
		}
		session = s
		dr.sessions[addr] = session

		stream, err = session.OpenStreamSync()
		if err != nil {
			log.Println("[2/2] open stream from new session failed:", err)
			delete(dr.sessions, addr)
			return nil, err
		}
		log.Println("[2/2] open stream from new session OK")
	}

	return &quicConn{
		Stream:     stream,
		localAddr:  session.LocalAddr(),
		remoteAddr: session.RemoteAddr(),
	}, nil
}

// SERVER FEATURES
//------------------------------------------------------------------------------------------------
type quicListener struct {
	listener quic.Listener
	connChan chan net.Conn
	errChan  chan error
}

// QUICListener creates a Listener for QUIC proxy server.
func QUICListener(addr string, config *QuicConfig) (Listener, error) {
	if config == nil {
		config = &QuicConfig{}
	}
	quicConfig := &quic.Config{
		Versions:		  SupportedVersions,
		HandshakeTimeout: QUICHandshakeTimeout,
		IdleTimeout:      QUICIdleTimeout,
		KeepAlive:        config.KeepAlive,
	}
	tlsConfig := config.TLSConfig

	udpAddr, err := net.ResolveUDPAddr("udp", addr)
	if err != nil {
		return nil, err
	}
	conn, err := net.ListenUDP("udp", udpAddr)
	if err != nil {
		return nil, err
	}
	listener, err := quic.Listen(conn, tlsConfig, quicConfig)
	if err != nil {
		return nil, err
	}

	l := &quicListener{
		listener: listener,
		connChan: make(chan net.Conn, 65535),
		errChan:  make(chan error, 1),
	}
	go l.accept()

	return l, nil
}

// Accept in accept accepts quic listener's session
func (l *quicListener) accept() {
	for {
		session, err := l.listener.Accept()
		if err != nil {
			log.Println("[QUIC SV ERR] accept session failed:", err)
			l.errChan <- err
			close(l.errChan)
			return
		}

		log.Println("[QUIC] accept session:", session.RemoteAddr(), "-", session.LocalAddr())

		go l.acceptStream(session)
	}
}

func (l *quicListener) acceptStream(session quic.Session) {
	for {
		stream, err := session.AcceptStream()
		if err != nil {
			log.Println("[QUIC SV ERR] accept stream failed:", err)
			session.Close()
			return
		}
		log.Println("[QUIC] accept stream:", session.RemoteAddr(), "-", session.LocalAddr())

		l.connChan <- &quicConn{
			Stream: stream,
			localAddr: session.LocalAddr(),
			remoteAddr: session.RemoteAddr(),
		}
	}
}

// net.Listener requirements
func (l *quicListener) Accept() (net.Conn, error) {
	var conn net.Conn
	var err error
	var ok bool
	select {
	case conn = <-l.connChan:
	case err, ok = <-l.errChan:
		if !ok {
			err = errors.New("accept on the closed listener")
		}
	}
	return conn, err
}
func (l *quicListener) Addr() net.Addr {
	return l.listener.Addr()
}
func (l *quicListener) Close() error {
	return l.listener.Close()
}
