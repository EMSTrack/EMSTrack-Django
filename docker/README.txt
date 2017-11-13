build:

cd ..
docker build -t cruzroja -f docker/Dockerfile .

run:

docker run -p 8000:8000 -p 8883:8883 -p 8884:8884 -ti cruzroja

self-signed certificate, as per:

https://stackoverflow.com/questions/10175812/how-to-create-a-self-signed-certificate-with-openssl

openssl req -config example-com.conf -new -x509 -sha256 -newkey rsa:2048 -nodes \
    -keyout example-com.key.pem -days 365 -out example-com.cert.pem
