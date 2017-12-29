docker stop nginx
docker rm nginx
# docker pull nginx:alpine
docker run -d --name nginx -p 80:80 --restart unless-stopped -v $PWD/default.conf:/etc/nginx/conf.d/default.conf:ro -v $PWD/static_content:/usr/share/nginx/html:ro nginx:alpine
