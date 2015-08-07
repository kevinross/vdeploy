#!/bin/bash

VM="$1"
I=0

# wait for the domain to shut down
while xl list | grep $VM; do
	# some domains shut down but don't die (flags ---s--), give them 2 seconds (as s means OS halted)
	# then destroy the domain
	if xl list | grep $VM | grep s--; then
		I=$(($I+1));
		if [ $I -ge 2 ]; then
			xl destroy $VM;
		fi
	fi
	sleep 1;
done
