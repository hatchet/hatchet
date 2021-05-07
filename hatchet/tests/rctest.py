from hatchet.util.rcmanager import RcManager, _resolve_conf_file, _read_config_from_file


def test_creation():
    file = _resolve_conf_file()
    config = _read_config_from_file(file)
    RC = RcManager(config)

    assert RC is not None


def test_global_binding():
    import hatchet as ht

    assert hasattr(ht, "RcParams")


def test_change_value():
    import hatchet as ht
    from hatchet.util.rcmanager import RcParams

    assert "logging" in ht.RcParams

    ht.RcParams["logging"] = True
    assert ht.RcParams["logging"] is True
    assert RcParams["logging"] is True

    ht.RcParams["logging"] = False
    assert ht.RcParams["logging"] is False
    assert RcParams["logging"] is False
