# Bounded Local AI Workflows — action-boundary demo.
#
# Demonstrates the effect gate: Cordon decides allow / confirm / block from a
# command's declared effect and the deployment posture (local vs strict). The
# default run prints the decision matrix; run `cordon-gate` directly to see the
# interactive confirm prompt and the non-interactive fail-closed behavior.
FROM node:22-slim

RUN apt-get update && apt-get install -y --no-install-recommends git ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Cordon's harness (gate.mjs + policy.mjs) is zero-dependency, so a shallow clone
# is all that is needed — no npm install.
ARG CORDON_REF=main
RUN git clone --depth 1 --branch "${CORDON_REF}" \
        https://github.com/joeseverino/cordon /opt/cordon

COPY action-boundary/sample-tool /usr/local/bin/sample-tool
COPY action-boundary/policy-matrix.mjs /usr/local/bin/policy-matrix.mjs
RUN chmod 0755 /usr/local/bin/sample-tool \
    && printf '#!/bin/sh\nexec node /opt/cordon/harness/gate.mjs "$@"\n' \
        > /usr/local/bin/cordon-gate \
    && chmod 0755 /usr/local/bin/cordon-gate

# Default: print the decision matrix. Override the entrypoint with cordon-gate to
# drive a single gated invocation (confirm prompt / fail-closed).
ENTRYPOINT ["node", "/usr/local/bin/policy-matrix.mjs"]
CMD ["sample-tool"]
