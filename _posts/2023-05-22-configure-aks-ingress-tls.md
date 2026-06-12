---
layout: post
title: "Configure AKS Ingress with NGINX and TLS"
page_title: "AKS Ingress with NGINX and TLS: Configure cert-manager, the Ingress Class, Public IP, and DNS End to End"
date: 2023-05-22
categories: ["Technology"]
tags: ["Azure", "AKS", "Kubernetes", "Networking", "DevOps", "Cloud Computing"]
excerpt: "Set up AKS ingress with NGINX and TLS: install the controller, bind the ingress class, issue certificates with cert-manager, map DNS, and verify HTTPS works."
image: "/assets/images/blog/blog-42.webp"
reading_time: 63
author: "marcus-hall"
last_updated: 2023-05-22
lang: en
---
A working AKS ingress setup is the difference between a cluster that quietly serves production traffic over HTTPS and one that returns a default backend page, a certificate warning, or nothing at all. The phrase AKS ingress sounds like a single switch you flip, and that framing is exactly why so many setups break. Ingress on Azure Kubernetes Service is not one object. It is a chain of three independent pieces that must agree with each other: a controller that actually moves the packets, a class that tells that controller which rules it owns, and a certificate issuer that supplies the keys for TLS. When all three line up, external clients reach your services by hostname over an encrypted connection and the certificate renews itself without a human touching it. When any single link is missing or mismatched, the symptom you see rarely points at the link that failed, which is what turns a thirty-minute task into a two-day investigation.

This guide walks the entire chain end to end on AKS, with the working commands and manifests for each step and the specific failure each step prevents. The target is a setup you can reproduce, verify, and hand to a colleague, not a copied snippet that happens to work once on your laptop.

![Configuring AKS ingress with NGINX and TLS through cert-manager - Insight Crunch](/assets/images/blog/blog-42.webp)

## What correct ingress buys you, and what breaks when it is wrong

Before the commands, it helps to be precise about what a routing rule layer does for a cluster, because the value it delivers is the same value you lose when it is misconfigured. Without ingress, every service you want to expose needs its own public load balancer. On AKS that means a separate Azure Standard Load Balancer frontend and a separate public IP per service, each billed, each needing its own DNS record, each terminating TLS on its own with its own certificate plumbing. Ten public services become ten IPs, ten certificates, and ten places where a renewal can lapse. The model does not scale and it does not centralize the policy you care about, such as TLS versions, redirect behavior, request size limits, and path routing.

An ingress controller collapses that sprawl into one entry point. A single public IP fronts the cluster. One component terminates TLS for every hostname, routes by host and path to the right internal service, and applies shared policy in one place. The services behind it stay private, exposed only inside the cluster as ClusterIP services, which is both cheaper and safer. The certificate machinery lives in one controller and one issuer rather than scattered across every workload. That consolidation is the entire point, and it is why getting the setup right once pays off for every service you add afterward.

When the setup is wrong, the failures are familiar to anyone who has run Kubernetes in anger. A browser shows the NGINX default backend 404 because no rule matched the request, which usually means the ingress object exists but no controller is watching it. A client gets a certificate name mismatch or an untrusted-certificate warning because TLS terminated with a self-signed placeholder instead of a real issued certificate. The hostname resolves to nothing because DNS was never pointed at the load balancer address. The proxy pod sits in a pending state because the cluster could not schedule it, so the public IP never appears. Each of these is a broken link in the same chain, and each has a confirming command that tells you which link broke. The bulk of this guide is teaching you to read those signals quickly.

## The controller-class-certificate chain

The single most useful mental model for AKS ingress is this: ingress works only when the NGINX proxy, the ingress class, and the certificate issuer all agree, so a broken ingress is almost always one missing link in that chain rather than a deep platform fault. Hold that sentence in your head while you debug and you will stop chasing the wrong layer.

The controller is the running software that reads ingress objects from the Kubernetes API and turns them into actual proxy configuration. For this guide that controller is ingress-nginx, the community NGINX-based controller, which is the most widely deployed option and the one most tutorials and error messages assume. The controller is a deployment of pods plus a service of type LoadBalancer that gives it a public address. Nothing routes until this component is running and has an IP.

The ingress class is the binding contract between an ingress object and a controller. A cluster can run more than one controller, and without a class the controllers would fight over the same rules. The IngressClass resource names a controller, and each object names an IngressClass through its `ingressClassName` field. an ingress with no class, or a class that points at a controller you did not install, is a route that nothing serves. This is the link people forget most often, because older clusters relied on a now-deprecated annotation rather than the field, so copied manifests silently do the wrong thing.

The certificate issuer is the component that obtains and renews TLS certificates so the controller has something real to present. cert-manager fills this role. It watches for Certificate requests, talks to a certificate authority such as Let's Encrypt through the ACME protocol, proves you control the domain, stores the issued certificate in a Kubernetes secret, and renews it before expiry. Without cert-manager and a valid issuer, you can still configure a TLS block on your ingress, but there is no real certificate behind it, so clients get a warning or the handshake fails outright.

Every section that follows installs and verifies one link in that chain, in the order the links depend on each other. You install the proxy first because the class and the certificate flow both depend on it. You install cert-manager next because the issuer must exist before any certificate can be requested. You create the object last because it references both the class and the issued certificate. Reverse that order and you spend your time staring at objects that reference things which do not yet exist.

## Prerequisites and the correct order of operations

You need a running AKS cluster and administrative access to it. If you are still deciding how that cluster is shaped, the node pool and networking decisions matter for ingress, and the broader model of what the managed control plane owns versus what you own is worth understanding before you layer networking on top; the [deep dive on how Azure Kubernetes Service actually works](/2022/01/17/azure-kubernetes-service-aks-explained/) covers that boundary. For this setup you need four things in place.

First, `kubectl` configured against the cluster. Confirm it with a quick read of the nodes:

```bash
az aks get-credentials --resource-group rg-prod --name aks-prod --overwrite-existing
kubectl get nodes -o wide
```

If the nodes list and report `Ready`, your context is correct. If `kubectl` cannot reach the API server, fix that before anything else, because every step here is a Kubernetes API operation.

Second, Helm, because both ingress-nginx and cert-manager ship as Helm charts and installing them any other way means hand-maintaining manifests the chart authors update for you. Confirm the version:

```bash
helm version
```

Third, control over a DNS zone for the hostname you intend to serve. You do not need Azure DNS specifically; any zone where you can create an A record works. What you cannot skip is the ability to point a name at an IP, because both the ACME HTTP-01 challenge and ordinary client access depend on the hostname resolving to the proxy.

Fourth, a namespace strategy. Keep the NGINX proxy and cert-manager in their own namespaces, separate from application workloads, so that cluster-scoped infrastructure is easy to find, upgrade, and reason about. This guide uses `ingress-nginx` and `cert-manager` as namespaces, which match the chart defaults.

The order of operations is fixed by the dependency graph. Install the controller and wait for its public IP. Install cert-manager and confirm its pods and CRDs are healthy. Create a ClusterIssuer and confirm it reports ready. Map DNS to the proxy IP. Create the object with its TLS block. Watch the certificate issue. Verify HTTPS from outside the cluster. Skipping ahead is the most common self-inflicted wound, because a routing rule created before its controller exists generates events that look like controller faults when NGINX simply is not there yet.

## Step one: install the NGINX ingress controller

Add the chart repository and install the proxy into its own namespace. The install creates the NGINX proxy deployment, the IngressClass it owns, the RBAC it needs, and the LoadBalancer service that requests a public IP from Azure.

```bash
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update

helm install ingress-nginx ingress-nginx/ingress-nginx \
  --namespace ingress-nginx \
  --create-namespace \
  --set controller.service.externalTrafficPolicy=Local \
  --set controller.ingressClassResource.name=nginx \
  --set controller.ingressClassResource.default=false
```

A few of those flags deserve explanation because the defaults are not always what a production cluster wants. Setting `externalTrafficPolicy=Local` preserves the client source IP through the Azure load balancer instead of replacing it with a node IP, which matters for any policy, logging, or rate limiting that keys on the caller's address. The trade-off is that the load balancer health probe only succeeds on nodes actually running a proxy pod, so you want enough replicas to cover your nodes, but the source-IP preservation is usually worth it. Naming the IngressClass `nginx` explicitly rather than relying on the chart default makes your later objects readable and portable. Leaving `default=false` is deliberate: a default ingress class quietly adopts every ingress that omits a class, which is convenient until an unrelated object you did not mean to expose gets picked up. Be explicit instead.

Now watch the proxy acquire its address. This is the step where the chain first touches Azure infrastructure, because the LoadBalancer service triggers AKS to program the Standard Load Balancer and allocate a public IP.

```bash
kubectl get service -n ingress-nginx ingress-nginx-controller --watch
```

The `EXTERNAL-IP` column shows `<pending>` for a short while and then resolves to a public IPv4 address. That address is the front door for the whole cluster. The path it takes through Azure, from the LoadBalancer service to the Standard Load Balancer frontend to the public IP resource, is the same outbound and inbound plumbing covered in the [Azure networking fundamentals guide](/2023/08/28/azure-networking-fundamentals/), and understanding it helps when the IP refuses to appear.

If `EXTERNAL-IP` stays pending for more than a couple of minutes, the proxy is telling you something. The two usual causes are a proxy pod that cannot schedule, which leaves nothing for the load balancer to point at, and a subscription or region issue allocating the public IP. Check the pod first:

