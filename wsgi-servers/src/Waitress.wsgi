from app import application
from waitress import serve

serve(application, listen='*:9808')


# Different approaches to serve:
## By default Waitress binds to any IPv4 address on port 8080
## serve(wsgiapp)
## 
## You can also specify the host IP address and the PORT
## serve(wsgiapp, host='0.0.0.0', port=8080)
##
## You can serve for both IPv4 and IPv6 on PORT 8080 as
## serve(wsgiapp, listen='*:8080')
##
## If you want to serve your application through a UNIX domain socket 
## serve(wsgiapp, unix_socket='/path/to/unix.sock')