FROM centos:7

LABEL version="1.0"
LABEL maintainer="Jean Metz"

# ENV REPO="wrk"
# ENV GIT_URL="https://github.com/wg/$REPO/archive/master.zip"

WORKDIR /home/wsgi_benchmark/gen

ENV PATH="/home/wsgi_benchmark/gen/wrk:${PATH}"

RUN yum update -y && \
    yum groupinstall -y "Development Tools" && \
    yum install -y  build-essential curl && \
    yum clean all && \
    rm -rf /var/cache/yum

RUN mkdir -p /home/wsgi_benchmark/gen/log && \
    git clone https://github.com/wg/wrk.git && \
    cd wrk && \
    make

COPY src /home/wsgi_benchmark/gen

ENTRYPOINT [ "./run.sh" ]
CMD ["run.sh", "-o", "DEFAULT_OUTPUT.log", "-i", "0.0.0.0:9898"]
