docker run -d --name grafana -p 3000:3000 --restart unless-stopped --memory="500M" -v $PWD/grafana_data:/var/lib/grafana grafana/grafana