```bash
kubectl get pods -n ingress-nginx
kubectl describe pod -n ingress-nginx -l app.kubernetes.io/component=controller
```

A pod stuck in `Pending` with `FailedScheduling` events is a node capacity or placement problem, not a routing rule problem, and the triage for that is exactly the same as for any unschedulable workload; the [guide to fixing AKS pods stuck in pending](/2022/07/25/fix-aks-pods-pending/) walks the resource, taint, and capacity causes in order. Resolve scheduling first, because the IP will never appear while the proxy has no running pod to back the service.

### How does the NGINX proxy get a public IP?

The proxy's LoadBalancer service makes AKS provision a frontend on the cluster's Azure Standard Load Balancer and attach a public IP to it, then program rules that forward inbound traffic to the NGINX proxy pods. The IP belongs to the service, so deleting the service releases it unless you pinned a static address.

That dynamic-by-default behavior is fine for a first setup and wrong for anything you will put DNS in front of, because a dynamic IP can change if the service is recreated, and your A record would then point at nothing. For production, allocate a static public IP in the node resource group and pin the service to it. AKS places load balancer IPs in the node (managed) resource group, named like `MC_<resourcegroup>_<clustername>_<region>`, so create the IP there:

```bash
NODE_RG=$(az aks show --resource-group rg-prod --name aks-prod --query nodeResourceGroup -o tsv)

az network public-ip create \
  --resource-group "$NODE_RG" \
  --name pip-ingress-prod \
  --sku Standard \
  --allocation-method Static

PIP=$(az network public-ip show --resource-group "$NODE_RG" --name pip-ingress-prod --query ipAddress -o tsv)
echo "$PIP"
```

Then point the proxy at it through the chart, which writes the right service annotation and the `loadBalancerIP` field:

```bash
helm upgrade ingress-nginx ingress-nginx/ingress-nginx \
  --namespace ingress-nginx \
  --reuse-values \
  --set controller.service.loadBalancerIP="$PIP" \
  --set controller.service.annotations."service\.beta\.kubernetes\.io/azure-load-balancer-resource-group"="$NODE_RG"
```

The annotation tells AKS to look for the pre-created IP in the node resource group rather than allocating a fresh one, and the `loadBalancerIP` value binds the service to that exact address. Now your front door has a stable address you can safely put in DNS. Note that newer chart and Kubernetes versions are moving from the `loadBalancerIP` field toward annotation-only configuration, so check which your chart version expects rather than assuming; treat the exact field name as a value to verify against the chart version you installed.

## Step two: understand the ingress class before you create rules

The IngressClass is the quietest link in the chain and the one that produces the most baffling symptom, an object that exists, looks correct, and serves nothing. It is worth a section of its own.

### What is an ingress class and why does it matter?

An IngressClass is a cluster-scoped resource that names a controller; an object names an IngressClass through its `ingressClassName` field, and a controller only acts on objects whose class points at it. The class is the routing of routing: it decides which controller owns which rules.

The chart you installed created an IngressClass named `nginx` whose controller value identifies the ingress-nginx controller. Confirm it exists and read its controller string:

```bash
kubectl get ingressclass
kubectl get ingressclass nginx -o jsonpath='{.spec.controller}{"\n"}'
```

The controller string will read something like `k8s.io/ingress-nginx`. That string is matched against the `--controller-class` the proxy process runs with. When a routing rule names `ingressClassName: nginx`, Kubernetes looks up that IngressClass, reads its controller value, and the ingress-nginx controller, which watches for exactly that controller value, picks up the rule. If those values do not match, nothing happens and nothing errors loudly, which is precisely why this link is so easy to miss.

Two historical traps live here. The first is the old annotation `kubernetes.io/ingress.class: nginx`, which predates the IngressClass resource. It still works in many controller versions for backward compatibility, but it is deprecated, and mixing the annotation with the field leads to confusing precedence. Use the `ingressClassName` field and drop the annotation entirely on new objects. The second trap is the default class. If exactly one IngressClass is marked default with the annotation `ingressclass.kubernetes.io/is-default-class: "true"`, then objects that omit a class get adopted by it. That can be a convenience or a surprise depending on whether you meant it. Because this guide left the class non-default on purpose, every ingress must name its class explicitly, which removes the ambiguity.

## Step three: install cert-manager and an issuer

With routing in place, the next link is TLS. cert-manager is the NGINX proxy that automates obtaining and renewing certificates, and it installs as its own Helm chart with a set of custom resource definitions that introduce the Certificate, Issuer, ClusterIssuer, CertificateRequest, Order, and Challenge resources.

```bash
helm repo add jetstack https://charts.jetstack.io
helm repo update

helm install cert-manager jetstack/cert-manager \
  --namespace cert-manager \
  --create-namespace \
  --set installCRDs=true
```

The `installCRDs=true` flag installs the custom resource definitions alongside the proxy so you do not have to apply them separately. Some teams prefer to manage CRDs out of band so that a chart uninstall does not remove them and orphan certificates; if that is your model, apply the CRDs first and leave the flag off. Either way, confirm the three cert-manager pods come up healthy:

```bash
kubectl get pods -n cert-manager
```

You should see the `cert-manager`, `cert-manager-webhook`, and `cert-manager-cainjector` pods running. The webhook is the one to watch, because cert-manager will reject Certificate and Issuer objects until the webhook is ready, and a common early error is an issuer creation that fails with a webhook connection refused message simply because the webhook pod had not finished starting. Give it a moment and retry rather than assuming the manifest is wrong.

### How does cert-manager issue and renew certificates?

cert-manager watches for Certificate resources, and for each one it creates a CertificateRequest, drives an ACME Order with the certificate authority, completes a Challenge that proves domain control, then writes the issued certificate and key into a Kubernetes secret and schedules a renewal well before expiry. The renewal is automatic, which is the entire reason to use it.

The certificate authority for most public setups is Let's Encrypt, which issues free, short-lived certificates through the ACME protocol. Short-lived is the point: a certificate that expires in weeks rather than years forces automation, and cert-manager provides that automation. To use it you create an Issuer or a ClusterIssuer. The difference is scope. An Issuer is namespaced and only serves Certificate requests in its own namespace; a ClusterIssuer is cluster-wide and can serve requests from any namespace. For a shared ingress that fronts services in several namespaces, a ClusterIssuer is usually the right choice.

Create a ClusterIssuer for the Let's Encrypt staging environment first. Staging exists specifically so you can shake out configuration errors without burning against the production rate limits, which are real and easy to hit while you iterate. The staging certificate will not be trusted by browsers, but it proves the whole issuance flow works.

```yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-staging
spec:
  acme:
    server: https://acme-staging-v02.api.letsencrypt.org/directory
    email: platform@example.com
    privateKeySecretRef:
      name: letsencrypt-staging-account-key
    solvers:
      - http01:
          ingress:
            class: nginx
```

Apply it and confirm it reports ready:

```bash
kubectl apply -f clusterissuer-staging.yaml
kubectl get clusterissuer letsencrypt-staging -o wide
```

The `solvers` block is where the routing chain reconnects to the certificate chain. The HTTP-01 solver tells cert-manager to prove domain control by serving a token at a well-known path over HTTP, and it does that by creating a temporary ingress using the `nginx` class. That is why the proxy and class had to exist first: the challenge itself rides through the same controller you installed. If the class name here does not match your real IngressClass, the challenge ingress is created but nothing serves it, the token is never reachable, and issuance hangs. The single most common cert-manager failure on AKS is exactly this mismatch or a DNS name that does not yet resolve to the NGINX proxy, both of which leave the Challenge stuck.

Once staging issues cleanly, create the production issuer by pointing at the production ACME endpoint:

```yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: platform@example.com
    privateKeySecretRef:
      name: letsencrypt-prod-account-key
    solvers:
      - http01:
          ingress:
            class: nginx
```

```bash
kubectl apply -f clusterissuer-prod.yaml
```

The only difference is the server URL and the account key secret name. Keep both issuers in the cluster so you can fall back to staging while testing changes and switch the production ingress over only when you are confident.

## Step four: map DNS to the proxy IP

A certificate for a hostname can only be issued if the certificate authority can reach a challenge at that hostname, and clients can only reach your services if the name resolves to the NGINX proxy. Both depend on one A record: the hostname pointed at the proxy's public IP.

If your zone lives in Azure DNS, create the record against the zone:

```bash
az network dns record-set a add-record \
  --resource-group rg-dns \
  --zone-name example.com \
  --record-set-name app \
  --ipv4-address "$PIP"
```

That publishes `app.example.com` pointing at the proxy IP. Confirm propagation before you go further, because the HTTP-01 challenge will fail if the name does not yet resolve:

```bash
dig +short app.example.com
nslookup app.example.com
```

The answer must be the proxy's public IP. DNS caching means a freshly created record can take time to appear depending on the zone's TTL and your resolver, so wait for the lookup to return the right address rather than racing ahead and then blaming cert-manager when the real cause is an unresolved name.

### How do I map a hostname to the AKS ingress?

Create a DNS A record for the hostname pointing at the NGINX proxy's public IP, the same address shown in the `EXTERNAL-IP` column of the proxy's LoadBalancer service. Use a static public IP so the address does not change, then verify the name resolves to it before requesting a certificate.

