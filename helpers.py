import socket

def communicate(host, port, request):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    s.send(request.encode('ascii'))
    response = s.recv(1024)
    s.close()
    return response.decode('ascii')
