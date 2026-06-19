# Bounded Local AI Workflows — OS-enforced isolation demo.
#
# Demonstrates isolation (not mediation): the agent reaches the vault ONLY
# through the MCP sensitivity gate. The vault is readable solely by the `mcp`
# user; the unprivileged `agent` user has no read access and can reach the MCP
# only through a locked sudo launcher that runs the MCP as `mcp`. There is no
# out-of-band filesystem path for the agent.
FROM python:3.12-slim

# The MCP uses ripgrep (body search) and fd (vault indexing); sudo enforces the
# single channel; git clones the MCP; ca-certificates for the clone.
RUN apt-get update && apt-get install -y --no-install-recommends \
        sudo git ca-certificates ripgrep fd-find \
    && rm -rf /var/lib/apt/lists/* \
    && ln -s "$(command -v fdfind)" /usr/local/bin/fd

# uv installs and runs the MCP from its own lockfile.
RUN pip install --no-cache-dir uv

# Two principals. mcp owns the vault; agent is the untrusted client.
RUN useradd -m -u 1001 mcp && useradd -m -u 1002 agent

# Build the MCP as the mcp user so the venv is owned by mcp.
ARG MCP_REF=main
ENV UV_CACHE_DIR=/home/mcp/.cache/uv UV_NO_PROGRESS=1
RUN git clone --depth 1 --branch "${MCP_REF}" \
        https://github.com/joeseverino/severino-vault-mcp /opt/mcp \
    && chown -R mcp:mcp /opt/mcp
USER mcp
WORKDIR /opt/mcp
RUN uv sync --no-editable --frozen
USER root

# The vault: the MCP's bundled sample vault (fake data), locked to mcp only.
# go-rwx removes all access for group/other, so `agent` cannot read or list it.
RUN cp -R /opt/mcp/examples/sample-vault /vault
# Add a `sensitive`-tier sample doc so the demo shows all three gate behaviors:
# internal (released), sensitive (released + advisory), restricted (withheld).
COPY ["read-boundary/sensitive-sample.md", "/vault/02 Infrastructure/Service Handoff.md"]
RUN chown -R mcp:mcp /vault && chmod -R go-rwx /vault

# The locked launcher: the single channel to the vault. Runs the MCP as mcp with
# the vault path fixed. Root-owned, not writable by agent.
COPY read-boundary/run-mcp /usr/local/bin/run-mcp
RUN chmod 0755 /usr/local/bin/run-mcp

# sudoers: agent may run ONLY run-mcp (no args) as mcp. Not a shell, not cat.
COPY read-boundary/agent.sudoers /etc/sudoers.d/agent
RUN chmod 0440 /etc/sudoers.d/agent && visudo -cf /etc/sudoers.d/agent

# The agent's verification client needs the MCP Python client library.
RUN pip install --no-cache-dir "mcp>=1.0"
COPY read-boundary/verify.py /usr/local/bin/verify.py
COPY read-boundary/mcp-read.py /usr/local/bin/mcp-read
RUN chmod 0755 /usr/local/bin/mcp-read

USER agent
WORKDIR /home/agent
ENTRYPOINT ["python3", "/usr/local/bin/verify.py"]
