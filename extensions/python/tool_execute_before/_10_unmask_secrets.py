import logging
import re

from helpers.extension import Extension
from helpers.secrets import get_secrets_manager, ALIAS_PATTERN

logger = logging.getLogger(__name__)

# Arg names where secret placeholder resolution is allowed (case-insensitive)
SECRET_ARG_NAMES = frozenset({
    "token", "api_key", "password", "secret", "key", "credential",
    "auth", "api_token", "access_token", "secret_key", "private_key",
    "passphrase",
})

# Arg names where resolution is explicitly denied (content-bearing args)
CONTENT_ARG_NAMES = frozenset({
    "content", "text", "code", "path", "patch_text", "old_text", "new_text",
    "message", "body", "html", "url", "query", "description", "prompt",
    "system_prompt",
})

# Precompiled pattern for detecting alias placeholders in values
_ALIAS_RE = re.compile(ALIAS_PATTERN)


class UnmaskToolSecrets(Extension):

    async def execute(self, **kwargs):
        if not self.agent:
            return

        # Get tool args from kwargs
        tool_args = kwargs.get("tool_args")
        if not tool_args:
            return

        secrets_mgr = get_secrets_manager(self.agent.context)

        # Resolve placeholders only in args that are known to accept secrets
        for k, v in tool_args.items():
            if not isinstance(v, str):
                continue

            name_lower = k.lower()
            if name_lower in SECRET_ARG_NAMES:
                tool_args[k] = secrets_mgr.replace_placeholders(v)
            elif name_lower in CONTENT_ARG_NAMES:
                logger.warning(
                    "Skipping placeholder resolution in content arg '%s'",
                    k,
                )
            elif _ALIAS_RE.search(v):
                # Unrecognized arg name, but value contains an alias pattern — resolve it
                # so tools using custom arg names for secrets still work.
                tool_args[k] = secrets_mgr.replace_placeholders(v)
            else:
                logger.debug(
                    "Skipping placeholder resolution for unrecognized arg '%s' "
                    "(no alias pattern detected in value)",
                    k,
                )
