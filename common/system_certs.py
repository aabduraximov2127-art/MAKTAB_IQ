"""Make Python trust the operating system's certificate store.

Needed on machines where an antivirus / corporate proxy inspects HTTPS (e.g. Avast "Web Shield"):
its root CA lives in the OS store but not in certifi's bundle, so requests/httpx calls to
api.telegram.org fail with CERTIFICATE_VERIFY_FAILED. Verification stays ON — we only widen
the trusted roots to what the OS already trusts.
"""


def use_system_trust_store():
    try:
        import truststore

        truststore.inject_into_ssl()
    except Exception:  # noqa: BLE001 - optional nicety, never fatal
        pass
