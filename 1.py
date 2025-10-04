import http.server
import socketserver
import os
import shutil
import urllib.parse
import time

UPLOAD_DIR = r"E:\local-share\uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

class UploadHandler(http.server.SimpleHTTPRequestHandler):

    def do_POST(self):
        if self.path != '/upload':
            self.send_error(404)
            return

        # Parse multipart/form-data manually
        content_length = int(self.headers['Content-Length'])
        boundary = self.headers['Content-Type'].split("boundary=")[1].encode()
        body = self.rfile.read(content_length)

        parts = body.split(b"--" + boundary)
        for part in parts:
            if b'Content-Disposition' in part and b'name="file"' in part:
                headers, file_data = part.split(b'\r\n\r\n', 1)
                file_data = file_data.rstrip(b'\r\n--')
                # Extract filename
                for line in headers.split(b'\r\n'):
                    if b'filename=' in line:
                        filename = line.split(b'filename=')[1].strip().strip(b'"')
                        filename = filename.decode()
                        break
                # Save file
                dest = os.path.join(UPLOAD_DIR, filename)
                if os.path.exists(dest):
                    base, ext = os.path.splitext(filename)
                    dest = os.path.join(UPLOAD_DIR, f"{base}_{int(time.time())}{ext}")
                with open(dest, 'wb') as f:
                    f.write(file_data)

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(b'{"success": true}')

    def list_directory(self, path):
        files = os.listdir(UPLOAD_DIR)
        files_html = ""
        for f in sorted(files):
            url = '/uploads/' + urllib.parse.quote(f)
            files_html += f'<li><a href="{url}" download>{f}</a></li>\n'
        if not files_html:
            files_html = '<li><em>No files uploaded yet.</em></li>'

        html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Local File Share</title>
<style>
body {{ font-family: Arial, Helvetica, sans-serif; max-width:800px; margin:2rem auto; }}
.card {{ border:1px solid #ddd; padding:1rem; border-radius:8px; margin-bottom:1rem; }}
progress {{ width:100%; height:14px; }}
ul {{ list-style:none; padding:0; }}
li {{ padding:.25rem 0; }}
</style>
</head>
<body>
<h1>📤 Local File Share</h1>
<div class="card">
<h3>Upload a file</h3>
<form id="uploadForm" enctype="multipart/form-data" method="post" action="/upload">
<input type="file" name="file" id="fileInput" required />
<br><br>
<button type="submit">Upload</button>
<br><br>
<progress id="progressBar" value="0" max="100"></progress>
<div id="status"></div>
</form>
</div>

<div class="card">
<h3>Available files (click to download)</h3>
<ul>
{files_html}
</ul>
</div>

<script>
const form = document.getElementById('uploadForm');
const progressBar = document.getElementById('progressBar');
const status = document.getElementById('status');

form.addEventListener('submit', function(e) {{
    e.preventDefault();
    const fileInput = document.getElementById('fileInput');
    if (!fileInput.files.length) return;
    const fd = new FormData();
    fd.append('file', fileInput.files[0]);

    const xhr = new XMLHttpRequest();
    xhr.open('POST', '/upload', true);

    xhr.upload.onprogress = function(ev) {{
        if (ev.lengthComputable) {{
            progressBar.value = (ev.loaded / ev.total) * 100;
        }}
    }};

    xhr.onload = function() {{
        if (xhr.status >= 200 && xhr.status < 300) {{
            status.textContent = '✅ Upload complete';
            setTimeout(function() {{ window.location.reload(); }}, 400);
        }} else {{
            status.textContent = '❌ Upload failed';
        }}
    }};

    xhr.onerror = function() {{
        status.textContent = '❌ Network error';
    }};

    xhr.send(fd);
}});
</script>
</body>
</html>"""
        encoded = html.encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

Handler = UploadHandler

if __name__ == "__main__":
    PORT = 8000
    with socketserver.TCPServer(("0.0.0.0", PORT), Handler) as httpd:
        print(f"Serving on http://0.0.0.0:{PORT} (uploads saved to {UPLOAD_DIR})")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down")
            httpd.shutdown()
