"""本地测速用：带 gzip + 缓存头的静态服务器（模拟 GitHub Pages）。python3 gzserve.py <dir> <port>"""
import sys,os,gzip,http.server,functools
class H(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*a): pass
    def send_head(self):
        p=self.translate_path(self.path)
        if os.path.isdir(p): p=os.path.join(p,'index.html')
        if not os.path.isfile(p): return super().send_head()
        b=open(p,'rb').read(); ct=self.guess_type(p)
        gz='gzip' in self.headers.get('Accept-Encoding','') and not p.endswith(('.jpg','.png','.webp'))
        if gz: b=gzip.compress(b,6)
        self.send_response(200); self.send_header('Content-Type',ct); self.send_header('Content-Length',str(len(b)))
        if gz: self.send_header('Content-Encoding','gzip')
        self.send_header('Cache-Control','max-age=600'); self.end_headers()
        import io; return io.BytesIO(b)
http.server.ThreadingHTTPServer(('127.0.0.1',int(sys.argv[2])),functools.partial(H,directory=sys.argv[1])).serve_forever()
