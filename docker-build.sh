docker build -t stochss/stochss-compute:$1 -f api.dockerfile .
docker build -t stochss/stochss-compute:examples -f examples.dockerfile .