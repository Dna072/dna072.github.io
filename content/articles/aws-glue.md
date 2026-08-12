---
title: AWS Glue for Lakehouse ETL
description: Using Glue jobs, the Data Catalog, and Athena to build landing → trusted → curated lakehouse zones.
date: 2026-03-15
tags: [AWS Glue, Lakehouse, Athena]
---

AWS Glue is a practical choice for Spark-based lakehouse ETL when you want serverless compute tightly integrated with S3 and the Glue Data Catalog.

## Zones create clarity

- **Landing** — raw, immutable-ish dumps
- **Trusted** — cleaned, consented, typed
- **Curated** — joined business/ML-ready tables

Consent filters and PII handling belong early—ideally before data reaches trusted zones.

## Catalog everything

If Athena cannot discover a table, analysts will invent shadow spreadsheets. Register schemas, document partitions, and keep naming consistent.

## Optimize for operability

Prefer jobs that are restartable, emit clear logs, and fail loudly on contract violations. Lakehouse platforms fail quietly when nobody owns quality.
