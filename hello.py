def main():
    print(f"Hello from backend! {add(3,9)}")


def add(a: int, b: int) -> int:
    return a + b


if __name__ == "__main__":
    main()
