# Bounded Local AI Workflows — OS-enforced isolation demo.
#
# Demonstrates isolation (not mediation): the agent reaches the vault ONLY
# through the MCP sensitivity gate. The vault is readable solely by the `mcp`
# user; the unprivileged `agent` user has no read access and can reach the MCP
# only through a locked sudo launcher that runs the MCP as `mcp`. There is no
# out-of-band filesystem path for the agent.
FROM golang:1.27.2-bookworm@sha256:5cf287a799e6b94384bad13d16b14904c531f51ba65792237e122ce42b392f61 AS build

# The MCP is a single static Go binary; build it from source at MCP_REF.
ARG MCP_REF=main
RUN git clone --depth 1 --branch "${MCP_REF}" \
        https://github.com/joeseverino/severino-vault-mcp /src \
    && cd /src \
    && CGO_ENABLED=0 go build -trimpath -o /out/severino-vault-mcp ./cmd/severino-vault-mcp

FROM python:3.14-slim@sha256:f85c5697265c178cc6887276c55fe16cf3d14ca35c3df6a5eab3b360534a55d2

# The MCP uses ripgrep for body search; sudo enforces the single channel.
RUN apt-get update && apt-get install -y --no-install-recommends \
        sudo ca-certificates ripgrep \
    && rm -rf /var/lib/apt/lists/*

# Two principals. mcp owns the vault; agent is the untrusted client.
RUN useradd -m -u 1001 mcp && useradd -m -u 1002 agent

COPY --from=build /out/severino-vault-mcp /usr/local/bin/severino-vault-mcp

# The vault: the MCP's bundled sample vault (fake data), locked to mcp only.
# go-rwx removes all access for group/other, so `agent` cannot read or list it.
COPY --from=build /src/examples/sample-vault /vault
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
