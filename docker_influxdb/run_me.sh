docker run -d --name influxdb -p 8086:8086 --restart unless-stopped --memory="1G" -v $PWD/influxdb_data:/var/lib/influxdb influxdb:alpine

