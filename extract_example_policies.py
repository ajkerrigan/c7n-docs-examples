from pathlib import Path

import click
import docutils.frontend
import docutils.nodes
import docutils.parsers.rst
import docutils.utils
import yaml
from c7n.config import Config
from c7n.exceptions import PolicyValidationError
from c7n.policy import Policy, PolicyCollection
from c7n.resources import load_available
from loguru import logger
from yaml.parser import ParserError
from yaml.scanner import ScannerError


class CodeBlockVisitor(docutils.nodes.GenericNodeVisitor):
    def __init__(self, document, target_dir):
        super().__init__(document)
        if not target_dir.exists():
            target_dir.mkdir(parents=True)
        self.target_dir = target_dir

    def _dump_collection(self, data, text):
        """
        If `data` represents a collection of valid Cloud Custodian
        policies, dump `text` to a file based on the name of the first
        policy in the collection.
        """
        try:
            collection = PolicyCollection.from_data(data, Config.empty())
            if collection:
                path = self.target_dir / f"{collection.policies[0].name}.yml"
                path.write_text(text)
                return True
        except PolicyValidationError as err:
            logger.warning(f"Unable to load policy collection: {err}")
        except AttributeError:
            pass

    def _dump_policy(self, data, text):
        """
        If `data` represents a valid Cloud Custodian policy,
        write `text` to a file based on the policy name.
        """
        try:
            policy = Policy(data, Config.empty())
            path = self.target_dir / f"{policy.name}.yml"
            path.write_text(f"policies:\n{text}")
            return True
        except (AssertionError, PolicyValidationError) as err:
            logger.warning(f"Unable to load policy data: {err}")

    def visit_literal_block(self, node):
        """
        If a `code-block` directive contains a valid Cloud Custodian
        policy or policy collection, infer a reasonable file name
        and write the policy data to it.

        To avoid mangled formatting, output raw policy text rather
        than loading and dumping YAML. Use parsed YAML only for
        validation.
        """
        try:
            y = yaml.safe_load(node.rawsource)
        except (ParserError, ScannerError):
            logger.info("Unable to load YAML, moving on...")
            return

        self._dump_collection(y, node.rawsource) or self._dump_policy(y, node.rawsource)

    def default_visit(self, node):
        pass


def _get_target_dir(full_path, base_path):
    """
    Given a file path and base path:

    1. Determine the parent directory's path relative to the base
    2. Trim out any directory segments containing the word "example"
    3. Return the trimmed path relative to the current directory

    Example:

    >>> _get_target_dir(
    ...     '/src/cloud-custodian/docs/source/aws/examples/policy.rst',
    ...     '/src/cloud-custodian/docs/source'
    ... )
    PosixPath('aws')
    """

    relative_dir = Path(full_path).relative_to(base_path).parent
    trimmed_parts = (p for p in relative_dir.parts if "example" not in p)
    return Path().joinpath(*trimmed_parts)


@click.argument("base_dir", type=click.Path(file_okay=False, dir_okay=True))
@click.command()
def cli(base_dir):
    """
    Look inside BASE_DIR and its children for an `examples`
    directory containing reStructuredText (.rst) files.

    For any examples policies defined inside `code-block`
    directives, validate and write the policies to .yml
    files under the current directory.
    """
    default_settings = docutils.frontend.OptionParser(
        components=(docutils.parsers.rst.Parser,)
    ).get_default_values()
    parser = docutils.parsers.rst.Parser()
    pattern = "**/examples/*.rst"

    for f in Path(base_dir).glob(pattern):
        logger.info(f"Extracting {f.name}...")
        document = docutils.utils.new_document(f.name, default_settings)
        parser.parse(f.read_text(), document)
        target_dir = _get_target_dir(f, base_dir)
        visitor = CodeBlockVisitor(document, target_dir)
        document.walk(visitor)


if __name__ == "__main__":
    load_available()
    cli()
