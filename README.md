# portfolio-dashboard
My portfolio dashboard workflow using Notion, Tinkoff and Google sheets

Launch it in my swarm:

```
docker build -t my/portfolio-dashboard:1 .
docker service create --name portfolio --constraint node.role==manager my/portfolio-dashboard:1
docker service update --force portfolio # if needed
```
