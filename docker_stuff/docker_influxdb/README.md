./run_me.sh

docker run --rm --link=influxdb -it influxdb influx -host influxdb
> show databases
name: databases
name
----
_internal
basecamp
> drop database basecamp
> drop database basecamp_24h
> create database basecamp with duration 180d
> create database basecamp_24h with duration 1d
> show databases
