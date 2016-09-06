FROM alpine
MAINTAINER jean-francois.nadeau@ticketmaster.com
RUN apk -U add python py-pip
RUN pip install pykube 
RUN pip install boto3
COPY kube-ecr-creds.py /usr/local/bin/
CMD ["/usr/local/bin/kube-ecr-creds.py"]
