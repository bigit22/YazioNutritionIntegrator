# Security Policy

## Supported versions

Only the latest commit on `main` is supported. There are no separate release branches.

## Reporting a vulnerability

If you discover a security vulnerability, please **do not open a public issue**.

Instead, report it privately via GitHub Security Advisories:
https://github.com/bigit22/YazioNutritionIntegrator/security/advisories/new

You can expect an initial response within a few days.

## Scope

This project uses reverse-engineered private Yazio API endpoints. Issues related to Yazio's own security or their API
are **out of scope** — please report those directly to Yazio.

In scope:

- Secrets accidentally committed to the repository
- Authentication / authorization issues in the bot itself
- Vulnerabilities in the deployment scripts (`install.sh`, `uninstall.sh`)
- Injection issues in Telegram command handling
