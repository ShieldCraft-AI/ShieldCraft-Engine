def test_confidence_meta_for_prose_items():
    from shieldcraft.services.guidance.checklist import enrich_with_confidence_and_evidence
    items = [{'ptr': '/sections/0', 'text': 'The system must not allow unsafe operations', 'value': 'The system must not allow unsafe operations', 'meta': {}, 'evidence': {}}]
    res = enrich_with_confidence_and_evidence(items)
    assert any(it.get('inferred_from_prose') is True and it.get('confidence_meta', {}).get('source') == 'heuristic:prose' for it in res)


def test_confidence_meta_for_instruction_items():
    from shieldcraft.services.guidance.checklist import enrich_with_confidence_and_evidence
    items = [{'ptr': '/instructions/0', 'text': 'Verify the build', 'value': 'Verify the build', 'meta': {}, 'evidence': {}}]
    res = enrich_with_confidence_and_evidence(items)
    assert any(it.get('confidence_meta', {}).get('source') == 'instruction' and it.get('confidence') == 'high' for it in res)
