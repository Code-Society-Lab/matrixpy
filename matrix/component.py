from html import escape
from abc import ABC, abstractmethod

CELL_TEMPLATE = "<td><strong>{name}</strong><br>{value}</td>"

ROW_TEMPLATE = "<tr>{cells}</tr>"

TABLE_TEMPLATE = "<h2>{title}</h2><table><tbody>{rows}</tbody></table>"


class Component(ABC):
    """Base class for message components."""

    @abstractmethod
    def to_plain_text(self) -> str:
        pass

    @abstractmethod
    def render(self) -> str:
        pass


class Table(Component):
    """A component that renders labeled fields as a table.

    Fields are displayed in rows using the configured number of columns.
    Incomplete rows are padded with empty cells. Field names, values, and the
    table title are HTML-escaped when rendered.
    """

    def __init__(self, *, title: str, column_count: int = 2) -> None:
        if column_count < 1:
            raise ValueError("column_count must be greater than 0")

        self.title: str = title
        self.column_count: int = column_count
        self.fields: list[tuple[str, str]] = []

    def __str__(self) -> str:
        return self.render()

    def add_field(self, name: str, value: str) -> None:
        """Add a labeled field to the table.

        ## Example

        ```python
        table = Table(title="User Info")
        table.add_field("Name", "Astra")
        ```
        """
        self.fields.append((name, value))

    def to_plain_text(self) -> str:
        """Render the table as plain text.

        ## Example

        ```python
        table = Table(title="User Info")
        table.add_field("Name", "Astra")

        result = table.to_plain_text()
        # User Info
        # Name: Astra
        ```
        """
        return "\n".join(
            [self.title, *[f"{name}: {value}" for name, value in self.fields]]
        )

    def render(self) -> str:
        """Render the table as HTML with escaped field content.

        Incomplete rows are padded with empty cells based on the configured
        column count.

        ## Example

        ```python
        table = Table(title="User Info")
        table.add_field("Name", "Astra")
        table.add_field("Role", "Engineer")

        html = table.render()
        ```
        """
        cells = []
        for name, value in self.fields:
            cells.append(
                CELL_TEMPLATE.format(
                    name=escape(name),
                    value=escape(value),
                )
            )

        rows = []
        for i in range(0, len(cells), self.column_count):
            row_cells = cells[i : i + self.column_count]

            while len(row_cells) < self.column_count:
                row_cells.append("<td></td>")

            rows.append(ROW_TEMPLATE.format(cells="".join(row_cells)))

        return TABLE_TEMPLATE.format(
            title=escape(self.title),
            rows="".join(rows),
        )
