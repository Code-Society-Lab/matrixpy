from dataclasses import dataclass


@dataclass
class File:
    path: str
    filename: str
    mimetype: str


@dataclass
class Image:
    path: str
    filename: str
    mimetype: str