For clusters with many hostnames that churn, the external-dns project can watch objects and create the DNS records for you against Azure DNS automatically, which removes the manual record step and keeps DNS in sync with what the cluster actually serves. It is optional, and adding it before the manual flow works once tends to hide which layer is failing, so get one hostname working by hand first and adopt automation afterward.

## Step five: create the routing layer with a TLS block

Now every dependency exists: a controller with an IP, a class that binds rules to it, an issuer that can produce certificates, and a hostname that resolves. The object ties them together. Assume a simple internal service named `web` listening on port 80 in the `apps` namespace.

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: web
  namespace: apps
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  ingressClassName: nginx
  tls:
    - hosts:
        - app.example.com
      secretName: web-tls
  rules:
    - host: app.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: web
                port:
                  number: 80
```

Three fields carry the whole chain. The `ingressClassName: nginx` binds this rule to the proxy you installed. The `cert-manager.io/cluster-issuer: letsencrypt-prod` annotation tells cert-manager to issue a certificate for the hosts in the TLS block using your production issuer. The `tls` section names the secret where the issued certificate and key will be stored, `web-tls`, and lists the hostname the certificate covers. cert-manager sees the annotation, notices there is no valid `web-tls` secret yet, and starts the issuance flow automatically. You do not create the secret by hand; cert-manager owns it.

Apply the routing layer and watch the machinery turn:

```bash
kubectl apply -f ingress-web.yaml
kubectl get ingress -n apps web
kubectl get certificate -n apps
kubectl get certificaterequest,order,challenge -n apps
```

The Certificate begins `False` under `READY` and flips to `True` once the challenge completes and the certificate is stored. Following the chain of objects from Certificate to CertificateRequest to Order to Challenge is how you watch issuance progress and find exactly where it stalls if it does. A Challenge that lingers in `pending` is the signal to check the two usual suspects: the challenge ingress reaching the proxy, and the hostname resolving to that proxy's IP.

### How do I configure TLS on AKS ingress?

Add a `tls` block to the routing layer that lists the hostname and names a secret, then add the `cert-manager.io/cluster-issuer` annotation pointing at a ready issuer. cert-manager issues the certificate for that hostname, stores it in the named secret, and the NGINX controller loads it to terminate TLS, after which it renews automatically.

## Step six: verify the setup from outside the cluster

Verification has two halves. Inside the cluster you confirm cert-manager finished its work, and outside the cluster you confirm a real client gets a trusted HTTPS response. Do both, because each catches failures the other misses.

Inside, confirm the certificate is ready and read why if it is not:

```bash
kubectl describe certificate -n apps web-tls
kubectl get secret -n apps web-tls
```

A ready certificate writes a TLS secret of type `kubernetes.io/tls` containing `tls.crt` and `tls.key`. The `describe` output narrates the issuance, and a failure here names the cause directly, whether it is a challenge that failed, a rate limit, or an issuer that is not ready.

Outside, confirm the handshake and the served content with curl, which shows the certificate chain and the response together:

```bash
curl -v https://app.example.com
```

Read the TLS handshake lines. The server certificate's subject should be your hostname and the issuer should be Let's Encrypt rather than the proxy's self-signed fake certificate, which is the placeholder NGINX serves when no real certificate is loaded. Seeing that placeholder, often issued to `Kubernetes Ingress Controller Fake Certificate`, is the unambiguous sign that the TLS secret was never produced or never loaded, and it sends you straight back to the certificate status rather than the network.

For a closer look at the chain, including the full certificate and the negotiated protocol, use openssl:

```bash
echo | openssl s_client -connect app.example.com:443 -servername app.example.com 2>/dev/null | openssl x509 -noout -issuer -subject -dates
```

That prints the issuer, the subject, and the validity window, which confirms both that the certificate is real and that it has a sane expiry that cert-manager will renew before. If you can curl the hostname over HTTPS, see a Let's Encrypt issuer, and reach your service's content, the chain is complete and verified.

The fastest way to build the muscle memory for this whole sequence is to run it against a throwaway cluster a few times, breaking one link deliberately each time and watching which command surfaces the failure. The [hands-on Azure labs and command library on VaultBook](https://vaultbook.org/tools/azure-labs.html) include a routing rule and TLS sandbox where you can install the proxy, issue a certificate, and reach a service over HTTPS against a real cluster, then tear it down, which is a far cheaper way to learn the failure signatures than discovering them in production.

## The InsightCrunch AKS ingress setup checklist

The findable artifact for this guide is a single checklist that captures every link in the chain, the command that proves the link is healthy, and the specific gotcha that bites at that step. Treat it as the thing you run top to bottom when an ingress misbehaves, because the failure almost always sits at the first row whose verification command does not return what it should.

| Step | What you do | Verify with | The gotcha |
|------|-------------|-------------|------------|
| Controller | Install ingress-nginx via Helm | `kubectl get pods -n ingress-nginx` shows running controller | Pod pending means nothing routes; fix scheduling first |
| Public IP | LoadBalancer service gets an address | `kubectl get svc -n ingress-nginx` shows an EXTERNAL-IP | Dynamic IP can change; pin a static IP in the node resource group |
| Ingress class | IngressClass exists and is named | `kubectl get ingressclass` shows `nginx` | Object with no class, or wrong class, serves nothing silently |
| cert-manager | Install via Helm with CRDs | `kubectl get pods -n cert-manager` all running | Webhook not ready rejects issuers; wait and retry |
| Issuer | Create a ClusterIssuer | `kubectl get clusterissuer` shows `Ready True` | Solver class must match the real IngressClass exactly |
| DNS | A record points host at the IP | `dig +short host` returns the NGINX proxy IP | Unresolved name stalls both the challenge and clients |
| Ingress | Create ingress with TLS block | `kubectl get certificate -n apps` shows `Ready True` | Missing annotation or class leaves no certificate issued |
| Verify | curl the host over HTTPS | `curl -v https://host` shows a Let's Encrypt issuer | The fake certificate means TLS terminated with no real cert |

The discipline this checklist enforces is to verify each link before moving to the next, rather than building the whole stack and then debugging a symptom three layers away from its cause. An engineer who internalizes the controller-class-certificate chain reads this table as a dependency order, not a menu.

## The settings the defaults get wrong

A controller that installs and serves traffic is not the same as a controller configured for production. Several defaults are reasonable for a demo and wrong for a real workload, and the symptoms they cause are easy to misattribute.

The request body size limit is the classic example. ingress-nginx caps the proxied request body at a modest default, and any upload larger than that returns a 413 Request Entity Too Large that looks like an application bug until you realize the proxy rejected the request before the app ever saw it. Raise it deliberately with an annotation on the routing layer, sized to your real upload needs:

```yaml
metadata:
  annotations:
    nginx.ingress.kubernetes.io/proxy-body-size: "50m"
```

Read and write timeouts are the next surprise. The default proxy read timeout is fine for snappy APIs and too short for long-running requests, streaming responses, or slow upstreams, where it surfaces as a 504 Gateway Timeout that the application logs never explain because the app was still working when the proxy gave up. Tune the timeout to match the slowest legitimate request:

```yaml
metadata:
  annotations:
    nginx.ingress.kubernetes.io/proxy-read-timeout: "120"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "120"
```

HTTP-to-HTTPS redirect behavior catches teams that expected it and teams that did not. By default, once a routing rule has a TLS block, the proxy redirects plain HTTP to HTTPS, which is usually what you want. But the same redirect can break the ACME HTTP-01 challenge if it is applied too aggressively, because the challenge is served over plain HTTP at a well-known path. Modern controllers special-case the ACME path, but if you have layered your own force-redirect annotation, confirm it does not swallow the challenge. The relevant knobs are `nginx.ingress.kubernetes.io/ssl-redirect` and `force-ssl-redirect`, and the safe posture is to let the NGINX proxy manage the redirect rather than forcing it everywhere.

Client source IP preservation, set earlier with `externalTrafficPolicy=Local`, interacts with how NGINX reads forwarded headers. If you sit another proxy or Azure service in front of the controller, you may need `use-forwarded-headers` enabled so NGINX trusts the `X-Forwarded-For` chain, and you must be careful about trusting those headers only from sources you control, because a blindly trusted forwarded header is a spoofing vector. The correct setting depends on your topology, which is exactly why it is not a safe default.

None of these are obscure. They are the handful of settings that separate an ingress that passed a smoke test from one that survives real traffic, and every one of them produces a symptom that points away from the proxy unless you know to look there.

## The six failures engineers actually report

The brief for this setup names six recurring patterns, and each maps to a single broken link in the chain. Reading them as a set is the fastest way to build the diagnostic instinct, because once you can name the pattern you already know the fix.

### Why does my ingress serve nothing even though it exists?

The most common pattern is a route with no matching ingress class. The object is present, `kubectl get ingress` lists it, and yet requests hit the default backend 404 or time out. Nothing is wrong with the rules; the problem is that no controller claimed them.

Confirm it by reading the ingress class on the object and comparing it to the installed classes:

```bash
kubectl get ingress -n apps web -o jsonpath='{.spec.ingressClassName}{"\n"}'
kubectl get ingressclass
```

If the object has an empty class, or names a class that does not exist, the proxy never adopts it. The fix is to set `ingressClassName: nginx` to match the real class, and to delete any stale `kubernetes.io/ingress.class` annotation that might be competing with the field. After the edit, the NGINX proxy picks up the rule within seconds and the default backend 404 turns into your service's response.

