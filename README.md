
Use this if you have a Kubernetes cluster, not hosted on EC2 but with a need to pull images from an ECR registry.

The container will poll ECR/STS with credentials to get a token, then create/update the secret you can referenced in an imagepullsecret in your application POD specs. 

See under K8s dir for a sample replication controller with required env. 

Note:  For now this only creates a secret in the default namesspace. 
