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
    def __init__(self, *, title: str, columns: int = 2) -> None:
        self.title: str = title
        self.columns: int = columns
        self.fields: list[tuple[str, str]] = []

    def __str__(self) -> str:
        return self.render()

    def add_field(self, name: str, value: str) -> None:
        self.fields.append((name, value))

    def to_plain_text(self) -> str:
        return "\n".join(
            [self.title, *[f"{name}: {value}" for name, value in self.fields]]
        )

    def render(self) -> str:
        cells = []
        for name, value in self.fields:
            cells.append(
                CELL_TEMPLATE.format(
                    name=escape(name),
                    value=escape(value),
                )
            )

        rows = []
        for i in range(0, len(cells), self.columns):
            row_cells = cells[i : i + self.columns]

            while len(row_cells) < self.columns:
                row_cells.append("<td></td>")

            rows.append(ROW_TEMPLATE.format(cells="".join(row_cells)))

        return TABLE_TEMPLATE.format(
            title=escape(self.title),
            rows="".join(rows),
        )