### Why is cert-manager failing the ACME challenge?

The second pattern is a Challenge stuck in `pending` because cert-manager cannot complete the HTTP-01 proof. This is almost never a cert-manager bug; it is the challenge token failing to be reachable, which means either DNS does not yet resolve to the controller or the challenge ingress is not being served because of a class mismatch.

Walk the chain of issuance objects to see where it stalls:

```bash
kubectl get challenge -n apps
kubectl describe challenge -n apps
kubectl get ingress -n apps
```

The `describe` output names the reason, often a self-check failure that says the token at the well-known path could not be fetched. Confirm the hostname resolves to the proxy IP and that the temporary challenge ingress carries the right class. The fix is whichever link is broken: publish or correct the DNS record, or align the solver's ingress class with your real IngressClass. Once the token is reachable, the challenge completes and the certificate issues without further intervention.

### Why is the NGINX proxy stuck waiting for a public IP?

The third pattern is a LoadBalancer service whose `EXTERNAL-IP` never leaves `<pending>`. Because no IP means no front door, this blocks everything downstream, so it is worth ruling out early.

The usual root cause is a proxy pod that cannot schedule, which leaves the service with no healthy endpoints to point at:

```bash
kubectl get pods -n ingress-nginx
kubectl describe svc -n ingress-nginx ingress-nginx-controller
```

If the pod is pending, treat it as a scheduling problem and resolve capacity, taints, or resource requests before looking at networking. If the pod is running but the IP still will not appear, the issue is on the Azure side, often a static IP that does not exist in the node resource group, a permissions gap on the cluster identity, or a regional allocation delay. Confirm the pre-created IP exists and that the service annotation names the correct node resource group. The IP appears once the service has a healthy pod and a valid allocation target.

### Why does the hostname not reach my service?

The fourth pattern is a hostname that resolves to the wrong place or to nothing, so clients never reach the proxy even though everything inside the cluster is healthy. This is purely a DNS link, but it presents as a routing rule failure because the user sees a connection error.

```bash
dig +short app.example.com
kubectl get svc -n ingress-nginx ingress-nginx-controller -o jsonpath='{.status.loadBalancer.ingress[0].ip}{"\n"}'
```

Compare the two outputs. They must be identical. If the A record points at an old IP from before you pinned a static address, or at nothing because the record was never created, that is the fault. The fix is to update the A record to the proxy's current public IP and wait for the TTL to expire so resolvers pick up the change. Until the lookup returns the NGINX proxy IP, no amount of cluster-side debugging will help.

### Why did my certificate stop renewing?

The fifth pattern is a certificate that issued fine originally and then failed to renew, surfacing weeks or months later as an expiry warning. cert-manager renews automatically, so a failed renewal means a dependency that was present at first issuance has since changed.

```bash
kubectl get certificate -A
kubectl describe certificate -n apps web-tls
kubectl get challenge -A
```

Look for a Certificate whose renewal triggered a new Challenge that is now failing. The usual culprits are a DNS record that changed, an issuer that was modified or deleted, or a rate limit hit because something was requesting certificates in a loop. Because renewal uses the same HTTP-01 path as first issuance, anything that would break a fresh challenge breaks renewal too. The fix follows the failing challenge's reason: restore the DNS record, recreate the issuer, or back off the loop that exhausted the rate limit. Watching the certificate expiry proactively, rather than waiting for a browser warning, turns this from an outage into a non-event.

### Why are two controllers fighting over my ingress?

The sixth pattern appears in clusters that, by accident or design, run more than one NGINX proxy. If two controllers both claim the same ingress, you get inconsistent behavior, duplicated rules, or traffic served by the wrong controller with the wrong configuration.

```bash
kubectl get ingressclass
kubectl get pods -A -l app.kubernetes.io/name=ingress-nginx
```

Multiple IngressClass objects, or a second controller installed in another namespace, are the tell. The clean resolution is to give each controller a distinct IngressClass and to make sure every ingress names exactly the class it intends, never relying on a default that two controllers might both interpret. If you only meant to run one controller, remove the duplicate. The ambiguity disappears the moment every rule names a single, unambiguous class.

## Making the configuration repeatable as code

A setup you clicked together by hand is a setup you will rebuild by hand the next time, and the next person will rebuild it differently. The whole chain belongs in version control so the cluster's ingress posture is reproducible, reviewable, and recoverable. There are three layers to capture.

The controller and cert-manager installations are Helm releases, so pin their chart versions and values in a values file rather than passing `--set` flags interactively. A committed `values.yaml` for ingress-nginx records the static IP, the external traffic policy, the replica count, and any tuned defaults, and a committed cert-manager values file records the CRD policy. Installing from pinned versions means a rebuilt cluster gets the same controller behavior, not whatever the chart's latest happened to be that day.

```yaml
# ingress-nginx-values.yaml
controller:
  replicaCount: 2
  service:
    externalTrafficPolicy: Local
    loadBalancerIP: "REPLACE_WITH_STATIC_IP"
    annotations:
      service.beta.kubernetes.io/azure-load-balancer-resource-group: "REPLACE_WITH_NODE_RG"
  ingressClassResource:
    name: nginx
    default: false
  config:
    proxy-body-size: "50m"
    proxy-read-timeout: "120"
```

```bash
helm upgrade --install ingress-nginx ingress-nginx/ingress-nginx \
  --namespace ingress-nginx --create-namespace \
  --version <pinned-chart-version> \
  -f ingress-nginx-values.yaml
```

The issuers and objects are plain Kubernetes manifests, so they live in the same repository and apply through whatever delivery mechanism you use, whether that is a pipeline that runs `kubectl apply` against the cluster or a GitOps controller that reconciles the repository continuously. The static public IP, because it is an Azure resource rather than a Kubernetes object, belongs in your infrastructure-as-code alongside the cluster itself, declared in Bicep or Terraform so it is created in the node resource group with the cluster rather than as a manual afterthought that someone forgets on the next rebuild.

Treating the IP as code matters more than it looks, because the IP is the one piece of the chain that is genuinely external to Kubernetes and therefore the one most likely to drift. A pinned static IP declared in the same template that builds the cluster, referenced by the Helm values that configure the proxy, keeps DNS stable across cluster rebuilds. When you can destroy and recreate the cluster and have the same hostname serving the same content over the same certificate without touching DNS, the configuration has earned the word repeatable.

