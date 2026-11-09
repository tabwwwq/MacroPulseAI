from macropulse_economics import COUNTRIES
from macropulse_economics.indicators import (
    INDICATORS,
    MAPPINGS,
    MappingStatus,
    get_indicator,
    mappings_for,
)


def test_indicator_ids_unique_and_kpis_defined() -> None:
    ids = [i.id for i in INDICATORS]
    assert len(ids) == len(set(ids))
    assert {i.id for i in INDICATORS if i.kpi} == {
        "real_gdp_qoq",
        "inflation_yoy",
        "unemployment_rate",
        "policy_rate",
    }


def test_every_mapping_points_to_a_known_indicator_and_country() -> None:
    countries = {c.iso2 for c in COUNTRIES}
    for m in MAPPINGS:
        assert get_indicator(m.indicator_id) is not None, m
        assert m.country in countries, m
    pairs = [(m.indicator_id, m.country) for m in MAPPINGS]
    assert len(pairs) == len(set(pairs)), "duplicate mapping"


def test_every_country_has_the_gdp_target_mapped() -> None:
    for c in COUNTRIES:
        gdp = mappings_for(c.iso2)["real_gdp_qoq"]
        assert gdp.status in {MappingStatus.VERIFIED, MappingStatus.PARTIAL}
        assert gdp.probe_last_period is not None


def test_probe_findings_are_reflected() -> None:
    # F-001: Eurostat HICP dataset is stale for the euro area countries.
    for c in ("BE", "DE", "FR", "NL"):
        hicp = mappings_for(c)["inflation_yoy"]
        assert hicp.status is MappingStatus.STALE
        assert hicp.probe_last_period == "2025-12"
    # F-002: OECD publishes no CLI for Belgium and the Netherlands.
    assert mappings_for("BE")["cli"].status is MappingStatus.NOT_PUBLISHED
    assert mappings_for("NL")["cli"].status is MappingStatus.NOT_PUBLISHED
    assert mappings_for("DE")["cli"].status is MappingStatus.PARTIAL


def test_shared_rate_and_scope_caveats_are_explicit() -> None:
    assert "Shared euro area" in mappings_for("DE")["policy_rate"].scope_note
    assert "Federal debt only" in mappings_for("US")["gov_debt_gdp"].scope_note
    assert "nber_recession" not in mappings_for("DE")
    assert (
        "never used as the technical-recession target" in mappings_for("US")["nber_recession"].note
    )
