
# Python web serves and web frameworks benchmark

This project was based on this [repository](https://github.com/omedhabib/WSGI_Benchmarks)
and the results published via a 2-parts article: 
[part 1](https://blog.appdynamics.com/engineering/an-introduction-to-python-wsgi-servers-part-1/)
and 
[part 2](https://blog.appdynamics.com/engineering/a-performance-analysis-of-python-wsgi-servers-part-2/).

However, since I could not reproduce the experiment on Mac OS box, I'v decided to adapt and extend 
the work by [Kevin Goldberg](https://blog.appdynamics.com/author/kevin/).



## Steps to reproduce benchmarks

1. Install docker
2. Prepare the python the conda environment. See the environment.yml file
3. Run run.sh <output directory>
4. Run processing/summary.py


Some useful commands for testing and debug: 

Build load generation image

    docker build -t wsgi_loadgen_benchmark:latest ./loadgen

run only wsgi server container

    docker run --detach --memory 512MB --cpuset-cpus 0,1 \ 
        --workdir /home/wsgi_benchmark/www -p 9808:9808 \
        wsgi_server_benchmark python Bjoern.wsgi


run only load generation container 

    docker run -it --workdir /home/wsgi_benchmark/gen \
        wsgi_loadgen_benchmark '/bin/bash'

run the work load from the docker shell (only from linux box)
    
    taskset -c 2,3 ./wrk/wrk -d 30s -t 4 -c 10 \
        "http://172.17.0.4:9808" > "/home/wsgi_benchmark/gen/my_test.log"

## The experiment setup

* Two docker containers were created: 1) for WSGI web server, and 2) for the load generation 
* [wrk](https://github.com/wg/wrk) is used to generate load on the target web serves.
* Each container run on 2 dedicated cores with 512 MB of RAM memory. 
* The servers are tested in a random order with an increasing number of simultaneous connections, 
    
    precisely this range 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000.
    
* Each test takes 30 seconds.
* The user can specify as a parameter the number of rounds he wants to perform the test.
* I haven't taken (yet) any specific measure to avoid cold-start.

## The measurements

The average number of sustained requests, errors (connection, read, write and timeouts)
and latencies were provided by `wrk`.
Docker’s stat tool provided the high CPU and memory watermarks.
We've and averaged the results over the rounds.


