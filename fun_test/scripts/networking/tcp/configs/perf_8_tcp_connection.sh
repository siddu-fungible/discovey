taskset -c 8 netperf -t TCP_STREAM -H 29.1.1.2 -l 60 -f m -j -N -P 0 -- -k "THROUGHPUT" -s 128K -P 1000,4555 &
taskset -c 9 netperf -t TCP_STREAM -H 29.1.1.2 -l 60 -f m -j -N -P 0 -- -k "THROUGHPUT" -s 128K -P 1000,4555 &
taskset -c 10 netperf -t TCP_STREAM -H 29.1.1.2 -l 60 -f m -j -N -P 0 -- -k "THROUGHPUT" -s 128K -P 1000,4555 &
taskset -c 11 netperf -t TCP_STREAM -H 29.1.1.2 -l 60 -f m -j -N -P 0 -- -k "THROUGHPUT" -s 128K -P 1000,4555 &
taskset -c 12 netperf -t TCP_STREAM -H 29.1.1.2 -l 60 -f m -j -N -P 0 -- -k "THROUGHPUT" -s 128K -P 1000,4555 &
taskset -c 13 netperf -t TCP_STREAM -H 29.1.1.2 -l 60 -f m -j -N -P 0 -- -k "THROUGHPUT" -s 128K -P 1000,4555 &
taskset -c 14 netperf -t TCP_STREAM -H 29.1.1.2 -l 60 -f m -j -N -P 0 -- -k "THROUGHPUT" -s 128K -P 1000,4555 &
taskset -c 15 netperf -t TCP_STREAM -H 29.1.1.2 -l 60 -f m -j -N -P 0 -- -k "THROUGHPUT" -s 128K -P 1000,4555 &