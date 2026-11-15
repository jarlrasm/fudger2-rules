
FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
ADD systems /usr/share/nginx/html/systems
