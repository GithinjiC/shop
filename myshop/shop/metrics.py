# import http.server
# from prometheus_client import start_http_server, Summary, Counter, Gauge
import prometheus_client


REQUEST_TIME = prometheus_client.Summary('request_seconds', 'Time spent processing request')
REQUESTS = prometheus_client.Counter('shop_requests_total', 'Total number of requests', ['view_function', ])
EXCEPTIONS = prometheus_client.Counter('shop_exceptions_total', 'Total number of exceptions')
PROGRESS = prometheus_client.Gauge('shop_requests_inprogress', 'Number of requests in progress')
