import json
import sys

class ExecutorError(Exception):
    pass

class Executor:
    def __init__(self, parse_tree_file):
        self.parse_tree = self.load_parse_tree(parse_tree_file)
        self.memory = {}
        self.output_lines = []

    def load_parse_tree(self, parse_tree_file):
        try:
            with open(parse_tree_file, "r", encoding="utf-8") as file:
                return json.load(file)
        except FileNotFoundError:
            raise ExecutorError(f"Error: Parse tree file '{parse_tree_file}' not found.")
        except json.JSONDecodeError:
            raise ExecutorError(f"Error: Parse tree file '{parse_tree_file}' is not valid JSON.")

    def run(self):
        if self.parse_tree.get("type") != "Program":
            raise ExecutorError("Runtime Error: Parse tree root must be Program.")

        print("\nEXECUTOR OUTPUT:")
        print("-" * 28)

        for statement in self.parse_tree.get("statements", []):
            self.execute_statement(statement)

        self.save_output()

    def execute_statement(self, statement):
        statement_type = statement.get("type")

        if statement_type == "Declaration":
            self.execute_declaration(statement)

        elif statement_type == "Assignment":
            self.execute_assignment(statement)

        elif statement_type == "Print":
            self.execute_print(statement)

        else:
            raise ExecutorError(f"Runtime Error: Unknown statement type '{statement_type}'.")

    def execute_declaration(self, statement):
        name = statement.get("identifier")

        if name in self.memory:
            raise ExecutorError(f"Runtime Error: Variable '{name}' already exists.")

        # Integers default to 0 until assigned a value.
        self.memory[name] = 0

    def execute_assignment(self, statement):
        name = statement.get("identifier")

        if name not in self.memory:
            raise ExecutorError(f"Runtime Error: Variable '{name}' was not declared.")

        value = self.evaluate_expression(statement.get("expression"))
        self.memory[name] = value

    def execute_print(self, statement):
        name = statement.get("identifier")

        if name not in self.memory:
            raise ExecutorError(f"Runtime Error: Variable '{name}' was not declared.")

        output = str(self.memory[name])
        print(output)
        self.output_lines.append(output)

    def evaluate_expression(self, node):
        node_type = node.get("type")

        if node_type == "Number":
            return node.get("value")

        if node_type == "Identifier":
            name = node.get("name")

            if name not in self.memory:
                raise ExecutorError(f"Runtime Error: Variable '{name}' was not declared.")

            return self.memory[name]

        if node_type == "GroupedExpression":
            return self.evaluate_expression(node.get("expression"))

        if node_type == "BinaryOp":
            left = self.evaluate_expression(node.get("left"))
            right = self.evaluate_expression(node.get("right"))
            operator = node.get("operator")

            if operator == "+":
                return left + right
            if operator == "-":
                return left - right
            if operator == "*":
                return left * right
            if operator == "/":
                if right == 0:
                    raise ExecutorError("Runtime Error: Division by zero.")
                return left // right

            raise ExecutorError(f"Runtime Error: Unknown operator '{operator}'.")

        raise ExecutorError(f"Runtime Error: Unknown expression type '{node_type}'.")

    def save_output(self):
        with open("execution_output.txt", "w", encoding="utf-8") as file:
            for line in self.output_lines:
                file.write(line + "\n")

        print("\nExecution completed successfully.")
        print("Output saved to 'execution_output.txt'.")
        print("Final Memory State:")
        print(self.memory)


def main():
    if len(sys.argv) != 2:
        print("Usage: python scl_executor.py parse_tree.json")
        sys.exit(1)

    parse_tree_file = sys.argv[1]

    try:
        executor = Executor(parse_tree_file)
        executor.run()
    except ExecutorError as error:
        print(error)
        sys.exit(1)


if __name__ == "__main__":
    main()