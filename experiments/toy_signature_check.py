"""
Toy experiment: understand the shape of a signed update manifest before any
real signing exists. The signature here is a fake placeholder string --
the point is the flow (manifest has a signature field, verification checks
it before an agent trusts the manifest), not real cryptography. Real signing
comes from cosign in Week 7, against the actual container image.
"""

FAKE_TRUSTED_SIGNATURE = "fake-signature-for-now"


def build_manifest(version: str, image: str, digest: str, rollout: str = "canary") -> dict:
    return {
        "version": version,
        "image": image,
        "digest": digest,
        "rollout": rollout,
        "signature": FAKE_TRUSTED_SIGNATURE,
    }


def verify_manifest_signature(manifest: dict) -> bool:
    """Placeholder verification -- just checks the field is present and
    matches the one fake trusted value. Real verification (Week 7) will
    check a cosign signature against the actual image digest instead of a
    string constant."""
    return manifest.get("signature") == FAKE_TRUSTED_SIGNATURE


if __name__ == "__main__":
    manifest = build_manifest(
        version="1.1.0",
        image="ghcr.io/yourname/climate-control:1.1.0",
        digest="sha256:abc123",
    )
    print("Manifest:", manifest)
    print("Signature valid:", verify_manifest_signature(manifest))

    tampered = dict(manifest)
    tampered["signature"] = "attacker-supplied-signature"
    print("Tampered signature valid:", verify_manifest_signature(tampered))
