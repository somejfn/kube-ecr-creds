#!/usr/bin/env python

import boto3
import pykube
import os
import operator
import base64
import json
import sys
import time
import datetime


class ecr():
    def __init__(self,name,region,keyid,keysecret):
        self.name = name
        self.region = region
        self.keyid = keyid
        self.keysecret = keysecret
        self.client = boto3.client(
                            'ecr', 
                            aws_access_key_id=self.keyid, 
                            aws_secret_access_key=self.keysecret, region_name=self.region)
    def get_token(self):
        return self.client.get_authorization_token(registryIds=[self.name,])

    # dockerconfig file
    def make_secret(self,token):
        self.token = token
        obj = { "auths": { self.token['proxyEndpoint']: { "auth": self.token['authorizationToken']}}}
        return obj


class kube_api():
    def __init__(self):
        # Make sure to use service hostname as IP would fail cert validation
        os.environ['PYKUBE_KUBERNETES_SERVICE_HOST'] = "kubernetes.default.svc.cluster.local"
        self.api = pykube.HTTPClient(pykube.KubeConfig.from_service_account())
    
    def get_secret(self, name):
        self.name = name
        try:
           return pykube.Secret.objects(self.api).get_by_name(self.name)
        except:
           return None

    def write_secret(self,name,secret,mode):
        self.name = name
        self.secret = secret
        self.mode = mode
        obj = {
         "kind": "Secret",
         "apiVersion": "v1",
         "metadata": {
            "name": self.name,
            "namespace": "default",
             },
         "data": {".dockerconfigjson": self.secret },
         "type": "kubernetes.io/dockerconfigjson"
         }
        if mode == "update":
            ret = pykube.Secret(self.api, obj).update()
        else:
            ret = pykube.Secret(self.api, obj).create()
        return ret


def get_environ():
    environ = ["AWS_REGION","REGISTRY","AWS_ACCESS_KEY_ID","AWS_SECRET_ACCESS_KEY","KUBE_SECRET","INTERVAL"]
    params = {}
    for i in environ:
        try:
            params[i] = os.environ[i]
        except:
            print "Please set env for var: " + i
            sys.exit(1)
    return params

def now():
    return str(datetime.datetime.utcnow())



def main():
    # We expect all env to be present in the container
    params = get_environ()
    # Our ECR instance
    myecr = ecr(params['REGISTRY'],params['AWS_REGION'],params['AWS_ACCESS_KEY_ID'],params['AWS_SECRET_ACCESS_KEY'])     
    # Our Kubernetes API instance
    kube = kube_api()
    while True:
        # Get the authorization token for the ECR registry
        print now() + " : Getting the token" 
        res = myecr.get_token()
        token = res['authorizationData'][0]
        # Imagepullsecrets are a base64 encoded docker config file 
        print now() + " : Got it making the secret" 
        secret = myecr.make_secret(token)
        b64secret = base64.b64encode(json.dumps(secret))
        # Let's create or refresh our credentials
        print now() + " : Done. Going to Kube API" 
        if kube.get_secret(params['KUBE_SECRET']) == None:
           kube.write_secret(params['KUBE_SECRET'], b64secret, "create")
           print ("%s : Creating secret %s for %s ") % (now(), params['KUBE_SECRET'],params['REGISTRY'])
        else:
           kube.write_secret(params['KUBE_SECRET'], b64secret, "update")
           print ("%s : Updating secret %s for %s ") % (now(), params['KUBE_SECRET'],params['REGISTRY'])
        time.sleep(int(params['INTERVAL']))

main()


