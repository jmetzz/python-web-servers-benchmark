#!/bin/bash

# taskset is used to set or retrieve the CPU affinity of a running process
# given its PID or to launch a new COMMAND with a given CPU affinity.
# CPU affinity is a scheduler property that "bonds" a process to
# a given set of CPUs on the system.
# The Linux scheduler will honor the given CPU affinity and
# the process will not run on any other CPUs.


function usage {
    echo "$0 [OPTIONS]"
    echo "       -h shows this message"
    echo "       -o output file name [REQUIRED]"
    echo "       -i the target IP address [REQUIRED]"
    echo "       -c the number of concurrent connections (Default: 100)"
    echo "       -d the time in seconds (Default: 30)"
    echo "       -t the number of threads to use (Default: 4"
    echo "       -p the target http PORT (Default: 9808)"
    echo
}

function error {
    echo "$1" >&2
    usage
    exit $2
}


PORT=9808
THREADS=4
DURATION=30
CONNECTIONS=100
BASE=/home/wsgi_benchmark/gen/log
OUTPUT=
IP=

ulimit -n 10240


while getopts ":ho:c:d:t:i:p:" opt; do
    case "${opt}" in
        h)
            usage
            exit 0
            ;;
        o)
            OUTPUT="${OPTARG}"
            ;;
        c)
            CONNECTIONS="${OPTARG}"
            ;;
        d)
            DURATION="${OPTARG}"
            ;;
        t)
            THREADS="${OPTARG}"
            ;;
        i)
            IP="${OPTARG}"
            ;;
        p)
            PORT="${OPTARG}"
            ;;
        :)
            error "Option -$OPTARG requires an argument." 2
            ;;
        \?)
            error "Invalid option: -$OPTARG" 1
            ;;
    esac
done
shift $((OPTIND-1))

remaining_arguments=( "$@" )
if [[ ${#remaining_arguments[*]} -gt 0 ]]; then
    error  "Extra arguments not allowed" 1
fi

[[ -z $OUTPUT ]] && error "Mandatory argument not given: output file name" 2

[[ -z $IP ]] && error "Mandatory argument not given: target IP" 2



echo "Bloating http://$IP:$PORT with $CONNECTIONS connections" >> "loadgen.global.log"
echo "$BASE/$OUTPUT.$CONNECTIONS.log" >> "loadgen.global.log"


taskset -c 2,3 wrk -d "${DURATION}s" -t $THREADS -c $CONNECTIONS "http://$IP:$PORT" > "${BASE}/${OUTPUT}.${CONNECTIONS}.log"
