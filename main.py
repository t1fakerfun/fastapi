import time
from http.server import ThreadingHTTPServer
from concurrent.futures import ThreadPoolExecutor, as_completed
import subprocess

from api_handler import RequestHandler
from server import mainServer

executor = ThreadPoolExecutor()
api_server = ThreadingHTTPServer(('127.0.0.1', 9001), RequestHandler)

mainServer.addMatch("match1", "taro", "tanaka", "../fields/tokyo.yml", time.time() + 3)

future_api = executor.submit(lambda: api_server.serve_forever())
future_server = executor.submit(lambda: mainServer.loopForever())
future_fastapi = executor.submit(lambda: subprocess.run(["uvicorn", "fastapi_main:app", "--reload", "--port", "9000"]))

try:
    for f in as_completed([future_api, future_server, future_fastapi]):
        print(f.result())
        
finally:
    api_server.shutdown()
    mainServer.shutdown()