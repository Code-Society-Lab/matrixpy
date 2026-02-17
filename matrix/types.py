from dataclasses import dataclass


@dataclass
class File:
    path: str
    filename: str
    mimetype: str


@dataclass
class Image(File):
    height: int
    width: int


@dataclass
class Audio(File):
    duration: int = 0


@dataclass
class Video(File):
    width: int = 0
    height: int = 0
    duration: int = 0
