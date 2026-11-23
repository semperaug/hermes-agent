"""The shared rules' session source and key builder keep main's ``shared_session`` flag (``gateway.session``)."""
from session_rules.route_entries import Platform, SessionSource, build_session_key


def _group(**extra):
    return SessionSource(platform=Platform.TELEGRAM, chat_id="-100", chat_type="group", user_id="111", **extra)


def test_shared_session_round_trips_and_is_absent_by_default():
    shared = _group(shared_session=True)
    assert shared.to_dict()["shared_session"] is True
    assert SessionSource.from_dict(shared.to_dict()).shared_session is True
    assert "shared_session" not in _group().to_dict()
    assert SessionSource.from_dict(_group().to_dict()).shared_session is False


def test_a_shared_group_source_keys_the_group_session_though_it_keeps_its_sender():
    from gateway.session import SessionSource as GatewaySource, build_session_key as gateway_key

    assert build_session_key(_group()) == "agent:main:telegram:group:-100:111"
    assert build_session_key(_group(shared_session=True)) == "agent:main:telegram:group:-100"
    main_source = GatewaySource.from_dict(_group(shared_session=True).to_dict())
    assert build_session_key(_group(shared_session=True)) == gateway_key(main_source)


def _whatsapp_dm(chat_id):
    return SessionSource(platform=Platform.WHATSAPP, chat_id=chat_id, chat_type="dm", user_id=chat_id)


def test_whatsapp_session_keys_are_canonicalised_identically_to_the_gateway():
    """Both key builders must resolve WhatsApp aliases to the same session key.

    The WhatsApp bridge can surface one human as a LID (``999...@lid``), as a
    phone JID (``1555...@s.whatsapp.net``), or as a bare phone number, and
    those are aliases for the *same* person. The gateway canonicalises them
    via :mod:`gateway.whatsapp_identity` so one human never lands in two
    sessions, and :func:`gateway.run_busy` depends on that when matching a
    live source against stored keys.

    ``session_rules.route_entries`` keeps its own copy of the key builder, so
    it has to canonicalise identically. Otherwise the two copies disagree for
    every aliased WhatsApp identity and a session keyed through one of them
    can never be found through the other.
    """
    from gateway.session import SessionSource as GatewaySource, build_session_key as gateway_key

    for chat_id in (
        "999123456789@lid",
        "15551234567@s.whatsapp.net",
        "+15551234567",
        "1555:12@s.whatsapp.net",
        "15551234567",
        "999123456789",
    ):
        source = _whatsapp_dm(chat_id)
        gateway_source = GatewaySource.from_dict(source.to_dict())

        expected = gateway_key(gateway_source)
        assert build_session_key(source) == expected, chat_id


def test_whatsapp_aliases_resolve_to_one_session_per_person():
    """Every alias for one person must land on the same session key.

    This pins the canonicalisation itself (not just the agreement between the
    two builders), so the case cannot be satisfied by both copies drifting
    together.
    """
    from gateway.session import SessionSource as GatewaySource, build_session_key as gateway_key

    def gateway_key_for(chat_id):
        source = _whatsapp_dm(chat_id)
        return gateway_key(GatewaySource.from_dict(source.to_dict()))

    # One person, reachable as a phone JID or as a bare phone number.
    assert gateway_key_for("15551234567@s.whatsapp.net") == "agent:main:whatsapp:dm:15551234567"
    assert gateway_key_for("+15551234567") == "agent:main:whatsapp:dm:15551234567"
    assert gateway_key_for("15551234567") == "agent:main:whatsapp:dm:15551234567"

    # A LID is canonicalised to its bare number too.
    assert gateway_key_for("999123456789@lid") == "agent:main:whatsapp:dm:999123456789"
