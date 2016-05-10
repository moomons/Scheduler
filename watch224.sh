#!/bin/bash
export GREP_OPTIONS='--color=auto'
greentext="\033[32m"
bold="\033[1m"
normal="\033[0m"
cyan="\033[36m"
underline="\033[4m"

while :
do

echo -e $bold$greentext"Time: "$(date +"%H:%M:%S")$normal
input=$(sudo ovs-ofctl -O OpenFlow13 dump-flows datanet224 | grep priority=1)
echo -e "$input" | grep n_packets=

counter=0
while read -r line
do
    #echo "Current line: $line"
    #n_pkts=$(awk -v curline="$line" -F '[=,]' '{print $8}')
    n_pkts=$(echo $line | grep -Po '(?<=(n_packets=))\d*')
    #echo "Got n_packets = $n_pkts"
    if (( "$n_pkts" >= 50000 )); then
        echo "Eliminating n_pkts = $n_pkts:"
        cmd="sudo ovs-ofctl -O OpenFlow13 del-flows datanet224 "$(echo $line | grep -Po 'tcp\S*')
        echo "Command: $cmd"
        eval $cmd
        ((counter++))
    fi
done <<< "$input"

if (( counter > 0 )); then
    echo -e $cyan$underline"Flow entry eliminated: $counter"$normal
fi

#input=$(sudo ovs-ofctl -O OpenFlow13 dump-flows datanet224 | grep priority=1)
#echo -e "\n$input"

sleep 2
done

