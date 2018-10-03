from enum import Enum

class ProxyConfig(Enum):
	BYPASS_PROXY_HTTPS 	= 0		# Client 				->  (bypass)ProxyClient -> ***  HTTPS  ***  ->  (bypass)ProxyServer -> WebServer
	BYPASS_PROXY_QUIC 	= 1		# Client(QUIC Request) 	->  (bypass)ProxyClient -> ***  QUIC   ***  ->  (bypass)ProxyServer -> WebServer
	HTTP_PROXY_HTTPS 	= 2		# Client 				->          ProxyClient -> ***  HTTPS  ***  ->          ProxyServer -> WebServer
	QUIC_PROXY_QUIC 	= 3		# Client(QUIC Request) 	->  		ProxyClient -> ***  QUIC   ***  ->          ProxyServer -> WebServer
	HTTP_PROXY_QUIC 	= 4		# Client 				->          ProxyClient -> ***  QUIC   ***  ->          ProxyServer -> WebServer

class ServiceConfig(Enum):
	NORMAL 	= 0		# No service degredation
	# DA2GC 	= 1		# Direct Air to Ground Connection
	# MSS 	= 2		# Mobile Satellite Service