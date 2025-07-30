G4dn Spot Pricing Estimates
g4dn.xlarge

Spot price range (global average): $0.0645 – $0.282; typical around $0.19/hr
Amazon Web Services

In ap-south‑1 region: likely around $0.15–$0.20/hr

g4dn.2xlarge

Ubuntu price example: ≈ $0.752/hr (which may refer to on-demand or stale spot)
Vantage
+1
Amazon Web Services
+1

Estimated spot: around $0.28 – $0.65/hr based on usage trends
Reddit

g4dn.4xlarge

On-demand ~ $0.64/hr; spot around $0.64 – $1.36/hr
aimably.com
Azure, AWS and GCP Specs and Pricing

g4dn.8xlarge

Spot in ap‑south‑1: ≈ $0.51/hr; on-demand ~ $2.395/hr
sparecores.com

g4dn.16xlarge

Pricing entry-level: available at ~ $3176.96/month on-demand (~$4.40/hr). Spot likely around $2–3/hr, as per upward scaling trends
Azure, AWS and GCP Specs and Pricing


aws ec2 describe-spot-price-history \
--instance-types g4dn.xlarge g4dn.2xlarge g4dn.4xlarge g4dn.8xlarge g4dn.12xlarge g4dn.16xlarge g4dn.metal \
--product-descriptions "Linux/UNIX" \
--start-time "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" \
--region ap-south-1