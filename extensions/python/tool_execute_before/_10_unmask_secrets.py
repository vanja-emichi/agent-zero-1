import logging

from helpers.extension import Extension
from helpers.secrets import get_secrets_manager

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
            else:
                logger.warning(
                    "Skipping placeholder resolution for unrecognized arg '%s' "
                    "(not in SECRET_ARG_NAMES or CONTENT_ARG_NAMES)",
                    k,
                )