Hardening the NGINX proxy belongs in this repeatable layer too, not as a later bolt-on. The exposure an NGINX proxy represents, a single public front door into the cluster, makes it a natural place to apply network policy, restrict who can create objects, and limit the annotations untrusted namespaces may set; the [guide to securing AKS clusters](/2024/02/12/securing-aks-clusters-guide/) treats the NGINX proxy as one of the surfaces that deserves deliberate lockdown rather than default trust. If you want structured practice diagnosing the failure modes above against realistic broken clusters, the scenario-based [troubleshooting drills on ReportMedic](https://reportmedic.org/tools/azure-troubleshooting-drills.html) rehearse the same controller, class, and certificate signatures until reading them becomes automatic.

## Private ingress and the internal load balancer variation

Not every ingress should face the public internet. For services that only internal clients or peered networks should reach, the controller can sit behind an Azure internal load balancer instead of a public one, which gives it a private IP inside your virtual network rather than a public address. The chain is identical except for one annotation on the proxy service and the corresponding DNS choice.

```yaml
controller:
  service:
    annotations:
      service.beta.kubernetes.io/azure-load-balancer-internal: "true"
```

With that annotation, AKS provisions an internal load balancer frontend and the proxy's `EXTERNAL-IP` becomes a private address from the subnet. The DNS record then points at that private IP through a private DNS zone, and clients reach the routing layer only from within the network. The TLS chain is unchanged in shape, though an internal-only hostname cannot complete a public HTTP-01 challenge because Let's Encrypt cannot reach it from the internet, so internal ingresses typically use the DNS-01 challenge, which proves control by writing a TXT record rather than serving an HTTP token, or an internal certificate authority entirely. The choice between HTTP-01 and DNS-01 comes down to reachability: HTTP-01 needs the hostname publicly reachable over HTTP, DNS-01 needs control of the DNS zone, and internal ingresses almost always take the DNS-01 path for that reason.

Running a public ingress for external services and an internal ingress for private ones is a common and clean topology, and it is the case where distinct IngressClass names earn their keep. Give the public controller the class `nginx` and the internal controller a class like `nginx-internal`, and every ingress names the class that matches its intended exposure. The class becomes the explicit declaration of whether a service is meant to be reachable from the internet, which is a property worth making impossible to get wrong by accident.

## How path routing decides which service answers

A single hostname rarely maps to a single service. A production front door routes `/api` to one workload, `/` to another, and perhaps `/static` to a third, all under the same name and the same certificate. Path routing is how the ingress object expresses that, and getting the matching semantics right is the difference between requests landing where you intend and a confusing mix of 404s and wrong responses.

Each path in an ingress rule carries a `pathType`, and the three values behave differently enough that mixing them up is a real source of bugs. A `Prefix` path matches the request path by URL path segments, so `/api` matches `/api`, `/api/`, and `/api/users` but not `/apifoo`, because the match respects segment boundaries. An `Exact` path matches only the precise path with no trailing variation, so `/api` matches `/api` and nothing else. The third value, `ImplementationSpecific`, hands interpretation to the NGINX proxy, which for ingress-nginx means the path is treated as an NGINX location and can use regular expressions when you enable them. Most rules want `Prefix`, and reaching for `ImplementationSpecific` should be a deliberate choice tied to a regex you actually need, not a default you copied.

```yaml
spec:
  ingressClassName: nginx
  rules:
    - host: app.example.com
      http:
        paths:
          - path: /api
            pathType: Prefix
            backend:
              service:
                name: api
                port:
                  number: 8080
          - path: /
            pathType: Prefix
            backend:
              service:
                name: web
                port:
                  number: 80
```

Ordering and specificity matter when paths overlap. With the rule above, a request to `/api/orders` matches the `/api` prefix and goes to the api service, while everything else falls through to the `/` prefix and reaches the web service. The controller resolves the most specific matching prefix, so the catch-all `/` does not swallow `/api` traffic even though it would match it in isolation. When you introduce regular expression paths through `ImplementationSpecific`, you also take on responsibility for ordering them yourself, because regex locations are evaluated in the order the proxy assembles them, and a broad pattern placed before a narrow one will shadow it.

### Which pathType should I use for an ingress rule?

Use `Prefix` for almost everything, because it matches on whole path segments the way engineers expect and routes a base path plus everything beneath it to one service. Reserve `Exact` for a single endpoint that must not match anything below it, and use `ImplementationSpecific` only when you genuinely need a regular expression and have enabled regex support deliberately.

Two annotations frequently accompany path routing and deserve a clear-eyed look. The rewrite-target annotation, `nginx.ingress.kubernetes.io/rewrite-target`, rewrites the path before it reaches the backend, which lets you strip a prefix so a service mounted at `/api` receives requests at `/` as if it owned the root. It is powerful and easy to misuse, because a rewrite combined with a regex capture group can mangle paths in ways that only show up for certain URLs. Test it against the exact paths your clients use rather than assuming a simple rewrite behaves uniformly. The use-regex annotation, `nginx.ingress.kubernetes.io/use-regex`, switches a path to regular expression matching, and once enabled the path is no longer a plain prefix, so a value like `/api` that you intended as a literal prefix now behaves as a pattern. Enabling regex on a path you wrote as a literal is a quiet way to change matching behavior without meaning to.

Host matching layers on top of path matching. The controller first selects rules whose `host` matches the request's Host header, then evaluates paths within those rules. A rule with no host acts as a catch-all for any hostname, which is occasionally what you want for a default backend and frequently a surprise when an unhosted rule absorbs traffic meant for a hosted one. Wildcard hosts, written as `*.example.com`, match a single label, so they cover `a.example.com` but not `a.b.example.com` and not the bare `example.com`. Knowing those boundaries keeps you from writing a wildcard rule that you think is broader than it is. When routing misbehaves, the question to ask in order is always the same: did the request reach the NGINX proxy at all, did its Host header match a rule, and did its path match a path within that rule. Each of those is a separate failure with a separate fix, and conflating them is what turns path debugging into guesswork.

## Reading the controller when something is wrong

Most ingress debugging is really reading what the proxy already knows. The NGINX controller is unusually transparent about its state if you know which three signals to pull, and learning them turns vague reports of "the site is down" into a precise diagnosis in minutes.

The first signal is NGINX's own logs. Every request the proxy proxies, and every configuration reload it performs, is logged, and the reload lines in particular tell you whether the NGINX proxy accepted your latest ingress change or rejected it.

```bash
kubectl logs -n ingress-nginx -l app.kubernetes.io/component=controller --tail=100
kubectl logs -n ingress-nginx -l app.kubernetes.io/component=controller -f
```

A healthy controller logs a successful configuration reload shortly after you apply a routing rule, and access log lines show the upstream each request was sent to along with the response code. If a request is returning a 502, the access log shows which upstream the proxy tried and failed to reach, which immediately separates a controller problem from a backend problem: a 502 with a named upstream means the NGINX proxy routed correctly but the backend pod refused or reset the connection, pointing you at the workload rather than the routing layer.

The second signal is the rendered configuration itself. The controller compiles all your ingress objects into one NGINX configuration, and you can dump exactly what it produced. This is the ground truth that settles arguments about whether an ingress took effect:

```bash
kubectl exec -n ingress-nginx deploy/ingress-nginx-controller -- /nginx-ingress-controller --version
kubectl exec -n ingress-nginx deploy/ingress-nginx-controller -- cat /etc/nginx/nginx.conf | grep -A 20 "server_name app.example.com"
```

If your hostname and its routes do not appear in the rendered configuration, the proxy never adopted your ingress, and you are back to the class binding. If they appear but point at an upstream you did not expect, the rule itself is wrong. Reading the compiled configuration removes the guesswork about whether the NGINX proxy saw your change, because the rendered server block either contains your routes or it does not.

### How do I see why the NGINX proxy rejected my ingress object?

The controller runs a validating admission webhook that checks every ingress object as you create it, and a rejected object shows the reason in the error returned by `kubectl apply`. If the apply succeeded but the rule does nothing, exec into the controller and grep the rendered `nginx.conf` for your hostname, then read the proxy logs for reload errors that name the offending annotation or path.

The third signal is the admission webhook, which is the piece newcomers do not expect. ingress-nginx installs a validating webhook that inspects each ingress before it is admitted, catching syntactically valid but semantically broken rules, such as a regex that will not compile or an annotation with an invalid value, before they reach the live configuration. The benefit is that a bad ingress is rejected at apply time with a clear message rather than silently breaking the running configuration. The occasional cost is that if the webhook itself is unhealthy, perhaps during a controller restart, ingress applies can fail with a webhook connection error that has nothing to do with the routing layer you are applying. When an apply fails with a webhook error, check NGINX's health before assuming your manifest is wrong, the same way a cert-manager webhook hiccup can briefly reject issuers. For deeper operational visibility, the proxy exposes a metrics endpoint that surfaces request rates, latencies, and reload counts, which you can scrape with Prometheus to alert on reload failures and rising error rates rather than waiting for a user to notice. Wiring those metrics in early means the NGINX proxy tells you it is unhappy before the symptoms reach a person.

## Upgrading the controller and cert-manager without an outage

the front door chain is long-lived infrastructure, and the two pieces most likely to need upgrading are the proxy and cert-manager. Both are upgraded as Helm releases, and both have version considerations that, if ignored, turn a routine upgrade into an outage. The discipline is not complicated, but it is specific.

For NGINX, the cardinal rule is to pin the chart version and upgrade deliberately rather than letting an unpinned `helm upgrade` pull whatever is latest. Read the release notes for the version you are moving to, because the proxy occasionally changes annotation behavior, default values, or the minimum Kubernetes version it supports, and a major version jump can change how an annotation you depend on is interpreted. Upgrade in a non-production cluster first, confirm your real ingress objects still render and serve correctly, then promote the same pinned version to production.

```bash
helm repo update
helm upgrade ingress-nginx ingress-nginx/ingress-nginx \
  --namespace ingress-nginx \
  --version <target-chart-version> \
  -f ingress-nginx-values.yaml
```

The upgrade rolls the proxy pods, and because the NGINX proxy is the data path for live traffic, you want that roll to be graceful. Running more than one replica means the rolling update keeps at least one controller serving while another restarts, so traffic does not drop. A PodDisruptionBudget protects against an upgrade or a node drain taking all replicas down at once, which is the kind of self-inflicted outage that pinning versions does nothing to prevent. The combination of multiple replicas spread across nodes and a disruption budget is what makes a controller upgrade a non-event rather than a brief outage.

### How do I upgrade cert-manager safely?

Upgrade cert-manager one minor version at a time, applying the matching custom resource definitions for the target version before or alongside the Helm upgrade, because cert-manager's CRDs and controller must agree. Check the release notes for breaking changes, upgrade in a test cluster first, and confirm existing Certificates stay ready after the upgrade rather than assuming they survived untouched.

cert-manager has one extra wrinkle the controller does not: its custom resource definitions are versioned alongside the proxy, and NGINX expects CRDs that match its version. If you installed CRDs through the chart with the install flag, a chart upgrade updates them together, but if you manage CRDs separately, you must update them to the target version as part of the upgrade rather than after, or the new controller may reject resources defined under an older schema. cert-manager's guidance is to upgrade one minor version at a time rather than jumping several versions, because the migration logic between versions assumes incremental steps. Skipping versions is the most common way to break a cert-manager upgrade. After upgrading, confirm that existing Certificates remain ready and that a renewal still completes, because the real test of a certificate-management upgrade is whether issuance and renewal still work, not merely that the pods restarted.

Version skew between the proxy, cert-manager, and the cluster's own Kubernetes version is the quiet risk underneath all of this. Each component declares the Kubernetes versions it supports, and AKS upgrades the cluster on its own cadence, so a cluster upgrade can move you onto a Kubernetes version that your pinned controller or cert-manager version does not officially support. Track the support matrix for all three together rather than upgrading any one in isolation, and when AKS schedules a cluster upgrade, confirm your controller and cert-manager versions support the target Kubernetes version before the upgrade lands. Treating the three as a coordinated set, rather than three independent upgrades, is what keeps the chain healthy across the cluster's lifetime.

## How the load balancer health probe shapes ingress availability

The Azure load balancer in front of the NGINX proxy does not blindly forward traffic; it probes the controller and only sends traffic to backends the probe considers healthy. How that probe is configured, and how it interacts with the proxy's own readiness, determines whether your ingress stays available during pod restarts, node drains, and upgrades. This is the link between Kubernetes-level health and Azure-level routing, and it is easy to overlook until an upgrade causes a brief outage that the cluster logs do not explain.

The proxy pods expose a health endpoint, conventionally `/healthz`, and NGINX's readiness probe gates whether a pod is considered ready to receive traffic. When a controller pod is starting, reloading a large configuration, or shutting down, its readiness reflects that, and Kubernetes removes an unready pod from the service endpoints so traffic stops flowing to it. The Azure load balancer, in turn, probes the nodes backing the service and stops sending traffic to nodes whose probe fails. The two layers together mean a restarting proxy pod should drain cleanly, provided another ready pod exists to take the traffic.

That proviso is the whole game. With a single controller replica, there is no other ready pod, so any restart, eviction, or node drain takes the only controller down and the routing layer goes dark until the pod comes back. With the `externalTrafficPolicy` set to `Local`, the dependency is sharper still, because Local routing means the load balancer only considers a node healthy if it is actually running a proxy pod, so the proxy must be present on enough nodes to keep the probe passing somewhere. Running multiple replicas, and spreading them across nodes and across availability zones where the cluster uses them, is what keeps a ready controller reachable through any single disruption.

### Why does my ingress briefly go down during a node drain or upgrade?

A brief outage during a drain or upgrade almost always means too few controller replicas, or replicas packed onto too few nodes, so a disruption takes them all at once. Run multiple controller replicas spread across nodes and zones, add a PodDisruptionBudget so a drain cannot evict them all simultaneously, and confirm the load balancer always has a healthy node to route to.

Pod anti-affinity is the tool that enforces the spread. A soft anti-affinity rule that prefers to place controller replicas on different nodes keeps a single node failure from removing every replica, and a topology spread constraint across zones extends that protection to a zone outage. Without such a rule, the scheduler is free to place all your replicas on one node, which gives you the false comfort of a replica count greater than one with the real availability of a single point of failure. The PodDisruptionBudget complements this by telling Kubernetes never to voluntarily evict so many controller pods that fewer than a minimum remain available, which protects you specifically during node drains and cluster upgrades, the planned disruptions that are otherwise the most common cause of a surprise ingress outage. The shape of a resilient controller is therefore concrete: several replicas, anti-affinity to spread them, a disruption budget to protect them during planned maintenance, and a health probe configuration that lets the load balancer route around any one of them while it restarts. Get that shape right and the front door survives the routine churn of a living cluster without anyone noticing.

## Protecting the front door: rate limits, headers, and what belongs in front

A public ingress controller is the single inbound surface for every web service behind it, which makes it both the natural place to apply protection and a tempting single target. Treating it as a security boundary rather than a passive proxy is what separates a controlled entry point from an open door, and the NGINX proxy gives you several levers that cost little to enable.

Rate limiting at the ingress blunts abusive traffic before it reaches your backends. The controller supports per-client connection and request rate limits through annotations, keyed on the client address that `externalTrafficPolicy=Local` preserved for exactly this purpose. A modest limit on requests per second per client absorbs accidental hammering and slows down brute-force attempts without affecting normal users, and because it runs at the proxy, your application never spends resources on the rejected requests. Set the limit to a value comfortably above legitimate peak usage so it acts as a ceiling on abuse rather than a throttle on real traffic.

Security response headers are another cheap win applied in one place. Rather than asking every backend to set headers like strict transport security, content type options, and frame options, you can have the controller add them to every response through a configuration snippet or a shared configuration, so a new service inherits the headers without its developers having to remember them. Centralizing response headers at the routing tier is consistent with the whole reason ingress exists, which is to apply shared policy once at the edge rather than scattering it across every workload.

For internet-facing workloads with real exposure, the question is often what belongs in front of the routing layer rather than on it. An Azure web application firewall, whether through Application Gateway or Front Door, sits ahead of the proxy's public IP and inspects traffic for common attack patterns before it ever reaches the cluster, adding a layer the in-cluster controller is not designed to provide. The trade-off is added cost and an extra hop, so the firewall layer is justified for workloads that face genuine internet threat and overkill for an internal tool. The decision is the same kind of deliberate trade-off the rest of this setup demands: apply the protection the exposure warrants, and no more.

The last piece of protecting the front door is governing who may open new doors through it. In a multi-tenant cluster, the ability to create ingress objects and set arbitrary controller annotations is effectively the ability to expose services and change edge behavior, so restricting who can create ingresses, and limiting which annotations untrusted namespaces may set, keeps a single misconfigured or malicious tenant from reshaping the cluster's public surface. That governance belongs in the same hardening pass as network policy and admission control, and it is the difference between a routing rule that a platform team controls and one that anyone with cluster access can repoint. The controller is the front door; deciding who holds the keys is as much a part of the configuration as the certificate that locks it.

## The AKS managed ingress add-on versus a self-managed controller

AKS offers a managed application routing add-on that installs and operates an NGINX ingress controller for you, and deciding between it and the self-managed Helm installation this guide describes is a real fork worth understanding rather than defaulting past. The add-on provisions NGINX, wires it to a managed certificate flow that can integrate with Azure DNS and Key Vault, and keeps the proxy upgraded as part of the cluster's lifecycle, which removes the Helm release you would otherwise own.

The appeal is operational: one less component to install, version, and upgrade by hand, and a certificate path that Azure manages rather than you assembling cert-manager and an issuer yourself. For teams that want a working ingress without taking on the maintenance of the NGINX proxy and the certificate machinery, the add-on is a reasonable starting point, and it follows the same controller-class-certificate logic underneath, so the mental model transfers directly.

The trade-off is control and flexibility. A self-managed controller lets you pin exact chart versions, set any controller configuration the chart exposes, run multiple controllers with distinct classes, and adopt new controller features the day they ship rather than when the add-on incorporates them. The managed add-on, like any managed abstraction, constrains you to the configuration surface and the upgrade cadence Azure exposes, which is liberating when you want defaults and limiting when you need a specific tuning the add-on does not surface. There is also the matter of portability: a self-managed Helm setup looks identical on any Kubernetes cluster, while the add-on is an AKS-specific convenience that does not travel to other platforms.

The honest decision rule is about who should own the proxy's lifecycle. If your team wants Azure to operate the front door and you can live within its configuration surface, the add-on removes genuine toil. If you need precise control over the proxy version and configuration, run multiple controllers, or want a setup that is identical across clusters and clouds, the self-managed installation this guide builds is the better fit. Many teams start with the add-on and graduate to self-managed when they hit a configuration they cannot express, which is a perfectly sensible path as long as the migration is planned rather than forced by an outage. Whichever you choose, the verification discipline is the same: prove each link in the chain is healthy in dependency order, because a managed controller can still be undone by a DNS record that points nowhere or a class that nothing claims.

## Where the Ingress API is heading: the Gateway API

The Kubernetes Ingress resource this guide uses is mature and ubiquitous, but it is not the end of the story, and a team building ingress today should know that the Gateway API exists as the designed successor. The Ingress resource solved the basic case well and then accumulated a sprawl of controller-specific annotations to express everything it could not, which is why so much real ingress behavior lives in annotations rather than in the spec itself. The Gateway API addresses that by moving routing, traffic policy, and the separation between infrastructure and application concerns into first-class, typed resources rather than annotations.

The shape of the Gateway API splits responsibilities that Ingress conflates. A GatewayClass and a Gateway describe the infrastructure, the equivalent of NGINX and its listeners, and are typically owned by a platform team. HTTPRoute and related route resources describe the application routing and are owned by the teams that run the services, referencing a Gateway they are permitted to attach to. That separation maps cleanly onto how organizations actually divide responsibility, where one team operates the shared ingress infrastructure and many teams attach their own routes to it, which the single flat Ingress object never expressed well.

For an AKS team today, the practical guidance is measured. Ingress with the NGINX controller remains a fully supported, well-understood choice, and there is no urgency to migrate working ingress objects. The value of knowing about the Gateway API now is in new design: if you are standing up ingress for a large multi-team platform, the Gateway API's separation of infrastructure from routes may fit your organization better than annotations on shared Ingress objects, and controllers including ingress-nginx and others increasingly support it. The controller-class-certificate chain still applies in spirit, because a Gateway still needs an implementation behind it, routes still need to bind to that implementation, and TLS still needs certificates from somewhere. The names change and the separation sharpens, but the discipline of proving each link in dependency order carries straight over. Treat the Gateway API as the direction of travel worth designing toward for greenfield platforms, and treat your existing Ingress setup as solid ground you do not need to abandon.

## Long-lived connections: WebSockets, gRPC, and session affinity

The defaults that suit short request-response traffic quietly break the connection styles that do not fit that mold, and these failures are among the hardest to attribute because the connection works briefly and then drops. WebSockets are the common case. A WebSocket starts as an HTTP request that upgrades to a persistent bidirectional connection, and the NGINX controller handles the upgrade correctly out of the box, but the proxy read timeout still applies to the connection's idle periods. A WebSocket that sits quiet longer than the read timeout is closed by the proxy, which the client experiences as a connection that drops every few seconds for no visible reason. The fix is to raise the read and send timeouts on that ingress to comfortably exceed the longest expected idle gap, the same timeouts that matter for slow uploads, applied here for a different reason.

gRPC backends need an explicit declaration because gRPC rides on HTTP/2 and the proxy must know to speak HTTP/2 to the upstream rather than HTTP/1.1. The backend-protocol annotation set to GRPC tells the NGINX proxy to proxy the connection as gRPC, and without it the controller talks the wrong protocol to a gRPC service and the calls fail in ways that look like application errors. When a gRPC service behind an ingress returns protocol errors that the service does not produce when called directly, the missing backend-protocol annotation is the first thing to check.

Session affinity, sometimes called sticky sessions, is the third long-lived concern. By default the proxy load-balances each request across the backend pods independently, which is correct for stateless services and wrong for any workload that keeps per-client state in a specific pod. The affinity annotations let NGINX pin a client to one backend pod using a cookie, so a stateful session keeps reaching the pod that holds its state. Use affinity only when the workload genuinely needs it, because pinning clients to pods undercuts even load distribution and complicates rolling updates, where a pod that a client is stuck to may be the one being replaced. The cleaner long-term answer is usually to make the service stateless and externalize the session state, but when that is not yet possible, ingress-level affinity is the bridge. Each of these three cases shares a lesson: the proxy's defaults are tuned for ordinary web traffic, and any connection style that differs from that needs a deliberate annotation, not a hope that the default will cope.

## Closing verdict

AKS ingress with TLS is not hard once you stop treating it as a single feature and start treating it as a chain. The controller moves the packets and owns the public IP. The ingress class binds your rules to that controller and prevents the silent no-op of an unclaimed ingress. cert-manager and an issuer supply real certificates and renew them so TLS is not a recurring chore. DNS points the hostname at the front door so both the ACME challenge and real clients can arrive. Every failure you will hit lives at one of those links, and every link has a command that confirms whether it is healthy.

The discipline that turns this from fragile to durable is verification in dependency order and configuration in code. Build the NGINX proxy, prove it has an IP, prove the class exists, prove the issuer is ready, prove DNS resolves, then create the ingress and prove HTTPS works from outside, in that sequence, and you will never again debug a certificate problem that was really a DNS problem or a routing problem that was really a missing class. Commit the Helm values, the issuers, the routing tier manifests, and the static IP so the whole chain rebuilds the same way every time. The controller-class-certificate chain is the model; the checklist is the tool; the commands are the proof. Hold all three and AKS ingress stops being a source of surprises and becomes the boring, reliable front door it is supposed to be.

What carries beyond this one cluster is the habit, not the specific commands. The commands will shift as charts version up, as the managed add-on absorbs more of the work, and as the Gateway API gradually reshapes how routing is expressed, but the reasoning does not change. An entry point that moves packets must exist and have an address. A binding must connect your rules to that entry point unambiguously. A certificate authority must supply and refresh real keys. A name must resolve to the door. Whenever a route misbehaves on any platform or any version, you walk those four questions in order and the failing one announces itself. Engineers who learn ingress as a memorized recipe are stranded the first time a detail differs; engineers who learn it as a dependency chain debug a setup they have never seen before, because the chain is the same even when the syntax is not. That transferable instinct, more than any single manifest in this guide, is what turns ingress from a recurring source of incidents into infrastructure you trust.

## Frequently Asked Questions

### Q: How do I set up NGINX ingress on AKS from scratch?

Install the ingress-nginx controller with Helm into its own namespace, which creates the controller deployment, an IngressClass named nginx, and a LoadBalancer service that requests a public IP from Azure. Wait for that service to show an external IP, then install cert-manager with Helm and create a ClusterIssuer for Let's Encrypt. Point a DNS A record at the proxy's public IP, and finally create an ingress object that names the nginx class, includes a TLS block, and carries the cert-manager cluster-issuer annotation. The order matters because each piece depends on the one before it: NGINX must exist before the class is useful, the issuer must exist before a certificate can be requested, and the routing layer references both. Verify the whole chain by running curl against your hostname over HTTPS and confirming the certificate was issued by Let's Encrypt rather than the proxy's built-in placeholder.

### Q: What is the difference between an NGINX proxy and an ingress class?

The controller is the running software that actually reads ingress objects and proxies traffic, while the ingress class is the binding that tells a controller which ingress objects belong to it. You can have a controller with no traffic flowing because no ingress names its class, and you can have a routing rule that serves nothing because its class points at a controller that is not installed. The controller is a workload, a set of pods plus a LoadBalancer service with a public IP. The class is a cluster-scoped IngressClass resource whose controller value matches what the NGINX proxy process watches for. An ingress object connects to a controller by setting its ingressClassName field to the name of an IngressClass whose controller value the running controller recognizes. When people say an ingress is not working despite looking correct, the broken link is most often this class binding rather than the controller itself or the rules inside the object.

### Q: How does cert-manager get a certificate from Let's Encrypt?

cert-manager watches for Certificate resources, which a route can request automatically through the cluster-issuer annotation, and for each one it creates a CertificateRequest, opens an ACME Order with Let's Encrypt, and completes a Challenge that proves you control the domain. For the HTTP-01 challenge, cert-manager creates a temporary ingress that serves a unique token at a well-known path, and Let's Encrypt fetches that token over HTTP to confirm control before issuing the certificate. Once the challenge passes, cert-manager stores the issued certificate and private key in a Kubernetes secret of type kubernetes.io/tls, and the NGINX controller loads that secret to terminate TLS. cert-manager also schedules renewal well before the certificate expires, repeating the same challenge automatically, which is why the short validity period of a Let's Encrypt certificate is a feature rather than a burden. The most common stall point is the challenge token not being reachable, which means either DNS does not resolve to the proxy or the challenge ingress is not being served because of a class mismatch.

### Q: Why does my browser show a fake certificate warning on an AKS ingress?

The NGINX ingress controller serves a built-in self-signed placeholder certificate, often issued to "Kubernetes Ingress Controller Fake Certificate," whenever it has no real certificate to present for a hostname. Seeing that certificate means TLS terminated correctly but the real certificate was never produced or never loaded into NGINX. The cause is almost always upstream in the certificate chain rather than in NGINX itself. Check whether cert-manager actually issued the certificate by describing the Certificate resource and looking at its ready status, then confirm the TLS secret named in your ingress exists and contains a real certificate rather than being empty or absent. Common reasons the real certificate is missing include a stalled ACME challenge, a cluster-issuer annotation pointing at an issuer that is not ready, a TLS secret name in the front door that does not match what cert-manager created, or a rate limit that blocked issuance. Fix the issuance, confirm the certificate goes ready, and the proxy swaps the placeholder for the real certificate automatically.

### Q: How do I give the NGINX proxy a static public IP on AKS?

Create a Standard SKU public IP with a static allocation method in the cluster's node resource group, the managed resource group named like MC underscore your resource group underscore cluster name underscore region, because that is where AKS places load balancer IPs. Then configure the NGINX proxy's LoadBalancer service to use it by setting the loadBalancerIP to that address and adding the azure-load-balancer-resource-group annotation naming the node resource group, which tells AKS to use the pre-created IP rather than allocating a new dynamic one. Doing this through your Helm values keeps the configuration reproducible. A static IP matters because DNS points at it, and a dynamic IP can change if the service is recreated, which would silently break every hostname that resolved to the old address. Note that some newer chart and Kubernetes versions are deprecating the loadBalancerIP field in favor of annotation-based configuration, so confirm which approach your chart version expects rather than assuming the field is available.

### Q: Why is my ACME challenge stuck in a pending state?

A pending Challenge means cert-manager cannot complete the proof that you control the domain, and for an HTTP-01 challenge that nearly always reduces to the challenge token being unreachable. Two things make it unreachable. First, the hostname does not resolve to the controller's public IP yet, either because the DNS A record was never created, points at an old address, or has not propagated past its TTL. Second, the temporary challenge ingress that cert-manager creates is not being served because its ingress class does not match your real proxy's class, so the proxy never picks it up. Diagnose by describing the Challenge, which reports the self-check reason, then confirm the hostname resolves to the right IP with dig and confirm the solver's ingress class matches your IngressClass. Fixing whichever link is broken, publishing the DNS record or aligning the class, lets the self-check pass and the certificate issues on its own. Using the Let's Encrypt staging issuer while you iterate avoids burning production rate limits during this debugging.

### Q: Should I use a ClusterIssuer or an Issuer in cert-manager?

The choice is about scope. An Issuer is namespaced and can only fulfill Certificate requests in the same namespace it lives in, while a ClusterIssuer is cluster-wide and can serve requests from any namespace. For a shared ingress controller that fronts services across several namespaces, a ClusterIssuer is usually the cleaner choice because you define the Let's Encrypt account and solver once and every namespace can use it through the cluster-issuer annotation. Use a namespaced Issuer when you deliberately want to isolate certificate issuance to one team or namespace, perhaps with a different account or solver configuration, so that one namespace cannot request certificates through another's issuer. Functionally the two behave identically in how they drive ACME and store certificates; the only real difference is the blast radius and who can reference them. Most platform teams running a central ingress settle on one or two ClusterIssuers, typically a staging and a production Let's Encrypt issuer, and reference them from ingress objects throughout the cluster.

### Q: Why does my ingress return a 404 default backend?

A default backend 404 from the NGINX controller means a request reached NGINX but no ingress rule matched it, so the proxy fell back to its catch-all backend. The two dominant causes are a routing rule that the NGINX proxy never adopted and a host or path that does not match any rule. If the controller adopted no rule at all, the usual reason is a class mismatch: the ingress has an empty ingressClassName, names a class that does not exist, or relies on a deprecated annotation that the current controller ignores. Confirm by reading the object's class and comparing it to the installed IngressClass list. If the proxy did adopt the routing tier but a specific request still 404s, check that the request's Host header exactly matches the host in the rule and that the path matches the configured pathType, since a Prefix match and an Exact match behave differently. Correct the class so NGINX claims the rule, or correct the host and path so the request matches, and the 404 turns into your service's response.

### Q: How do I serve multiple hostnames through one AKS ingress controller?

One controller and one public IP can serve any number of hostnames, which is the main reason to use ingress instead of a load balancer per service. Each hostname gets its own ingress object, or you combine several hosts into one object, with a rule per host that routes to the appropriate backend service. Every host that needs TLS lists itself in a tls block with a secret name, and cert-manager issues a separate certificate per hostname, or a single certificate covering multiple names if you configure it that way. The DNS records for every hostname point at the same controller public IP, and the proxy routes by the Host header in each request to the right service. This is exactly the consolidation ingress is built for: add a service, add an ingress rule and a DNS record, and the existing controller and certificate machinery handle it without a new public IP or a new load balancer. Keep the rules in version control so the growing set of hostnames stays reviewable.

### Q: What does externalTrafficPolicy Local do for an proxy?

Setting externalTrafficPolicy to Local on the NGINX proxy's LoadBalancer service preserves the original client source IP as traffic passes through the Azure load balancer, rather than replacing it with a node's internal IP through source NAT. This matters whenever you care about the real caller address, for rate limiting, IP allow lists, geographic logging, or any policy that keys on who is connecting. The trade-off is that the load balancer health probe only succeeds against nodes that are actually running a proxy pod, because Local routing does not bounce traffic to a pod on another node. In practice that means you want the controller spread across enough nodes that the load balancer always has a healthy target, typically by running multiple replicas. The alternative, the Cluster policy, spreads traffic evenly and probes succeed on every node, but it hides the client IP behind SNAT. For an NGINX proxy where source IP visibility is usually valuable, Local is the common production choice, paired with enough replicas to keep the probe healthy.

### Q: How do I configure ingress for an internal, non-public service on AKS?

Add the azure-load-balancer-internal annotation set to true on the proxy's LoadBalancer service, which makes AKS provision an internal load balancer with a private IP from your virtual network instead of a public address. The controller then sits behind a private frontend reachable only from within the network or from peered and connected networks, and you point a private DNS zone record at that private IP. The routing chain is otherwise identical, but TLS differs because Let's Encrypt cannot reach an internal hostname to complete an HTTP-01 challenge from the public internet. Internal ingresses therefore typically use the DNS-01 challenge, which proves domain control by writing a TXT record rather than serving an HTTP token, or they use an internal certificate authority instead of a public one. A clean pattern is to run two controllers with distinct ingress classes, a public one and an internal one, so the class an ingress names becomes the explicit statement of whether the service is meant to be reachable from the internet, removing the chance of exposing an internal service by mistake.

### Q: Why did my certificate work at first and then fail to renew?

A certificate that issued cleanly and later failed to renew means a dependency present at first issuance has since changed, because cert-manager uses the same challenge process for renewal as for the original issuance. The frequent culprits are a DNS A record that changed or was deleted so the renewal challenge can no longer reach NGINX, an issuer that was modified or removed, or a rate limit that something tripped by requesting certificates repeatedly in a loop. Diagnose by listing certificates across namespaces, describing the one that failed to find its renewal status and the reason, and checking for a stuck Challenge tied to the renewal. The fix follows the reported reason: restore the DNS record to point at the proxy, recreate or correct the issuer, or stop and back off whatever was requesting certificates in a loop and wait for the rate limit window to clear. Monitoring certificate expiry proactively, rather than waiting for a client to report an expired certificate, converts this from a customer-visible outage into routine maintenance.

### Q: Do I need cert-manager, or can I bring my own certificate to an AKS ingress?

You do not strictly need cert-manager. You can create a TLS secret manually from a certificate and key you obtained elsewhere, a wildcard certificate from a commercial certificate authority for example, and reference that secret in your ingress tls block. The NGINX controller will happily terminate TLS with any valid certificate in a properly formed secret. What you lose without cert-manager is automation: you become responsible for renewing the certificate before it expires and updating the secret, which is the step teams forget until a browser warning appears. cert-manager exists to remove that manual renewal entirely, and it pairs naturally with short-lived Let's Encrypt certificates where manual renewal would be impractical. A reasonable middle ground is to use cert-manager with a commercial issuer or an internal certificate authority if you cannot use Let's Encrypt, keeping the automation while changing the source of trust. Bring your own certificate only when you have a specific reason and a process to manage its lifecycle, because a manually managed certificate is a future expiry waiting to surprise someone.

### Q: How do I increase the maximum upload size through an NGINX ingress?

The NGINX ingress controller limits the proxied request body to a modest default, and an upload larger than that limit returns a 413 Request Entity Too Large from the proxy before your application ever receives the request, which is why the application logs show nothing. Raise the limit with the proxy-body-size annotation on the specific ingress object, setting it to a value with a unit such as 50m for fifty megabytes, sized to your real upload needs. You can also set it globally in the NGINX proxy's configuration if every service shares the same requirement, but a per-ingress annotation is more precise and avoids loosening the limit for services that should keep a tight cap. After applying the annotation the controller reloads its configuration and the larger uploads succeed. Remember that the limit is one of several proxy defaults tuned for safety rather than for any particular workload, so review the read and write timeouts at the same time if your uploads are also slow, since a large file over a slow connection can hit a timeout even after the size limit is raised.

### Q: How do I verify my AKS ingress TLS setup is actually working?

Verify in two places, inside the cluster and from a real client outside it, because each catches what the other misses. Inside, describe the Certificate resource to confirm it reports ready and check that the TLS secret it produced exists and is of type kubernetes.io/tls, which proves cert-manager finished its work. Outside, run curl with the verbose flag against your hostname over HTTPS and read the TLS handshake: the server certificate's subject should be your hostname and its issuer should be Let's Encrypt rather than the proxy's fake placeholder certificate. For a precise look at the chain, use openssl s_client to connect and print the issuer, subject, and validity dates, which confirms both that the certificate is genuine and that it has a sensible expiry cert-manager will renew before. If curl returns your application's content over a trusted HTTPS connection with a real issuer, the entire controller-class-certificate chain is healthy and verified end to end. Doing the external check from outside the cluster network also confirms DNS resolves correctly for ordinary clients, not just inside the cluster.

### Q: Can I run more than one NGINX proxy in the same AKS cluster?

Yes, and it is a common production pattern, but every controller must have a distinct ingress class so they do not compete for the same ingress objects. A frequent setup runs a public controller with one class and an internal controller with another, so each ingress declares, through the class it names, whether it should be reachable from the internet or only from inside the network. The hazard is ambiguity: if two controllers can both claim an unclassed ingress, or if you rely on a default class that more than one controller might interpret, you get inconsistent routing where a rule is served by the wrong controller with the wrong configuration. Avoid that by giving each controller a unique IngressClass name, marking at most one class as default and only if you truly want unclassed ingresses adopted, and making every ingress object name its class explicitly. Diagnosing a conflict starts with listing the IngressClass resources and NGINX pods across namespaces to see how many controllers actually exist and which classes they own.

### Q: What ports and traffic does the AKS ingress public IP expose?

The proxy's LoadBalancer service typically exposes ports 80 and 443 on the public IP, forwarding HTTP and HTTPS into the proxy pods, which then terminate TLS and route by host and path to internal services. Everything behind the NGINX proxy stays as ClusterIP services, private to the cluster, so the public IP is the single inbound surface for web traffic. Because that one address is the front door for the whole cluster, it is a natural place to apply protection: restrict who can create or modify ingress objects, consider a web application firewall or Azure-level protection in front of the IP for internet-facing workloads, and apply network policy so the controller can only reach the backends it should. The plain HTTP port 80 generally exists to serve the ACME challenge and to redirect clients to HTTPS rather than to serve real traffic unencrypted, so confirm the redirect is in place. Treating the routing layer IP as the security boundary it is, rather than an incidental detail, is the difference between a controlled entry point and an open door.

### Q: How do I make my AKS ingress and TLS setup reproducible as code?

Capture all three layers of the chain in version control. The controller and cert-manager are Helm releases, so pin their chart versions and record their configuration in committed values files rather than passing flags interactively, which fixes the proxy behavior across rebuilds. The ClusterIssuers and ingress objects are plain Kubernetes manifests that live in the same repository and apply through a pipeline or a GitOps controller that reconciles the repository against the cluster. The static public IP is an Azure resource rather than a Kubernetes object, so declare it in Bicep or Terraform alongside the cluster, created in the node resource group, and reference its address from the Helm values. The payoff is that you can destroy and recreate the cluster and have the same hostname serving the same content over the same certificate without manual DNS surgery, because the IP is stable and every layer rebuilds identically. A setup that survives a cluster rebuild untouched is the practical definition of reproducible, and it is the standard worth holding the configuration to.
