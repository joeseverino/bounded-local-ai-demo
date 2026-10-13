# Bounded Local AI Workflows — action-boundary demo.
#
# Demonstrates the effect gate: Cordon decides allow / confirm / block from a
# command's declared effect and the deployment posture (local vs strict). The
# default run prints the decision matrix; run `cordon-gate` directly to see the
# interactive confirm prompt and the non-interactive fail-closed behavior.
FROM node:24.21.0-slim@sha256:d6aa754f16b3197301076f047b5def2f02ea1dbbc2ca920407d46d7ec7f87b20

RUN apt-get update && apt-get install -y --no-install-recommends git ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Cordon's harness (gate.ts + policy.ts) is zero-dependency and Node 24 runs
# TypeScript directly, so a shallow clone is all that is needed.
ARG CORDON_REF=main
RUN git clone --depth 1 --branch "${CORDON_REF}" \
        https://github.com/joeseverino/cordon /opt/cordon

COPY action-boundary/sample-tool /usr/local/bin/sample-tool
COPY action-boundary/policy-matrix.ts /usr/local/bin/policy-matrix.ts
RUN chmod 0755 /usr/local/bin/sample-tool \
    && printf '#!/bin/sh\nexec node /opt/cordon/harness/gate.ts "$@"\n' \
        > /usr/local/bin/cordon-gate \
    && chmod 0755 /usr/local/bin/cordon-gate

# Default: print the decision matrix. Override the entrypoint with cordon-gate to
# drive a single gated invocation (confirm prompt / fail-closed).
ENTRYPOINT ["node", "/usr/local/bin/policy-matrix.ts"]
CMD ["sample-tool"]
