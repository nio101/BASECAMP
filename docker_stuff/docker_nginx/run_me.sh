docker pull nginx:alpine
docker run -d --name nginx -p 80:80 --restart unless-stopped -v $HOME/docker_nginx/default.conf:/etc/nginx/conf.d/default.conf:ro -v $HOME/docker_nginx/static_content:/usr/share/nginx/html:ro nginx:alpine
