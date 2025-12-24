from app.core.validation.config_validator import ConfigValidator


def test_config_validator_import_and_instance():
    validator = ConfigValidator()
    assert validator is not None
