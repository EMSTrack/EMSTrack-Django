Two options seem to work:

1) self-signed certificate, as per https://mcuoneclipse.com/2017/04/14/enable-secure-communication-with-tls-and-the-mosquitto-broker/:

       openssl genrsa -des3 -out example-com.ca.key 2048
       openssl req -config example-com.conf -new -x509 -key example-com.ca.key -days 3650 -out example-com.ca.crt
	   openssl genrsa -out example-com.srv.key 2048
	   openssl req -config example-com.conf -new -out example-com.srv.csr -key example-com.srv.key
	   openssl x509 -req -in example-com.srv.csr -CA example-com.ca.crt -CAkey example-com.ca.key -CAcreateserial -out example-com.srv.crt -days 3650

2) self-signed certificate, as per https://stackoverflow.com/questions/10175812/how-to-create-a-self-signed-certificate-with-openssl:

       openssl req -config example-com.conf -new -x509 -sha256 -newkey rsa:2048 -nodes -keyout example-com.key.pem -days 365 -out example-com.cert.pem

