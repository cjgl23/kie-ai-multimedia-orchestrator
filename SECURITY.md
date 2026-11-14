# Security Policy

## Supported versions

Security fixes are targeted at the latest version on `main`.

## Reporting a vulnerability

Please use **Security → Report a vulnerability** if available. If private reporting is unavailable, open a public issue **without credentials, exploit details, or private media URLs**, requesting private contact from the maintainer.

## Credential and media handling

Use `KIE_API_KEY` through the environment, never a committed file. Avoid exposing sensitive input URLs or generated media in issue reports. Do not disable TLS validation to work around HTTPS or proxy errors.
