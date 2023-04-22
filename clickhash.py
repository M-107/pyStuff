import click
import hashlib

algos = {
    "sha1": "sha1",
    "sha256": "sha256",
    "sha512": "sha512",
    "md5": "md5",
}


def input_file_option(prompt):
    return click.option(
        "--input-file", "-if",
        required=True,
        type=click.File(mode="rb"),
        help="Path to file for hashing",
        prompt=prompt,
    )


def algorithm_option(prompt):
    return click.option(
        "--algorithm", "-a",
        required=True,
        type=click.Choice(algos.keys(), case_sensitive=False),
        help="The type of hashing algorithm used",
        prompt=prompt,
    )


@click.group()
def cli():
    pass


@click.command()
@input_file_option("File to be hashed")
@algorithm_option("Hash algorithm to use")
def get_hash(input_file, algorithm):
    hasher = getattr(hashlib, algos[algorithm])()
    for chunk in iter(lambda: input_file.read(4096), b""):
        hasher.update(chunk)
    click.echo(hasher.hexdigest())


@click.command()
@input_file_option("File to be checked")
@algorithm_option("Hash algorithm to use")
@click.option(
    "--hash-value", "-h",
    required=True,
    type=click.STRING,
    help="Hash value to check against",
    prompt="Hash value to check",
)
def check_hash(input_file, algorithm, hash_value):
    hasher = getattr(hashlib, algos[algorithm])()
    for chunk in iter(lambda: input_file.read(4096), b""):
        hasher.update(chunk)
    if hasher.hexdigest() == hash_value:
        click.echo("Hash matched!")
    else:
        click.echo("Hash did not match.")


cli.add_command(get_hash)
cli.add_command(check_hash)

if __name__ == '__main__':
    cli()
