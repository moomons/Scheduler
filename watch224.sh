#!/bin/bash
export GREP_OPTIONS='--color=auto'
greentext="\033[32m"
bold="\033[1m"
normal="\033[0m"
cyan="\033[36m"
underline="\033[4m"
threshold=1000000
ovsip=(192.168.109.214 192.168.109.215 192.168.109.224 192.168.109.225)

#echo "pingall"
#./pingall.sh

echo "Starting Watcher."
LOG_FILE="watch.log"
exec 3>&1 1>>${LOG_FILE} 2>&1
# log ref: http://stackoverflow.com/a/18462920/5676271

while :
do
    echo -e $bold$greentext"Time: "$(date +"%H:%M:%S")$normal | tee /dev/fd/3
    for ip in "${ovsip[@]}"; do
        echo -e $bold$underline"On switch $ip:"$normal | tee /dev/fd/3
        input_all=$(ovs-ofctl -O OpenFlow13 dump-flows tcp:$ip:6666 | grep priority=)
        input=$(echo -e "$input_all" | grep priority=1)  # Only P1
        echo -e "$input_all" | grep n_packets= | tee /dev/fd/3

        counter=0
        while read -r line
        do
            #echo "Current line: $line"
            #n_pkts=$(awk -v curline="$line" -F '[=,]' '{print $8}')
            n_pkts=$(echo $line | grep -Po '(?<=(n_packets=))\d*')
            # if n_pkts is empty, continue
            #echo "Got n_packets = $n_pkts"
            if (( "$n_pkts" >= "$threshold" )); then
                echo "Eliminating n_pkts = $n_pkts:" | tee /dev/fd/3
                cmd="sudo ovs-ofctl -O OpenFlow13 del-flows tcp:$ip:6666 "$(echo $line | grep -Po 'tcp\S*')
                echo "Command: $cmd" | tee /dev/fd/3
                eval $cmd
                ((counter++))
            fi
        done <<< "$input"

        if (( counter > 0 )); then
            echo -e $cyan$underline"Flow entry eliminated: $counter at $ip"$normal | tee /dev/fd/3
        fi

    done
    echo "Done. Waiting for next loop."
    sleep 2
done

