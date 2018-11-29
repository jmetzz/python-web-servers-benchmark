#!/bin/bash


WSGI_SERVER_IMAGE="wsgi_server_benchmark"
WSGI_SERVER_CONTAINER_NAME="wsgi-server"

LOADGEN_IMAGE="wsgi_loadgen_benchmark"
LOADGEN_CONTAINER_NAME="loadgen-benchmark"

PORT=9808
CONNECTIONS=(100 200 300 400 500 600 700 800 900 1000 2000 3000 4000 5000 6000 7000 8000 9000 10000)
#CONNECTIONS=(100)
ROUNDS=1
SERVER=
STATS_PID=
IP=



ulimit -n 10240

function startServerContainer() {
    WSGI_SERVER_CONTAINER=$(docker run --name $WSGI_SERVER_CONTAINER_NAME --detach --memory 512MB --cpuset-cpus 0,1 --workdir /home/wsgi_benchmark/www -p $PORT:$PORT $WSGI_SERVER_IMAGE "$@")
    while true; do
        echo "    Waiting for container ..."
        result=$(docker inspect --format '{{ .State.Status }}' "$WSGI_SERVER_CONTAINER")
        [[ "$result" == "running" ]] && break
        sleep 1
    done
}

function startWSGIServer() {
    round="$1"
    server="$2"
    filename="$3"
    ext="$4"

    case "$ext" in
        py|pyc)
            # ignore, this is the base application that the WSGI servers wrap around
            continue
            ;;
        wsgi)
            startServerContainer python "$filename"
            ;;
        sh)
            startServerContainer ash "$filename"
            ;;
        *)
            echo "!! Unknown file type: $filename !!"
            continue
            ;;
    esac
}

function startLoadGen() {
    # task set is used to set or retrieve the CPU affinity of a running process
    # given its PID or to launch a new COMMAND with a given CPU affinity.
    # CPU affinity is a scheduler property that "bonds" a process to
    # a given set of CPUs on the system.
    # The Linux scheduler will honor the given CPU affinity and
    # the process will not run on any other CPUs.
    round=$1
    server=$2
    conn=$3

    TARGET_IP=$(docker inspect --format '{{ .NetworkSettings.IPAddress }}' "$WSGI_SERVER_CONTAINER")

    LOADGEN_CONTAINER=$(docker run --name $LOADGEN_CONTAINER_NAME --detach --memory 512MB --cpuset-cpus 2,3 --workdir /home/wsgi_benchmark/gen -v $OUTPUT_PATH:/home/wsgi_benchmark/gen/log $LOADGEN_IMAGE -i "${TARGET_IP}" -c "${conn}" -o "${server}.${round}")

    docker stats $WSGI_SERVER_CONTAINER >> "$OUTPUT_PATH/$server.$round.$connections.stats" & STATS_PID=$!

    #wait for LOADGEN_CONTAINER to finish
    echo "    Generating load ..."
    while true; do
        STATUS=$(docker inspect --format '{{ .State.Running }}' "$LOADGEN_CONTAINER")
        [[ "$STATUS" == "false" ]] && break
        sleep 1
    done
    kill $STATS_PID > /dev/null 2>&1
}

function stop() {
    $CONTAINER="$1"
    echo "    Shutting down '$CONTAINER' ..."
    docker kill "$CONTAINER" > /dev/null 2>&1 || true && docker rm "$CONTAINER" > /dev/null 2>&1 || true
}


function silentStop(){
    containers=("${@}")
    for container in "${containers[@]}"; do
        docker stop $container > /dev/null 2>&1 || true && docker rm $container > /dev/null 2>&1 || true
        sleep 1
    done
}

function buildDockerImage() {
    image="$1"
    context="$2"
    echo "Building docker image '$image'"
    docker inspect $image > /dev/null 2>&1
    [ $? -gt 0 ] && cd $context && docker build -t $image:latest . && cd -
}

function main() {
    if [ ! -z $SERVER ]; then
        target_servers=($SERVER)
    else
        if [[ "$OSTYPE" == "linux-gnu" ]]; then
            target_servers=$(find wsgi-servers/src/* | shuf)
        elif [[ "$OSTYPE" == "darwin"* ]]; then
            target_servers=$(find wsgi-servers/src/* | gshuf)
        fi
    fi

    # run for all known servers
    for round in $(seq 1 $ROUNDS); do
        echo "Starting round '$round' "
        for connections in "${CONNECTIONS[@]}"; do
            echo "    Simultaneous connections: '$connections'"

            for server in ${target_servers[@]}; do
                filename=$(basename "$server")
                server="${filename%.*}"
                ext="${filename##*.}"
                startWSGIServer "$round" "$server" "$filename" "$ext"
                sleep 5
                startLoadGen "$round" "$server" "$connections"
                silentStop $WSGI_SERVER_CONTAINER $LOADGEN_CONTAINER
                sleep 1
            done
        done
    done
}


function usage {
    echo "$0 [OPTIONS]"
    echo "       -h shows this message"
    echo "       -o output path"
    echo "       -r the number of rounds to perform the benchmark"
    echo
}

function error {
    echo "$2" >&2
    usage
    exit $1
}

while getopts ":ho:r:s:" opt; do
    case "${opt}" in
        h)
            usage
            exit 0
            ;;
        o)
            OUTPUT_PATH="${OPTARG}"
            ;;
        r)
            ROUNDS="${OPTARG}"
            ;;
        s)
            SERVER="${OPTARG}"
            ;;
        :)
            error 2 "Option -$OPTARG requires an argument."
            ;;
        \?)
            error 1 "Invalid option: -$OPTARG"
            ;;
    esac
done
shift $((OPTIND-1))

remaining_arguments=( "$@" )
if [[ ${#remaining_arguments[*]} -gt 0 ]]; then
    error 1 "Too many arguments"
fi




# ------------------------------------------
#   Start the tests
# ------------------------------------------


# Make sure there is no wsgi_benchmark container running
echo "Preparing environment"
silentStop $WSGI_SERVER_CONTAINER_NAME $LOADGEN_CONTAINER_NAME

# Install docker image (if needed)
buildDockerImage $WSGI_SERVER_IMAGE "./wsgi-servers"
echo
echo
buildDockerImage $LOADGEN_IMAGE "./loadgen"
echo
echo

main
