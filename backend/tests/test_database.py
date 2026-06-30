import pytest
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import RuleORM


@pytest.mark.asyncio
async def test_database_connection_succeeds(db_session: AsyncSession):
    result = await db_session.execute(text("SELECT 1"))
    assert result.scalar() == 1


@pytest.mark.asyncio
async def test_can_insert_and_retrieve_rule(db_session: AsyncSession):
    rule = RuleORM(
        rule_number="999.99",
        section_title="Test Section",
        rule_text="Test rule text.",
        full_text="Test rule text.",
    )
    db_session.add(rule)
    await db_session.flush()

    result = await db_session.execute(select(RuleORM).where(RuleORM.rule_number == "999.99"))
    fetched = result.scalar_one_or_none()
    assert fetched is not None
    assert fetched.rule_text == "Test rule text."
    assert fetched.created_at is not None


@pytest.mark.asyncio
async def test_rule_number_is_unique(db_session: AsyncSession):
    from sqlalchemy.exc import IntegrityError

    rule1 = RuleORM(
        rule_number="999.98",
        section_title="A",
        rule_text="Text 1.",
        full_text="Text 1.",
    )
    db_session.add(rule1)
    await db_session.flush()

    rule2 = RuleORM(
        rule_number="999.98",
        section_title="B",
        rule_text="Text 2.",
        full_text="Text 2.",
    )
    db_session.add(rule2)
    with pytest.raises(IntegrityError):
        await db_session.flush()


@pytest.mark.asyncio
async def test_query_all_rules_returns_count(db_session: AsyncSession):
    rules = [
        RuleORM(
            rule_number=f"900.{i}",
            section_title="Test",
            rule_text=f"Rule {i}",
            full_text=f"Rule {i}",
        )
        for i in range(3)
    ]
    for r in rules:
        db_session.add(r)
    await db_session.flush()

    result = await db_session.execute(select(RuleORM).where(RuleORM.rule_number.like("900.%")))
    fetched = result.scalars().all()
    assert len(fetched) == 3
