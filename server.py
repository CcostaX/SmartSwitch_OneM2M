import http.server
import socketserver
import p2p_smartswitch

# Define your values here
my_value = "Hello, World!"

class MyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(bytes(f"<h1>{my_value}</h1>", 'utf-8'))
        else:
            self.send_error(404)

# Set the port number you want to use
port = 8081

# Start the server
with socketserver.TCPServer(("", port), MyHandler) as httpd:
    print(f"Server running on http://localhost:{port}")
    httpd.serve_forever()
