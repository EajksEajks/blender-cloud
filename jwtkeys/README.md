# Flamenco Server JWT keys

To generate a keypair for `ES256`:

    openssl ecparam -genkey -name prime256v1 -noout -out es256-private.pem
    openssl ec -in es256-private.pem -pubout -out es256-public.pem
