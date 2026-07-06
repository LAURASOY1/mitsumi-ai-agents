# Decision 1

## Context

Backend currently runs API and worker together.

## Decision

Separate API and worker into independent containers.

## Why

- Independent scaling
- Easier deployments
- Better fault isolation

## Tradeoffs

- Slightly more infrastructure