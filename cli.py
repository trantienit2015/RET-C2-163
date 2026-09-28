"""AGENTIC STAR Marketplace entry point — the container's ``CMD``.

Entry adapter only, in the same sense ``src/api/server.py`` is one. The runner owns the
lifecycle: it constructs the graph class, compiles it, builds the SecretProvider, provisions
secrets, then runs one Marketplace execution (identity, input, progress events, terminal
delivery, exit) and exits.

The runner constructs the graph itself, so ``config/config.yaml`` is loaded here and handed
over explicitly — without it every runtime parameter would fall back to its framework default
on this path only. Both entry points read it through the framework's own loader, so neither
restates how the file is found.

``agent_name`` / ``namespace`` mirror the values ``src/api/server.py`` passes to
``secrets_factory``, so secrets resolve from one place whichever transport started the agent.
"""

import logging
from pathlib import Path

from framework.utils.config_loader import load_agent_config
from shared.bootstrap.marketplace_app import run_agent_marketplace

from src.graph.graph import Graph

# cli.py sits next to config/ both in the repository and in the image
# (/app/cli.py + /app/config/config.yaml), so one expression covers both.
_AGENT_DIR = Path(__file__).resolve().parent

# Identity for the Marketplace runner. Mirrors what src/api/server.py hands to
# secrets_factory so both entry paths resolve secrets from the same location; an empty
# or defaulted value here would silently point the Marketplace path elsewhere.
_AGENT_NAME = "ret-c2-163"
_NAMESPACE = "ret"

# Add overrides here to set values without editing config/config.yaml.
extend_config: dict = {}

def main() -> None:
    # The framework writes its audit records to the ``agentcore.audit`` logger at INFO.
    # Nothing configures logging in this process, so without a handler those records are
    # dropped and a failed run leaves no trace of which node ran or why it stopped — the
    # pod log holds a traceback at best, and nothing at all when the run "succeeds" without
    # doing its work. Configure it here, at the entry point that owns process setup.
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    run_agent_marketplace(
        Graph,
        agent_name=_AGENT_NAME,
        namespace=_NAMESPACE,
        config={**load_agent_config(_AGENT_DIR), **extend_config},
    )


if __name__ == "__main__":
    main()
