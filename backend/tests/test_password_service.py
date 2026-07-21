from app.services.password_service import PasswordService


def test_hash_password_returns_non_empty_hash() -> None:
    service = PasswordService()

    hashed = service.hash_password("StrongPassword!123")

    assert isinstance(hashed, str)
    assert hashed
    assert hashed != "StrongPassword!123"


def test_hash_password_produces_unique_hashes_for_same_password() -> None:
    service = PasswordService()

    first = service.hash_password("StrongPassword!123")
    second = service.hash_password("StrongPassword!123")

    assert first != second


def test_verify_password_returns_true_for_matching_password() -> None:
    service = PasswordService()
    password = "StrongPassword!123"
    hashed = service.hash_password(password)

    assert service.verify_password(password, hashed) is True


def test_verify_password_returns_false_for_non_matching_password() -> None:
    service = PasswordService()
    hashed = service.hash_password("StrongPassword!123")

    assert service.verify_password("WrongPassword!321", hashed) is False


def test_verify_password_returns_false_for_invalid_hash_format() -> None:
    service = PasswordService()

    assert service.verify_password("StrongPassword!123", "not-a-valid-hash") is False
