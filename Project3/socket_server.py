import os
import socket
from datetime import datetime

class SocketServer:
    def __init__(self):
        self.bufsize = 4096
        self.DIR_PATH = './request'
        self.createDir(self.DIR_PATH)

        # 응답 메시지 준비
        body = b"<html><body>I've got your message</body></html>"
        header = (
            b"HTTP/1.1 200 OK\r\n"
            b"Server: socket server v0.1\r\n"
            b"Content-Type: text/html\r\n"
            + f"Content-Length: {len(body)}\r\n\r\n".encode()
        )
        self.RESPONSE = header + body

    def createDir(self, path):
        if not os.path.exists(path):
            os.makedirs(path)

    def run(self, ip, port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((ip, port))
        sock.listen(5)
        print(f"✅ Start the socket server on {ip}:{port}\n")

        try:
            while True:
                clnt_sock, req_addr = sock.accept()
                print(f"[{datetime.now()}] Request from {req_addr}")
                clnt_sock.settimeout(3)

                # --- Step 1: 먼저 헤더만 읽기 ---
                header_data = b""
                while b"\r\n\r\n" not in header_data:
                    chunk = clnt_sock.recv(self.bufsize)
                    if not chunk:
                        break
                    header_data += chunk
                    if len(header_data) > 100000:  # 너무 큰 경우 방지
                        break

                # --- Step 2: Content-Length 확인 ---
                content_length = 0
                try:
                    for line in header_data.split(b"\r\n"):
                        if b"Content-Length:" in line:
                            content_length = int(line.split(b":")[1].strip())
                            break
                except:
                    pass

                # --- Step 3: 본문(body) 읽기 ---
                header_end = header_data.find(b"\r\n\r\n") + 4
                body = header_data[header_end:]
                bytes_to_read = content_length - len(body)

                while bytes_to_read > 0:
                    chunk = clnt_sock.recv(min(self.bufsize, bytes_to_read))
                    if not chunk:
                        break
                    body += chunk
                    bytes_to_read -= len(chunk)

                data = header_data[:header_end] + body

                # --- Step 4: 요청 전체 저장 ---
                filename = datetime.now().strftime("%Y-%m-%d-%H-%M-%S.bin")
                filepath = os.path.join(self.DIR_PATH, filename)
                with open(filepath, "wb") as f:
                    f.write(data)
                print(f"📂 Saved request to {filepath}")

                # --- Step 5: multipart 이미지 추출 ---
                if b"multipart/form-data" in data:
                    try:
                        boundary = data.split(b"boundary=")[1].split(b"\r\n")[0]
                        parts = data.split(b"--" + boundary)
                        for part in parts:
                            if b"Content-Type: image" in part:
                                start = part.find(b"\r\n\r\n") + 4
                                end = part.rfind(b"\r\n")
                                image_data = part[start:end]
                                img_filename = "received_image.jpg"
                                with open(img_filename, "wb") as img:
                                    img.write(image_data)
                                print(f"🖼️ Image extracted and saved as {img_filename}")
                    except Exception as e:
                        print("⚠️ Error parsing multipart data:", e)

                # --- Step 6: 응답 보내기 ---
                clnt_sock.sendall(self.RESPONSE)
                clnt_sock.close()
                print("✅ Response sent.\n")

        except KeyboardInterrupt:
            print("\n🛑 Server stopped.")
            sock.close()

if __name__ == "__main__":
    server = SocketServer()
    server.run("127.0.0.1", 8000)
