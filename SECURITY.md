# Security Policy

## Scope

This server talks to a locally reachable printer. Keep it on a trusted local
network. Do not expose Moonraker or this server to the public internet.

Write operations are disabled unless `K2_ALLOW_WRITE=1` is set locally. The
project intentionally does not provide arbitrary G-code execution.

## Reporting a vulnerability

Do not publish vulnerabilities, printer access details, or credentials in a
public issue. Contact the maintainer privately through GitHub instead.
