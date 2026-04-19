from hrdesk.domain.message import Message
from hrdesk.observability.logging import get_logger
from hrdesk.providers.factory import get_provider

log = get_logger(__name__)
provider = get_provider()
reply = provider.chat(
    [
        Message(role="user", content="Say 'hello' in one word only."),
    ]
)
log.info("provider_test", reply=reply.content)
