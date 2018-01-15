docker pull influxdb:alpine
docker run -d --name influxdb -p 8086:8086 --restart unless-stopped --memory="1G" -v $HOME/docker_influxdb/influxdb_data:/var/lib/influxdb influxdb:alpine
