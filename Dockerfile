# Build from ~/Projects:
#   docker build -f raphael-registry/Dockerfile .
FROM python:3.11-slim
WORKDIR /app
RUN pip install --no-cache-dir uv
COPY raphael-contracts /deps/raphael-contracts
RUN uv pip install --system /deps/raphael-contracts
COPY raphael-registry/pyproject.toml raphael-registry/README.md ./
COPY raphael-registry/src ./src
RUN python3 -c "import re; from pathlib import Path; p=Path('pyproject.toml'); p.write_text(re.sub(r'\n\[tool\.uv\.sources\][^\[]*','\n',p.read_text(),flags=re.S))"
RUN uv pip install --system -e .
ENV RAPHAEL_SERVICE_PORT=8097
EXPOSE 8097
CMD ["uvicorn", "raphael_registry.app:app", "--host", "0.0.0.0", "--port", "8097"]
