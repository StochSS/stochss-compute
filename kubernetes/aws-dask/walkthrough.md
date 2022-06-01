Search in services bar for EKS.

Click Add cluster -> Create.

Read all the documentation links during the cluster creation process. They contain important info.

aws eks update-kubeconfig --region us-east-2 --name stochss-compute-dask

+++++++++++++++

eksctl utils associate-iam-oidc-provider --cluster stochss-compute-dask --approve

aws eks describe-cluster --name my-cluster | grep ipFamily

eksctl create iamserviceaccount \
    --name aws-node \
    --namespace kube-system \
    --cluster stochss-compute-dask \
    --role-name "SSSC-EKSVPCCNIRole" \
    --attach-policy-arn arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy \
    --override-existing-serviceaccounts \
    --approve