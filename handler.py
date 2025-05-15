import runpod
import threading
import os
import signal
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
import asyncio

# Global flag to track server status
server_running = True
server_instance = None
mode_to_run = os.getenv("MODE_TO_RUN", "pod")

class SimpleHTTPHandler(BaseHTTPRequestHandler):
    """Simple HTTP handler with Hello World and terminate button"""
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/':
            # Serve the main page with Hello World and terminate button
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            html = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>RunPod Web Server</title>
                <style>
                    body {
                        font-family: Arial, sans-serif;
                        margin: 0;
                        padding: 20px;
                        display: flex;
                        flex-direction: column;
                        align-items: center;
                        justify-content: center;
                        height: 100vh;
                        background-color: #f5f5f5;
                    }
                    .container {
                        background-color: white;
                        padding: 30px;
                        border-radius: 8px;
                        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                        text-align: center;
                    }
                    h1 {
                        color: #333;
                    }
                    button {
                        background-color: #e74c3c;
                        color: white;
                        border: none;
                        padding: 10px 20px;
                        margin-top: 20px;
                        border-radius: 4px;
                        cursor: pointer;
                        font-size: 16px;
                    }
                    button:hover {
                        background-color: #c0392b;
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>Hello World!</h1>
                    <p>This is a simple web server running on RunPod.</p>
                    <button onclick="terminateServer()">Terminate Server</button>
                </div>
                
                <script>
                    function terminateServer() {
                        fetch('/terminate', {
                            method: 'POST'
                        })
                        .then(response => response.text())
                        .then(data => {
                            alert('Server is shutting down...');
                            setTimeout(() => {
                                document.body.innerHTML = '<div class="container"><h1>Server Terminated</h1><p>The server has been shut down.</p></div>';
                            }, 1000);
                        })
                        .catch(error => {
                            console.error('Error:', error);
                        });
                    }
                </script>
            </body>
            </html>
            """
            
            self.wfile.write(html.encode())
        else:
            # Return 404 for any other path
            self.send_response(404)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b"Not found")
    
    def do_POST(self):
        """Handle POST requests"""
        if self.path == '/terminate':
            # Handle terminate request
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b"Server is shutting down")
            
            # Set the global flag to False to signal termination
            global server_running
            server_running = False
            
            # Schedule the server to stop
            threading.Thread(target=self.server.shutdown).start()
        else:
            # Return 404 for any other path
            self.send_response(404)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b"Not found")

def run_server():
    """Run the HTTP server"""
    global server_instance
    
    # Create and configure the server
    port = int(os.environ.get('PORT', 8000))
    server_instance = HTTPServer(('0.0.0.0', port), SimpleHTTPHandler)
    
    print(f"Starting server on port {port}")
    
    # Start the server
    try:
        server_instance.serve_forever()
    except Exception as e:
        print(f"Server error: {e}")
    finally:
        print("Server has been shut down")

def handler(job):
    """
    RunPod handler that starts a web server and waits for it to be terminated
    """
    job_input = job["input"]
    
    # Extract port from input if provided
    if "port" in job_input:
        os.environ['PORT'] = str(job_input["port"])
    
    # Get the current pod ID for URL construction
    pod_id = os.environ.get('RUNPOD_POD_ID', 'unknown')
    port = os.environ.get('PORT', '8000')
    
    # Start the server in a separate thread
    server_thread = threading.Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()
    
    # URL that can be used to access the server
    access_url = f"https://{pod_id}-{port}.proxy.runpod.net"
    print(access_url)
    
    # Wait for the server to be terminated
    while server_running:
        time.sleep(1)
    
    # At this point, server_running has been set to False by the terminate button
    return {
        "status": "completed",
        "message": "Web server was terminated by user"
    }

# Start the serverless handler
if mode_to_run in ["serverless"]:
    # Assuming runpod.serverless.start is correctly implemented elsewhere
    runpod.serverless.start({
        "handler": handler,
    })

if mode_to_run == "pod":
    async def main():
        requestObject = {"input": {}}
        
        response = await handler(requestObject)
        print(response)

    asyncio.run(main())