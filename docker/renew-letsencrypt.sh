#!/bin/bash -e

cd /data/letsencrypt

certbot renew

echo
echo "Recreating HAProxy certificates"

for certdir in /etc/letsencrypt/live/*; do
    domain=$(basename $certdir)
    echo "  - $domain"

    cat $certdir/privkey.pem $certdir/fullchain.pem > $domain.pem
    mv $domain.pem /data/certs/
done


echo
echo -n "Restarting "
docker restart haproxy

echo "Certificate renewal completed."

