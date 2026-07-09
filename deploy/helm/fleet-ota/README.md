# fleet-ota Helm chart

Deploys `update-server` and `climate-control` into a namespace (default
`fleet-ota`). Written by hand (no `helm` binary available in the
environment this project was built in), and validated the only way
possible without one: each template's `{{ ... }}` expressions were
stripped and the remaining structure checked with `yaml.safe_load` to
confirm the surrounding YAML is well-formed. That's a real check, but
it isn't the same as `helm template . | kubectl apply --dry-run=client
-f -`, which is what would actually confirm rendered output is valid
Kubernetes YAML with real values substituted in -- that step is listed
as "not yet run" for the same reason all the AWS/Kubernetes-execution
steps in this project's docs are: honesty about what was verified
versus what was only reviewed.

## Values

See `values.yaml` for the full set. The two image repository/tag pairs
(`updateServer.image` / `climateControl.image`) point at the same GHCR
path the release workflow (`.github/workflows/release.yml`) pushes to.

## Install (not yet run)

```
helm install fleet-ota ./deploy/helm/fleet-ota --namespace fleet-ota --create-namespace
```
