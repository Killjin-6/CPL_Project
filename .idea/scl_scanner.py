import sys
import json
import re

# ---------- Token Definitions ----------

KEYWORDS = {"int", "print", "if", "else", "while", "return"}

OPERATORS = {"+", "-", "*", "/", "=", "==", "!=", "<", ">", "<=", ">="}

SYMBOLS = {";", "(", ")", "{", "}", ","}


# ---------- Token Class ----------

class Token:
    def __init__(self, type, value, line):
        self.type = type
        self.value = value
        self.line = line

    def to_dict(self):
        return {
            "type": self.type,
            "value": self.value,
            "line": self.line
        }


# ---------- Scanner ----------

def scan_file(filename):

    tokens = []
    identifiers = set()

    with open(filename, "r") as file:
        lines = file.readlines()

    for line_number, line in enumerate(lines, 1):

        words = re.findall(r'==|!=|<=|>=|\w+|[+\-*/=;(){}<>,]', line)

        for word in words:

            if word in KEYWORDS:
                tokens.append(Token("KEYWORD", word, line_number))

            elif word in OPERATORS:
                tokens.append(Token("OPERATOR", word, line_number))

            elif word in SYMBOLS:
                tokens.append(Token("SYMBOL", word, line_number))

            elif word.isdigit():
                tokens.append(Token("NUMBER", word, line_number))

            elif word.isidentifier():
                tokens.append(Token("IDENTIFIER", word, line_number))
                identifiers.add(word)

            else:
                print(f"Lexical Error at line {line_number}: Invalid token '{word}'")

    return tokens, list(identifiers)


# ---------- Output ----------

def save_tokens_json(tokens, output_file="tokens.json"):

    token_dicts = [token.to_dict() for token in tokens]

    with open(output_file, "w") as f:
        json.dump(token_dicts, f, indent=4)


def print_tokens(tokens):

    print("\nTOKENS:")
    print("----------------------------")

    for token in tokens:
        print(f"{token.type:12} {token.value:10} line {token.line}")


# ---------- Main ----------

def main():

    if len(sys.argv) != 2:
        print("Usage: python scl_scanner.py filename.scl")
        return

    filename = sys.argv[1]

    tokens, identifiers = scan_file(filename)

    print_tokens(tokens)

    save_tokens_json(tokens)

    print("\nIdentifiers Table:")
    print(identifiers)

    print("\nJSON file 'tokens.json' created.")


if __name__ == "__main__":
    main()
