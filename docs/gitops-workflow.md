# GitOps Workflow (config-only, not yet executed)

Same honesty pattern as the AutoGitOps Platform project: this section
describes how `argocd/application.yaml` is *supposed* to work, written
and reviewed carefully, but there is no Kubernetes cluster, no ArgoCD
installation, and no `kubectl`/`helm`/`argocd` CLI available in the
environment this project was built in. Nothing below has been run
against a real cluster.

## What the Application resource does

`argocd/application.yaml` points ArgoCD at this repo's
`deploy/helm/fleet-ota` path and tells it to render that Helm chart
with `values.yaml` into the `fleet-ota` namespace on the same cluster
ArgoCD itself runs on (`https://kubernetes.default.svc` -- the in-cluster
API server address, the normal case for a single-cluster GitOps setup).

`syncPolicy.automated` with `prune: true` and `selfHeal: true` means:
once this Application is created, ArgoCD watches the repo and applies
changes automatically (no manual `argocd app sync`), removes resources
that get deleted from the chart (`prune`), and reverts manual `kubectl
edit`-style changes made directly against the cluster back to match Git
(`selfHeal`) -- Git is the single source of truth, which is the entire
point of GitOps.

## How a release would actually reach the cluster (the intended flow)

1. A tag push (`v1.3.0`) triggers `.github/workflows/release.yml`,
   which builds, signs, and pushes `climate-control:1.3.0` (and, if the
   same workflow were extended to update-server, that image too) to
   GHCR.
2. A human (or a follow-up automation step not built in this project)
   updates `deploy/helm/fleet-ota/values.yaml` with the new tag and
   commits that change to `main`.
3. ArgoCD's automated sync picks up the `values.yaml` change and
   applies the rendered chart, rolling out the new image.

Step 2 is deliberately a manual, explicit commit rather than the
release workflow auto-committing a `values.yaml` bump back into `main`.
A workflow that pushes back into the branch it was triggered from is a
common way to get an infinite trigger loop or a confusing commit
history where "who changed this and why" gets harder to trace -- for a
portfolio project, an explicit human-reviewed commit is the more
defensible default, and a real team adopting auto-bumping later would
do it with a dedicated bot identity and a `[skip ci]`-style guard, not
as an afterthought.

## What's genuinely unverified here

Everything: whether the Helm chart renders into valid Kubernetes
manifests with real values substituted (only checked structurally by
stripping `{{ }}` expressions, see `deploy/helm/fleet-ota/README.md`),
whether the `Application` CRD fields are exactly right for whatever
ArgoCD version would run this, whether `selfHeal`/`prune` behave as
described against a live cluster. This is the same category of honesty
gap as the Terraform/EKS code in the AutoGitOps Platform project: this
config could be validated for real with a `kind` cluster (a free local
Kubernetes-in-Docker option, as that project's `local/` directory
demonstrates) -- not done here for this project, but the same path
exists if it's worth doing later.
