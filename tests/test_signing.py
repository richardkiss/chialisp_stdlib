from os import PathLike
from typing import List

import tempfile

from chia_base.bls12_381 import BLSSecretExponent  # type: ignore
from clvm_rs import Program  # type: ignore
from chialisp_puzzles import load_puzzle

import clvm_tools_rs  # type: ignore

from chialisp_stdlib import NIGHTLY_INCLUDE_DIRECTORY, STABLE_INCLUDE_DIRECTORY

Program.set_run_unsafe_max_cost(1 << 31)

INCLUDES = [NIGHTLY_INCLUDE_DIRECTORY, STABLE_INCLUDE_DIRECTORY]


def compile_clsp(program_str: str, search_paths: List[PathLike]) -> Program:
    """
    This is a bit of a mess.
    """
    in_file = tempfile.NamedTemporaryFile("w")
    out = tempfile.NamedTemporaryFile()
    in_file.write(program_str)
    in_file.flush()
    clvm_tools_rs.compile_clvm(
        in_file.name, out.name, search_paths=[str(_) for _ in search_paths]
    )
    with open(out.file.name, "r") as f:
        blob = f.read()
    return Program.fromhex(blob)


def eval(s: str) -> Program:
    return compile_clsp(f'(mod X (include "signing.clinc") {s})', INCLUDES).run(0)


PK1 = BLSSecretExponent.from_int(1).public_key()
PK1_HEX = bytes(PK1).hex()

PK2 = BLSSecretExponent.from_int(2).public_key()
PK2_HEX = bytes(PK2).hex()


def test_add_public_keys():
    # example usage
    r = eval("(+ 1 50)")
    assert int(r) == 51

    t = eval(f"(add_public_keys 0x{PK1_HEX} 0x{PK2_HEX})")
    assert t.atom == bytes(PK1 + PK2)


def test_add_signatures():
    se1 = BLSSecretExponent.from_int(1)
    sig1 = se1.sign(message=b"foo")
    sig2 = se1.sign(message=b"bar")
    sig1_int = int(Program.to(sig1))
    sig2_int = int(Program.to(sig2))
    t1 = eval(f"(add_signatures {sig1_int} {sig2_int})")
    total = sig1.from_bytes(t1.atom)
    assert total == sig1 + sig2


def test_signer():
    msg = b"foo"
    msg_s = msg.decode()
    for se_int in [1, 2, (1 << 256) - 891]:
        se = BLSSecretExponent.from_int(se_int)
        se_pub = se.public_key()
        t = eval(f'(signer {se_int} "{msg_s}")')
        sig = se.sign(message=msg)
        assert bytes(sig) == t.atom
        assert bytes(sig) == t.atom
        assert sig.verify(hash_key_pairs=[(se_pub, msg)])


def test_partial_signer():
    se_offset_int = 20000
    se_offset = BLSSecretExponent.from_int(se_offset_int)
    se_offset_pub = se_offset.public_key()

    msg = b"foo"
    msg_s = msg.decode()
    for se_int in [1, 2, (1 << 256) - 891]:
        se = BLSSecretExponent.from_int(se_int)
        se_pub = se.public_key()
        final_public_key = se_pub + se_offset_pub
        sig_offset = se_offset.sign(msg, final_public_key=final_public_key)
        t = eval(
            f'(partial_signer {se_offset_int} 0x{bytes(final_public_key).hex()} "{msg_s}")'
        )
        assert t.atom.hex() == bytes(sig_offset).hex()
        t = eval(
            f'(partial_signer {se_int} 0x{bytes(final_public_key).hex()} "{msg_s}")'
        )
        sig = se.sign(msg, final_public_key=final_public_key)
        assert t.atom.hex() == bytes(sig).hex()
        total_sig = sig_offset + sig
        assert total_sig.verify(hash_key_pairs=[(final_public_key, msg)])


def test_standard_puzzle():
    t = eval(f"(standard_puzzle 0x{PK1_HEX})")
    p2_d = load_puzzle("p2_delegated_puzzle_or_hidden_puzzle")
    curried = p2_d.curry(bytes(PK1))
    assert t.tree_hash() == curried.tree_hash()
    assert t == curried


def test_standard_puzzle_hash():
    p2_d = load_puzzle("p2_delegated_puzzle_or_hidden_puzzle")
    curried = p2_d.curry(bytes(PK1))
    hashed_pubkey_hex = Program.to(PK1).tree_hash().hex()
    t = eval(f"(standard_puzzle_hash 0x{hashed_pubkey_hex})")
    assert t.atom == curried.tree_hash()


def test_standard_puzzle_solution_maker():
    # (defun standard_puzzle_solution_maker (conditions private_key)
    # make a standard puzzle (which we've already tested)
    # come up with a bogus list of conditions
    # call this
    # run the puzzle with the results of this
    # compare to conditions

    std_puzzle = load_puzzle("p2_delegated_puzzle_or_hidden_puzzle").curry(PK1)
    conditions = Program.to(["hello", [1, 2, 3, 4], "goodbye"])
    conditions_text = "('hello' (1 2 3 4) 'goodbye')"
    t = eval(f"(standard_puzzle_solution_maker (q . {conditions_text}) 1)")
    solution, signature_program = t.pair
    r = std_puzzle.run(solution)
    print(r)
    assert r.pair[1] == conditions
    inner_puzzle = Program.to((1, conditions))
    qcth = inner_puzzle.tree_hash()
    expected_sig_condition = Program.to([50, PK1, qcth])
    assert r.pair[0] == expected_sig_condition

    sig1 = BLSSecretExponent.from_int(1).sign(b"foo")
    signature = sig1.from_bytes(signature_program.atom)
    assert signature.verify(hash_key_pairs=[(PK1, qcth)])
