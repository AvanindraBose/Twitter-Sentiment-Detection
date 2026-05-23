Store the ECS task definition JSON used by the CI deployment here:

```text
.github/ecs/twitter-sentiment-containers-revision8.json
```

The workflow replaces the image for the container named `fast-api` and deploys the
rendered task definition to the ECS service.
