#!/bin/bash

nginxfile="nginx.conf"
nginxaccess="/app/access.log"

cat > $nginxfile << EOM
events {
  worker_connections  1024;
}
http {
  error_log stderr;
  server {
    listen 80;
    listen [::]:80;
    server_name localhost;
    access_log $nginxaccess;

EOM

while [ $# -gt 0 ]
do
        dp="$1"
        IFS='=' read -ra pieces <<< "$dp"
        echo "Path: ${pieces[0]} => ${pieces[1]}"
        cat >> $nginxfile << EOM
    location ${pieces[0]} {
EOM
        if [ "${pieces[0]}" != "/" ]; then
            cat >> $nginxfile << EOM
        rewrite ${pieces[0]}/(.*) /\$1 break;
EOM
        fi
        cat >> $nginxfile << EOM
        proxy_pass ${pieces[1]};
    }
EOM
        shift
done


cat >> $nginxfile << EOM

  } 
}
EOM

cat $nginxfile

# Start nginx
cp $nginxfile /etc/nginx/nginx.conf
touch $nginxaccess
tail -f $nginxaccess 1>&2 &
exec nginx -g 'daemon off;'
