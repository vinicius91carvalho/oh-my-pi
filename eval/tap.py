# Logging proxy in front of oMLX. Forwards everything to 1337 and writes each
# request body to disk, so the exact JSON omp sends can be audited.
import http.server, json, os, re, socketserver, urllib.request, urllib.error, threading

OUT = os.environ["TAP_OUT"]
UP = "http://127.0.0.1:1337"
# TAP_STUB=1 answers from the proxy instead of forwarding. Token counting only
# needs the request body, and a real 22k-token cold prefill costs minutes, so
# profile sweeps run stubbed and only the final winners go to the server.
STUB = os.environ.get("TAP_STUB") == "1"
n = [0]
lock = threading.Lock()

class H(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _forward(self, body):
        req = urllib.request.Request(UP + self.path, data=body, method=self.command)
        for k, v in self.headers.items():
            if k.lower() not in ("host", "content-length", "connection", "accept-encoding"):
                req.add_header(k, v)
        return urllib.request.urlopen(req, timeout=1800)

    def do_POST(self):
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length)
        with lock:
            n[0] += 1
            i = n[0]
        try:
            parsed = json.loads(body)
            with open(f"{OUT}/req-{i:03d}.json", "w") as f:
                json.dump(parsed, f, indent=2, ensure_ascii=False)
        except Exception as e:
            with open(f"{OUT}/req-{i:03d}.raw", "wb") as f:
                f.write(body)
        if STUB and self.path.endswith("/chat/completions"):
            self._stub()
            return
        self._relay(body, i)

    def _stub(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Transfer-Encoding", "chunked")
        self.end_headers()
        events = [
            {"choices": [{"index": 0, "delta": {"role": "assistant", "content": "OK"}}]},
            {"choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
             "usage": {"prompt_tokens": 0, "completion_tokens": 1, "total_tokens": 1}},
        ]
        for e in events:
            payload = ("data: " + json.dumps(e) + "\n\n").encode()
            self.wfile.write(b"%x\r\n" % len(payload) + payload + b"\r\n")
        done = b"data: [DONE]\n\n"
        self.wfile.write(b"%x\r\n" % len(done) + done + b"\r\n")
        self.wfile.write(b"0\r\n\r\n")
        self.wfile.flush()

    def do_GET(self):
        self._relay(None, None)

    def _relay(self, body, i):
        try:
            r = self._forward(body)
        except urllib.error.HTTPError as e:
            r = e
        except Exception as e:
            self.send_response(502); self.end_headers()
            self.wfile.write(str(e).encode()); return
        self.send_response(r.status)
        for k, v in r.headers.items():
            if k.lower() in ("content-length", "transfer-encoding", "connection"):
                continue
            self.send_header(k, v)
        self.send_header("Transfer-Encoding", "chunked")
        self.end_headers()
        buf = bytearray()
        while True:
            chunk = r.read(4096)
            if not chunk:
                break
            buf += chunk
            self.wfile.write(b"%x\r\n" % len(chunk) + chunk + b"\r\n")
            self.wfile.flush()
        self.wfile.write(b"0\r\n\r\n")
        # Keep the server's own usage next to the request: prompt_tokens is the
        # authoritative context size, and a 400 here is "Prompt too long".
        if i is not None:
            usage, text = None, bytes(buf).decode("utf-8", "replace")
            for line in text.splitlines():
                line = line.strip()
                if not line.startswith("data:"):
                    continue
                try:
                    ev = json.loads(line[5:].strip())
                except Exception:
                    continue
                if isinstance(ev, dict) and ev.get("usage"):
                    usage = ev["usage"]
            if usage is None and r.status < 400 and text.lstrip().startswith("{"):
                try: usage = json.loads(text).get("usage")
                except Exception: pass
            with open(f"{OUT}/usage-{i:03d}.json", "w") as f:
                json.dump({"status": r.status, "usage": usage,
                           "error": text[:300] if r.status >= 400 else None}, f)

    def log_message(self, *a):
        pass

class T(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True

T(("127.0.0.1", 1338), H).serve_forever()
