# Security Policy

## Scope
This repository contains a public, static personal portfolio. It should not collect credentials, payment details, or sensitive visitor information.

## Reporting a vulnerability
Do not publish exploit details in a public issue. Contact the repository owner through the email listed on the portfolio and include a description, impact, reproducible steps, and suggested mitigation. Allow reasonable time to investigate before public disclosure.

## Security expectations
- Never commit API keys, tokens, private keys, passwords, or production credentials.
- Publish only personal contact details intentionally shared by the owner.
- Do not add analytics, third-party scripts, database access, or forms without a clear need and security review.
- Configure security response headers at the hosting layer. The in-document CSP is defense in depth; it cannot replace HTTP headers such as frame-ancestors, HSTS, X-Content-Type-Options, and Referrer-Policy.
- Review changes for accessibility, broken links, and unexpected external requests before release.

A security policy is not a certification or a guarantee that the site is vulnerability-free.
