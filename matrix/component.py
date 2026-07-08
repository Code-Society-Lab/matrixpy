from html import escape
from abc import ABC, abstractmethod


class Component(ABC):
    """Base class for message components."""

    @abstractmethod
    def to_plain_text(self) -> str:
        pass

    @abstractmethod
    def render(self) -> str:
        pass


class MatrixTable(Component):
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
        cells = [f"""
            <td>
                <strong>{escape(name)}</strong><br>
                {escape(value)}
            </td>
            """ for name, value in self.fields]

        rows = ""
        for i in range(0, len(cells), self.columns):
            row_cells = cells[i : i + self.columns]

            while len(row_cells) < self.columns:
                row_cells.append("<td></td>")

            rows += f"<tr>{''.join(row_cells)}</tr>"

        return f"""<blockquote>
    <h2>{escape(self.title)}</h2>
    <table>
        <tbody>
            {rows}
        </tbody>
    </table>
</blockquote>
""".strip()
