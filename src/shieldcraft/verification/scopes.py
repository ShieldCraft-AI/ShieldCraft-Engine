from enum import Enum, unique


@unique
class VerificationScope(Enum):
    SPEC = "spec"
    CHECKLIST = "checklist"
    CODE = "code"
    TESTS = "tests"
    PERSONA = "persona"
    OUTPUT = "output"
    SYSTEM = "system"
