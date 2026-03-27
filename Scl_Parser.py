import json
import sys
from typing import Any, Dict, List, Optional


class ParserError(Exception):
    pass

class Parser:
    def __init__(self, token_file: str):
        self.tokens = self.load_tokens(token_file)
        self.index = 0
        self.current_token = self.tokens[0] if self.tokens else None
        self.symbol_table = set()

    def load_tokens(self, token_file: str) -> List[Dict[str, Any]]:
        try:
            with open(token_file, "r", encoding="utf-8") as file:
                data = json.load(file)
        except FileNotFoundError:
            raise ParserError(f"Error: Token file '{token_file}' not found.")
        except json.JSONDecodeError:
            raise ParserError(f"Error: Token file '{token_file}' is not valid JSON.")

        if not isinstance(data, list):
            raise ParserError("Error: Token file must contain a list of tokens.")

        if not data:
            return [{"type": "EOF", "value": "EOF", "line": -1}]

        # Add EOF token if scanner did not include one
        if data[-1].get("type") != "EOF":
            last_line = data[-1].get("line", -1)
            data.append({"type": "EOF", "value": "EOF", "line": last_line})

        return data

    def getNextToken(self) -> Dict[str, Any]:
        if self.index < len(self.tokens) - 1:
            self.index += 1
            self.current_token = self.tokens[self.index]
        return self.current_token

    def identifierExists(self, identifier: str) -> bool:
        #Check whether an identifier has already been declared.
        return identifier in self.symbol_table

    def begin(self) -> Dict[str, Any]:
        #Entry point for parsing.
        tree = self.program()
        self.expect("EOF", "EOF")
        return tree

    def current_type(self) -> str:
        return self.current_token.get("type", "EOF") if self.current_token else "EOF"

    def current_value(self) -> str:
        return self.current_token.get("value", "EOF") if self.current_token else "EOF"

    def current_line(self) -> int:
        return self.current_token.get("line", -1) if self.current_token else -1

    def expect(self, token_type: str, token_value: Optional[str] = None) -> Dict[str, Any]:
        #Ensure the current token matches what is expected.
        if self.current_token is None:
            raise ParserError(f"Syntax Error: Unexpected end of input.")

        actual_type = self.current_type()
        actual_value = self.current_value()
        actual_line = self.current_line()

        type_matches = actual_type == token_type
        value_matches = token_value is None or actual_value == token_value

        if type_matches and value_matches:
            matched = self.current_token
            self.getNextToken()
            return matched

        expected_desc = token_type if token_value is None else f"{token_type}('{token_value}')"
        raise ParserError(
            f"Syntax Error at line {actual_line}: Expected {expected_desc}, "
            f"but found {actual_type}('{actual_value}')."
        )

    def program(self) -> Dict[str, Any]:
        statements = []

        while self.current_type() != "EOF":
            statements.append(self.statement())

        return {
            "type": "Program",
            "statements": statements
        }

    def statement(self) -> Dict[str, Any]:
        if self.current_type() == "KEYWORD" and self.current_value() == "int":
            return self.declaration()

        if self.current_type() == "KEYWORD" and self.current_value() == "print":
            return self.print_statement()

        if self.current_type() == "IDENTIFIER":
            return self.assignment()

        raise ParserError(
            f"Syntax Error at line {self.current_line()}: Unexpected token "
            f"{self.current_type()}('{self.current_value()}') at start of statement."
        )

    def declaration(self) -> Dict[str, Any]:
        keyword = self.expect("KEYWORD", "int")
        identifier_token = self.expect("IDENTIFIER")
        identifier_name = identifier_token["value"]

        if self.identifierExists(identifier_name):
            raise ParserError(
                f"Syntax Error at line {identifier_token['line']}: "
                f"Variable '{identifier_name}' declared more than once."
            )

        self.symbol_table.add(identifier_name)
        self.expect("SYMBOL", ";")

        return {
            "type": "Declaration",
            "datatype": keyword["value"],
            "identifier": identifier_name,
            "line": keyword["line"]
        }

    def assignment(self) -> Dict[str, Any]:
        identifier_token = self.expect("IDENTIFIER")
        identifier_name = identifier_token["value"]

        if not self.identifierExists(identifier_name):
            raise ParserError(
                f"Syntax Error at line {identifier_token['line']}: "
                f"Variable '{identifier_name}' used before declaration."
            )

        self.expect("OPERATOR", "=")
        expr = self.expression()
        self.expect("SYMBOL", ";")

        return {
            "type": "Assignment",
            "identifier": identifier_name,
            "expression": expr,
            "line": identifier_token["line"]
        }

    def print_statement(self) -> Dict[str, Any]:
        keyword = self.expect("KEYWORD", "print")
        identifier_token = self.expect("IDENTIFIER")
        identifier_name = identifier_token["value"]

        if not self.identifierExists(identifier_name):
            raise ParserError(
                f"Syntax Error at line {identifier_token['line']}: "
                f"Variable '{identifier_name}' used before declaration."
            )

        self.expect("SYMBOL", ";")

        return {
            "type": "Print",
            "identifier": identifier_name,
            "line": keyword["line"]
        }

    def expression(self) -> Dict[str, Any]:
        node = self.term()

        while self.current_type() == "OPERATOR" and self.current_value() in {"+", "-"}:
            operator_token = self.current_token
            self.getNextToken()
            right = self.term()

            node = {
                "type": "BinaryOp",
                "operator": operator_token["value"],
                "left": node,
                "right": right,
                "line": operator_token["line"]
            }

        return node

    def term(self) -> Dict[str, Any]:
        node = self.factor()

        while self.current_type() == "OPERATOR" and self.current_value() in {"*", "/"}:
            operator_token = self.current_token
            self.getNextToken()
            right = self.factor()

            node = {
                "type": "BinaryOp",
                "operator": operator_token["value"],
                "left": node,
                "right": right,
                "line": operator_token["line"]
            }

        return node

    def factor(self) -> Dict[str, Any]:
        if self.current_type() == "IDENTIFIER":
            identifier_token = self.expect("IDENTIFIER")
            identifier_name = identifier_token["value"]

            if not self.identifierExists(identifier_name):
                raise ParserError(
                    f"Syntax Error at line {identifier_token['line']}: "
                    f"Variable '{identifier_name}' used before declaration."
                )

            return {
                "type": "Identifier",
                "name": identifier_name,
                "line": identifier_token["line"]
            }

        if self.current_type() == "NUMBER":
            number_token = self.expect("NUMBER")
            return {
                "type": "Number",
                "value": int(number_token["value"]),
                "line": number_token["line"]
            }

        if self.current_type() == "SYMBOL" and self.current_value() == "(":
            open_paren = self.expect("SYMBOL", "(")
            expr = self.expression()
            self.expect("SYMBOL", ")")
            return {
                "type": "GroupedExpression",
                "expression": expr,
                "line": open_paren["line"]
            }

        raise ParserError(
            f"Syntax Error at line {self.current_line()}: Unexpected token "
            f"{self.current_type()}('{self.current_value()}') in expression."
        )


def save_parse_tree(parse_tree: Dict[str, Any], filename: str = "parse_tree.json") -> None:
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(parse_tree, file, indent=4)
    print(f"Parse tree saved to '{filename}'.")


def print_success_summary(parse_tree: Dict[str, Any]) -> None:
    print("\nPARSER OUTPUT:")
    print("-" * 28)
    print("Parsing completed successfully.")
    print(f"Root node: {parse_tree['type']}")
    print(f"Statements recognized: {len(parse_tree.get('statements', []))}")


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python scl_parser.py tokens.json")
        sys.exit(1)

    token_file = sys.argv[1]

    try:
        parser = Parser(token_file)
        parse_tree = parser.begin()
        print_success_summary(parse_tree)
        save_parse_tree(parse_tree)
    except ParserError as error:
        print(error)
        sys.exit(1)


if __name__ == "__main__":
    main()
