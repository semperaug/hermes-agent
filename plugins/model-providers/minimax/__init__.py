"""MiniMax provider profiles (international, China, OAuth).

Default routes use anthropic_messages (base URLs end in /anthropic). Users can
opt MiniMax-M3 into the OpenAI-compatible https://api.minimax.io/v1 route,
which needs MiniMax-specific reasoning controls in extra_body.
"""

from typing import Any
from urllib.parse import urlparse

from providers import register_provider
from providers.base import ProviderProfile

# MiniMax still advertises models in /v1/models that the inference endpoint has
# already retired — calling one returns HTTP 404 with error code 2069
# ("The model ... is no longer available"). Verified against the live endpoint:
# MiniMax-M2.1, MiniMax-M2.1-highspeed and MiniMax-M2 are listed but dead.
# Filter them so the picker never offers a model that cannot be called.
_MINIMAX_RETIRED_MODELS = frozenset({
    "minimax-m2.1", "minimax-m2.1-highspeed", "minimax-m2",
    "m2-her",
})


def _is_minimax_global_openai_base_url(base_url: str | None) -> bool:
    parsed = urlparse(str(base_url or "").strip())
    return (parsed.hostname or "").lower() == "api.minimax.io" and parsed.path.rstrip("/").lower() == "/v1"


class MiniMaxProfile(ProviderProfile):
    """MiniMax — M3 OpenAI-compatible reasoning controls."""

    def fetch_models(
        self, *, api_key: str | None = None, base_url: str | None = None, timeout: float = 8.0
    ) -> list[str] | None:
        """Live catalog from ``<base>/v1/models``, minus the ids the inference
        endpoint has already retired."""
        models = super().fetch_models(api_key=api_key, base_url=base_url, timeout=timeout)
        if models is None:
            return None
        return [m for m in models if str(m).strip().lower() not in _MINIMAX_RETIRED_MODELS]

    def build_api_kwargs_extras(
        self, *, reasoning_config: dict | None = None, model: str | None = None,
        base_url: str | None = None, **context: Any,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        """M3 on api.minimax.io/v1 keeps thinking inline unless ``reasoning_split``
        is sent; effort levels only select adaptive vs disabled ``thinking``."""
        is_m3 = str(model or "").strip().lower() in {"minimax-m3", "minimax/minimax-m3"}
        if not _is_minimax_global_openai_base_url(base_url) or not is_m3:
            return {}, {}
        extra_body: dict[str, Any] = {"reasoning_split": True}
        if isinstance(reasoning_config, dict) and reasoning_config.get("enabled") is False:
            extra_body["thinking"] = {"type": "disabled"}
        elif reasoning_config is not None:
            extra_body["thinking"] = {"type": "adaptive"}
        return extra_body, {}


minimax = MiniMaxProfile(
    name="minimax", aliases=("mini-max",), api_mode="anthropic_messages", env_vars=("MINIMAX_API_KEY",),
    base_url="https://api.minimax.io/anthropic", auth_type="api_key", default_aux_model="MiniMax-M3",
    # MiniMax serves its catalog at <base>/v1/models (OpenAI- and Anthropic-compatible shapes);
    # the default <base>/models path 404s.
    models_url="https://api.minimax.io/anthropic/v1/models",
)

minimax_cn = MiniMaxProfile(
    name="minimax-cn", aliases=("minimax-china", "minimax_cn"), api_mode="anthropic_messages",
    env_vars=("MINIMAX_CN_API_KEY",), base_url="https://api.minimaxi.com/anthropic", auth_type="api_key",
    default_aux_model="MiniMax-M3",
    # MiniMax serves its catalog at <base>/v1/models (OpenAI- and Anthropic-compatible shapes);
    # the default <base>/models path 404s.
    models_url="https://api.minimaxi.com/anthropic/v1/models",
)

minimax_oauth = MiniMaxProfile(
    name="minimax-oauth", aliases=("minimax_oauth", "minimax-portal", "minimax-global", "minimax-oauth-io"), api_mode="anthropic_messages",
    display_name="MiniMax (OAuth)", description="MiniMax via OAuth browser flow — no API key required",
    signup_url="https://api.minimax.io/",
    env_vars=(),  # OAuth — tokens in auth.json, not env
    base_url="https://api.minimax.io/anthropic", auth_type="oauth_external", default_aux_model="MiniMax-M3.1-Flash",
    # Same catalog path as the API-key profiles: <base>/v1/models.
    models_url="https://api.minimax.io/anthropic/v1/models",
)

register_provider(minimax)
register_provider(minimax_cn)
register_provider(minimax_oauth)
