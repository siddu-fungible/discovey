taskset -c 1 netperf -t TCP_STREAM -H 29.1.1.2 -l 30 -f m -j -N -P 0 -- -k "THROUGHPUT" -s 128K -P 1000,4555 &
taskset -c 2 netperf -t TCP_STREAM -H 29.1.1.2 -l 30 -f m -j -N -P 0 -- -k "THROUGHPUT" -s 128K -P 1000,4555 &
taskset -c 3 netperf -t TCP_STREAM -H 29.1.1.2 -l 30 -f m -j -N -P 0 -- -k "THROUGHPUT" -s 128K -P 1000,4555 &
taskset -c 4 netperf -t TCP_STREAM -H 29.1.1.2 -l 30 -f m -j -N -P 0 -- -k "THROUGHPUT" -s 128K -P 1000,4555 &