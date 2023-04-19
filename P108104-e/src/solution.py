from typing import NamedTuple
class LegoSet(NamedTuple):
    number: int
    name: str
    theme: str
    pieces: int


def from_line(line: str) -> LegoSet:
    tokens = line.split(";")
    return LegoSet(
        tokens[0],
        str(tokens[1]),
        str(tokens[2]),
        tokens[3]
    )

def to_line(lego_set: LegoSet) -> str:
    return f"{lego_set.name} {lego_set.number} {lego_set.pieces} {lego_set.theme}"

def order(lego_sets: list[LegoSet]) -> list[LegoSet]:
    return sorted(
        lego_sets,
        key=lambda lego_set: (-lego_set.pieces, lego_set.theme, lego_set.name,lego_set.number)
    )

def main() -> None:
    legos: list[LegoSet] = []
    while True:
        try:
            line = input()
            legos.append(from_line(line))
        except EOFError:
            break

    ordered_lego_sets =order(legos)
    for lego in ordered_lego_sets:
        print(to_line(lego))


if __name__ == '__main__':
    main()

