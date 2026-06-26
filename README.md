# raphael-registry

Open publish/install for adapters, workflows, agents, templates

## API

- Prefix: `/v1/registry`
- Port: `8097`
- Health: `GET /health`

## Events

_Published and consumed events documented in `openapi.yaml` and raphael-contracts._

## Development

```bash
uv sync
uv run uvicorn raphael_registry.app:app --reload --port 8097
```

Part of the [Raphael Platform](https://github.com/hummingbird-labs) by HummingBird Labs.
