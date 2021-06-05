docker stop grafana
docker rm grafana
docker pull grafana/grafana
docker run -d --name grafana -p 3000:3000 --restart unless-stopped --memory="500M" -v $HOME/docker_grafana/custom.ini,/etc/grafana/grafana.ini -v $HOME/docker_grafana/grafana_data:/var/lib/grafana -e "GF_AUTH_ANONYMOUS_ENABLED=true" grafana/grafana
