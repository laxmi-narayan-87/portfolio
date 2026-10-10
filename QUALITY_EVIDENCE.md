# Portfolio quality evidence

## What runs automatically

The GitHub Actions workflow runs on pushes to `portfolio` and `fix/**`, on pull requests targeting `portfolio`, and by manual dispatch. It runs a small Python regression suite against the checker and then validates the current `index.html`.

The checks cover document metadata, CSP directives, the absence of executable scripts and embedded content, remote asset dependencies, inline event handlers, JavaScript URLs, duplicate IDs, in-page links, new-tab link safety, image alt attributes, reduced-motion support, and the expected page landmarks.

## What these checks do not prove

- They are static checks, not a full HTML conformance validator or a browser-based accessibility audit.
- They do not prove that external profile/repository links exist, that the production deployment has the expected response headers, or that the site is free of all vulnerabilities.
- The CSP in a meta element cannot provide every response-header control (notably `frame-ancestors`). GitHub Pages does not provide arbitrary per-site HTTP response-header configuration. Treat this as a hosting limitation, not as a completed header-hardening claim.
- They do not validate Supabase or any other external service. This portfolio is intentionally static and these changes do not inspect or modify Supabase.
- No screenshots, test reports, or performance measurements should be presented as real unless captured from the actual running project and tied to a dated test run.

## Capturing authentic project evidence

For each project, add only artifacts that can be reproduced: a screenshot captured from the real running app, the exact commit or release, the test command/environment, and a short note describing what the image proves. Remove credentials, personal records, tokens, and other private data before publishing. Do not use generated mockups as evidence of implemented functionality.

## Release checklist

- [ ] Review the Actions run and resolve all failed checks.
- [ ] Open the site in a real browser at mobile and desktop widths.
- [ ] Check keyboard navigation, focus visibility, contrast, and reduced-motion behaviour.
- [ ] Open every project/profile link and remove broken or misleading links.
- [ ] Inspect the deployed response headers separately from the HTML meta policy.
- [ ] Capture genuine screenshots only after the corresponding feature is running.
