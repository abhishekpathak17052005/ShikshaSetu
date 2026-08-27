from app.scripts.seed_framework import COMPETENCIES, ROLE_REQUIREMENTS, seed_framework


def test_seed_taxonomy_defines_all_four_domains() -> None:
    domains = {domain.value for domain, _ in COMPETENCIES}

    assert len(COMPETENCIES) == 33
    assert domains == {"STATISTICAL", "TECHNICAL", "DIGITAL_GOVERNANCE", "BEHAVIOURAL_MANAGERIAL"}
    assert len({name for _, name in COMPETENCIES}) == len(COMPETENCIES)
    assert len(ROLE_REQUIREMENTS) == 8
