"""
Dynamic Schedule Web Application and PDF Generator Server.
Run this file to launch the interactive editor in your browser:
    py app.py
"""
import os
import sys
import json
import webbrowser
import subprocess
from http.server import HTTPServer, SimpleHTTPRequestHandler
import socket

from generate_pdf import (
    load_data,
    generate_html,
    generate_tex,
    compile_pdf,
    DATA_FILE,
    HTML_FILE,
    TEX_FILE,
    PDF_FILE,
    BASE_DIR
)

def find_free_port(start_port=5500):
    port = start_port
    while port < 6500:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('127.0.0.1', port)) != 0:
                return port
            port += 1
    return 5500

class ScheduleRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=BASE_DIR, **kwargs)

    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.path = "/schedule_builder.html"
            return super().do_GET()
        elif self.path == "/api/data":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            try:
                data = load_data()
                self.wfile.write(json.dumps(data).encode("utf-8"))
            except Exception as e:
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return
        elif self.path == "/api/status":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "running"}).encode("utf-8"))
            return
        else:
            return super().do_GET()

    def do_POST(self):
        if self.path == "/api/save":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")
            try:
                data = json.loads(body)
                # 1. Save JSON
                with open(DATA_FILE, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)

                # 2. Generate HTML
                html_content = generate_html(data)
                with open(HTML_FILE, "w", encoding="utf-8") as f:
                    f.write(html_content)

                # 3. Generate LaTeX
                tex_content = generate_tex(data)
                with open(TEX_FILE, "w", encoding="utf-8") as f:
                    f.write(tex_content)

                # 4. Generate PDF
                pdf_path = compile_pdf(HTML_FILE, PDF_FILE)

                response_data = {
                    "success": True,
                    "message": "Schedule saved and PDF generated successfully!",
                    "pdfPath": PDF_FILE,
                    "texPath": TEX_FILE,
                    "htmlPath": HTML_FILE
                }
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps(response_data).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))
            return

        elif self.path == "/api/open-pdf":
            try:
                if os.path.exists(PDF_FILE):
                    os.startfile(PDF_FILE)
                    resp = {"success": True, "message": "Opening PDF..."}
                else:
                    resp = {"success": False, "error": "PDF file does not exist yet. Please generate it first."}
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps(resp).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))
            return

        self.send_error(404, "Not Found")

def main():
    port = find_free_port(5500)
    server_address = ("127.0.0.1", port)
    httpd = HTTPServer(server_address, ScheduleRequestHandler)
    url = f"http://127.0.0.1:{port}"
    print("=" * 60)
    print(f" Dynamic Schedule Builder Server Started")
    print(f" URL: {url}")
    print(" Press Ctrl+C in this terminal to stop the server.")
    print("=" * 60)

    # Open browser
    webbrowser.open(url)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
        httpd.server_close()

if __name__ == "__main__":
    main()

