
# WSGI Benchmarks

This benchmark will run with 2 dedicated CPU cores for the load generation and 2 dedicate CPU cores for the WSGI servers.

## Steps to reproduce benchmarks

1. Install docker
2. Run run.sh <output directory>
3. Run processing/summary.py



### Some useful commands to debug 

Build load generation image

    docker build -t wsgi_loadgen_benchmark:latest ./loadgen

run only wsgi server container

    docker run --detach --memory 512MB --cpuset-cpus 0,1 --workdir /home/wsgi_benchmark/www -p 9808:9808 wsgi_server_benchmark python Bjoern.wsgi


run only load generation container 

    docker run -it --workdir /home/wsgi_benchmark/gen wsgi_loadgen_benchmark '/bin/bash'

run the work load from the docker shell (only from linux box)
    
    taskset -c 2,3 ./wrk/wrk -d 30s -t 4 -c 10 "http://172.17.0.4:9808" > "/home/wsgi_benchmark/gen/my_test.log"

