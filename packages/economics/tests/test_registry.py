from macropulse_economics import COUNTRIES, SOURCES, PolicyRateScope, get_country


def test_initial_countries_are_the_five_specified() -> None:
    assert [c.iso2 for c in COUNTRIES] == ["BE", "DE", "FR", "NL", "US"]


def test_country_codes_are_unique_and_well_formed() -> None:
    iso2 = [c.iso2 for c in COUNTRIES]
    iso3 = [c.iso3 for c in COUNTRIES]
    assert len(set(iso2)) == len(iso2)
    assert len(set(iso3)) == len(iso3)
    assert all(len(c) == 2 and c.isupper() for c in iso2)
    assert all(len(c) == 3 and c.isupper() for c in iso3)


def test_euro_area_members_share_the_euro_area_policy_rate() -> None:
    for c in COUNTRIES:
        if c.euro_area_member:
            assert c.policy_rate_scope is PolicyRateScope.EURO_AREA_SHARED
            assert c.currency == "EUR"
        else:
            assert c.policy_rate_scope is PolicyRateScope.NATIONAL


def test_get_country_is_case_insensitive_and_rejects_unknown() -> None:
    be = get_country("be")
    assert be is not None
    assert be.name == "Belgium"
    assert get_country("XX") is None


def test_sources_have_https_docs_and_key_env_only_when_needed() -> None:
    ids = [s.id for s in SOURCES]
    assert len(set(ids)) == len(ids)
    for s in SOURCES:
        assert s.docs_url.startswith("https://")
        assert s.base_url.startswith("https://")
        assert (s.api_key_env is not None) == s.requires_api_key
