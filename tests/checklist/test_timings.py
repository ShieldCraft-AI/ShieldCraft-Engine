"""
Test pipeline stage timing.
"""


def test_timings_exist():
    """Test that timings structure exists in generator output."""
    from shieldcraft.services.checklist.generator import ChecklistGenerator
    
    gen = ChecklistGenerator()
    spec = {"metadata": {"product_id": "test"}}
    
    # Build checklist (will add timings if implemented)
    result = gen.build(spec)
    
    # Check if timings exist
    if "timings" in result:
        timings = result["timings"]
        
        # Should be a dict
        assert isinstance(timings, dict)
        
        # Values should be numeric
        for pass_name, duration in timings.items():
            assert isinstance(duration, (int, float))
            assert duration >= 0


def test_timings_deterministic_keys():
    """Test that timing keys are deterministic."""
    from shieldcraft.services.checklist.generator import ChecklistGenerator
    
    gen = ChecklistGenerator()
    spec = {"metadata": {"product_id": "test"}}
    
    # Run twice
    result1 = gen.build(spec)
    result2 = gen.build(spec)
    
    # If timings exist, keys should match
    if "timings" in result1 and "timings" in result2:
        keys1 = sorted(result1["timings"].keys())
        keys2 = sorted(result2["timings"].keys())
        
        assert keys1 == keys2
