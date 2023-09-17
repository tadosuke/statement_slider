import argparse
import ast
import astor
from collections import defaultdict

from collections import defaultdict
import ast
import astor


class VarRearranger:

    def __init__(self, func_node: ast.FunctionDef):
        self.func_node = func_node

    def find_and_rearrange_vars(self) -> list[ast.stmt]:
        var_to_decl = self._find_var_declarations()
        var_to_first_use = self._find_var_first_use(var_to_decl)
        copied = self._copy_var_declarations_to_first_use(var_to_first_use, var_to_decl)
        new_body = self._delete_duplicated_state(copied)

        return new_body

    def _find_var_declarations(self) -> dict[str, ast.Assign]:
        var_to_decl = {}
        for stmt in self.func_node.body:
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if isinstance(target, ast.Name):
                        var_to_decl[target.id] = stmt
        return var_to_decl

    def _find_var_first_use(self, var_to_decl: dict[str, ast.Assign]) -> dict[str, int]:
        var_to_first_use = defaultdict(int)
        for i, stmt in enumerate(self.func_node.body):
            for node in ast.walk(stmt):
                if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                    var_name = node.id
                    if var_name not in var_to_first_use and var_name in var_to_decl:
                        var_to_first_use[var_name] = i
        return var_to_first_use

    def _copy_var_declarations_to_first_use(
            self,
            var_to_first_use: dict[str, int],
            var_to_decl: dict[str, ast.Assign]) -> list[ast.stmt]:
        new_body = []
        for i, stmt in enumerate(self.func_node.body):
            to_insert = [var_to_decl[var] for var in var_to_first_use.keys() if var_to_first_use[var] == i]
            new_body.extend(to_insert)
            new_body.append(stmt)
        return new_body

    def _delete_duplicated_state(self, copied_body: list[ast.stmt]) -> list[ast.stmt]:
        seen_statements = {}
        to_remove = set()
        for i, stmt in enumerate(copied_body):
            stmt_str = astor.to_source(stmt).strip()
            if stmt_str in seen_statements:
                to_remove.add(seen_statements[stmt_str])
            else:
                seen_statements[stmt_str] = i
        new_body = [stmt for i, stmt in enumerate(copied_body) if i not in to_remove]
        return new_body


def main():
    parser = argparse.ArgumentParser(description='Delete duplicated statements in a Python function.')
    parser.add_argument('file', type=str, help='The Python file to process.')
    parser.add_argument('func', type=str, help='The name of the function to process.')

    args = parser.parse_args()

    with open(args.file, 'r') as f:
        code = f.read()

    tree = ast.parse(code)
    func_node = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == args.func][0]
    func_node.body = VarRearranger(func_node).find_and_rearrange_vars()

    with open(args.file, 'w') as f:
        f.write(astor.to_source(tree))


if __name__ == '__main__':
    main()