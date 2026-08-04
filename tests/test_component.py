import pytest
from matrix.component import Table


@pytest.fixture
def table():
    return Table(title="User Info")


@pytest.mark.parametrize("column_count", [0, -1, -10])
def test_init__when_column_count_is_less_than_one__expect_value_error(
    column_count: int,
) -> None:
    with pytest.raises(
        ValueError,
        match="column_count must be greater than 0",
    ):
        Table(title="User Info", column_count=column_count)


def test_init__when_column_count_is_one__expect_column_count_set() -> None:
    table = Table(title="User Info", column_count=1)

    assert table.column_count == 1


def test_to_plain_text__expect_title_and_fields(table):
    table.add_field("Name", "Astra")
    table.add_field("Role", "Engineer")

    result = table.to_plain_text()

    assert result == "User Info\nName: Astra\nRole: Engineer"


def test_to_plain_text__with_no_fields__expect_title_only(table):
    result = table.to_plain_text()

    assert result == "User Info"


def test_render__expect_html_table(table):
    table.add_field("Name", "Astra")
    table.add_field("Role", "Engineer")

    result = table.render()

    assert "<h2>User Info</h2>" in result
    assert "<table>" in result
    assert "<strong>Name</strong>" in result
    assert "Astra" in result
    assert "<strong>Role</strong>" in result
    assert "Engineer" in result


def test_render__with_odd_number_of_fields__expect_empty_padding_cell(table):
    table.add_field("Name", "Astra")
    table.add_field("Role", "Engineer")
    table.add_field("Location", "CA")

    result = table.render()

    assert result.count("<tr>") == 2
    assert result.count("<td>") == 4
    assert result.count("<td></td>") == 1
    assert result.count("<strong>") == 3


def test_render__with_custom_columns__expect_rows_grouped_by_column_count():
    table = Table(title="User Info", column_count=3)
    table.add_field("Name", "Astra")
    table.add_field("Role", "Engineer")
    table.add_field("Location", "CA")
    table.add_field("Status", "Active")

    result = table.render()

    assert result.count("<tr>") == 2
    assert result.count("<td>") == 6
    assert result.count("<td></td>") == 2
    assert result.count("<strong>") == 4


def test_render__with_html_content__expect_escaped_html():
    table = Table(title="<User Info>")
    table.add_field("<Name>", "<Astra & Co>")

    result = table.render()

    assert "&lt;User Info&gt;" in result
    assert "&lt;Name&gt;" in result
    assert "&lt;Astra &amp; Co&gt;" in result

    assert "<User Info>" not in result
    assert "<Name>" not in result
    assert "<Astra & Co>" not in result


def test_str__expect_rendered_html(table):
    table.add_field("Name", "Astra")

    assert str(table) == table.render()
