from _2005055_sbox_mixer import *
import os


def plaintext_to_hex_list(plaintext):
    return [ord(c) for c in plaintext]


def hex_list_to_plaintext(hex_list):
    return "".join(chr(b) for b in hex_list)


# List must contain exactly 16 elements.
def hex_list_to_hex_matrix(lst):
    return [lst[i * 4 : (i + 1) * 4] for i in range(4)]


def hex_matrix_to_hex_list(matrix):
    return [matrix[i][j] for i in range(4) for j in range(4)]


# print a list in hex
def print_hex_list(list):
    print("[", end=" ")
    for val in list:
        print(f"{val:02x}", end=" ")
    print("]")


# print a matrix in hex
def print_hex_matrix(matrix):
    for row in matrix:
        print_hex_list(row)


# transposing a 4 * 4 matrix
def get_transposed_matrix(matrix):
    transposed = [[matrix[j][i] for j in range(4)] for i in range(4)]
    return transposed


# Both lists must have the same length.
def xor_of_2_list(list1, list2):
    return [a ^ b for a, b in zip(list1, list2)]


# XOR of two matrices using XOR of two lists
def xor_of_2_matrix(matrix1, matrix2):
    return [xor_of_2_list(row1, row2) for row1, row2 in zip(matrix1, matrix2)]


# left shift a list
def left_shift_a_list(list, n):
    return list[n:] + list[:n]


# right shift a list
def right_shift_a_list(list, n):
    return list[-n:] + list[:-n]


# galois field multiplication
def gf_mul(a, b):
    p = 0
    for i in range(8):
        if b & 1:
            p ^= a
        hi_bit_set = a & 0x80
        a = (a << 1) & 0xFF
        if hi_bit_set:
            a ^= 0x1B
        b >>= 1
    return p


# Round number must be between 1 and 10
def get_round_constant(round_num):
    rcon = [1]  # Start with 0x01
    for _ in range(1, 10):
        rcon.append(gf_mul(rcon[-1], 2))
    return rcon[round_num - 1]


def substitute_a_list_with_sbox(list):
    return [Sbox[b] for b in list]


def substitute_a_matrix_with_sbox(matrix):
    return [substitute_a_list_with_sbox(row) for row in matrix]


def substitute_a_list_with_inv_sbox(list):
    return [InvSbox[b] for b in list]


def substitute_a_matrix_with_inv_sbox(matrix):
    return [substitute_a_list_with_inv_sbox(row) for row in matrix]


def g(input_list, round_no):
    # Left circular shift by 1
    shifted = left_shift_a_list(input_list, 1)
    # Substitution using S-box
    substituted = substitute_a_list_with_sbox(shifted)
    xor_with = [get_round_constant(round_no), 0, 0, 0]
    # XOR
    result = [a ^ b for a, b in zip(substituted, xor_with)]
    return result


def mix_column(matrix):
    result = [[0 for _ in range(4)] for _ in range(4)]
    for i in range(4):
        for j in range(4):
            for k in range(4):
                result[i][j] ^= gf_mul(Mixer[i][k], matrix[k][j])
    return result


def inv_mix_column(matrix):
    result = [[0 for _ in range(4)] for _ in range(4)]
    for i in range(4):
        for j in range(4):
            for k in range(4):
                result[i][j] ^= gf_mul(InvMixer[i][k], matrix[k][j])
    return result


# divide the message into blocks and use PKCS#7 padding
def message_processor(message):
    blocks = []
    block_size = 16
    input_bytes = plaintext_to_hex_list(message)
    total_len = len(input_bytes)
    num_blocks = (total_len + block_size - 1) // block_size

    # dividing the message into blocks
    for i in range(num_blocks):
        block = input_bytes[i * block_size : (i + 1) * block_size]
        if len(block) < block_size:
            pad_len = block_size - len(block)
            block += [pad_len] * pad_len
        blocks.append(block)

    # Multiple of block_size(16) and needs an extra block
    if total_len % block_size == 0:
        blocks.append([block_size] * block_size)

    return blocks


# removing the PKCS#7 padding
def remove_pkcs7_padding(plaintext):
    pad_len = plaintext[-1]
    return plaintext[:-pad_len]


# return the hex of the key
def key_processor(key):
    if isinstance(key, str):
        key_bytes = [ord(c) for c in key]
    elif isinstance(key, int):
        key_bytes = list(key.to_bytes(16, byteorder="big"))
    elif isinstance(key, (bytes, bytearray)):
        key_bytes = list(key)

    # Pad or truncate to 16 bytes
    if len(key_bytes) < 16:
        key_bytes += [0x01] * (16 - len(key_bytes))
    elif len(key_bytes) > 16:
        key_bytes = key_bytes[:16]

    return key_bytes


# generate random iv
def get_random_iv():
    return list(os.urandom(16))


# this array is for storing all the round keys, dimention -> [11][4][4]
round_keys = [[[0x00 for _ in range(4)] for _ in range(4)] for _ in range(11)]
inv_round_keys = [[[0x00 for _ in range(4)] for _ in range(4)] for _ in range(11)]


# the keys are stored in row major
def compute_all_keys():
    for i in range(1, 11):
        round_keys[i][0] = xor_of_2_list(
            round_keys[i - 1][0], g(round_keys[i - 1][3], i)
        )
        inv_round_keys[i][0] = xor_of_2_list(
            inv_round_keys[i - 1][0], g(inv_round_keys[i - 1][3], i)
        )
        for j in range(1, 4):
            round_keys[i][j] = xor_of_2_list(round_keys[i][j - 1], round_keys[i - 1][j])
            inv_round_keys[i][j] = xor_of_2_list(
                inv_round_keys[i][j - 1], inv_round_keys[i - 1][j]
            )
    inv_round_keys.reverse()


# expanding all keys for both encryption and decryption
def expand_key(key):
    # padding or discarding key
    key_hex_list = key_processor(key)
    # initializing the round 0 key
    # initializing the keys
    round_keys[0] = hex_list_to_hex_matrix(key_hex_list)
    inv_round_keys[0] = hex_list_to_hex_matrix(key_hex_list)
    compute_all_keys()


# encrypt a block
def encrypt_a_block(message_hex_list):
    state_matrix = hex_list_to_hex_matrix(message_hex_list)
    # round 0
    state_matrix = get_transposed_matrix(state_matrix)
    state_matrix = xor_of_2_matrix(state_matrix, get_transposed_matrix(round_keys[0]))
    # round 1 to 10
    for r in range(1, 11):
        # Sub Bytes
        state_matrix = substitute_a_matrix_with_sbox(state_matrix)
        # Shift Rows
        for i in range(4):
            state_matrix[i] = left_shift_a_list(state_matrix[i], i)
        # Mix Columns:
        if r != 10:  # no mix column step in round 10
            state_matrix = mix_column(state_matrix)
        # Add Round Key
        state_matrix = xor_of_2_matrix(
            state_matrix, get_transposed_matrix(round_keys[r])
        )
    # as the matrix was in column major
    state_matrix = get_transposed_matrix(state_matrix)
    ciphertext = hex_matrix_to_hex_list(state_matrix)
    return ciphertext


def encrypt(message):
    initial_iv = get_random_iv()
    current_iv = initial_iv
    blocks = message_processor(message)
    ciphertext = []
    for b in blocks:
        current_iv = encrypt_a_block(xor_of_2_list(b, current_iv))
        ciphertext += current_iv
    return initial_iv + ciphertext


def decrypt_a_block(ciphertext, iv):
    # round 0
    state_matrix = hex_list_to_hex_matrix(ciphertext)
    state_matrix = get_transposed_matrix(state_matrix)
    # Add Round Key
    state_matrix = xor_of_2_matrix(
        state_matrix, get_transposed_matrix(inv_round_keys[0])
    )
    # round 1 to 10
    for r in range(1, 11):
        # Inverse Shift Rows
        for i in range(4):
            state_matrix[i] = right_shift_a_list(state_matrix[i], i)
        # Inserse Sub Bytes
        state_matrix = substitute_a_matrix_with_inv_sbox(state_matrix)
        # Add ROund Key
        state_matrix = xor_of_2_matrix(
            state_matrix, get_transposed_matrix(inv_round_keys[r])
        )
        # Inverse Mix Column
        if r != 10:
            state_matrix = inv_mix_column(state_matrix)
    state_matrix = get_transposed_matrix(state_matrix)
    # Removing the iv
    plaintext = xor_of_2_list(hex_matrix_to_hex_list(state_matrix), iv)
    return plaintext


def decrypt(ciphertext_with_iv):
    # Separating the key
    iv = ciphertext_with_iv[:16]
    # Dividing into blocks
    blocks = [
        ciphertext_with_iv[i : i + 16] for i in range(16, len(ciphertext_with_iv), 16)
    ]

    plaintext = []
    for b in blocks:
        # Decrypt one block, then XOR with IV
        decrypted = decrypt_a_block(b, iv)
        plaintext += decrypted
        # this block will be IV for the next block
        iv = b

    plaintext = remove_pkcs7_padding(plaintext)
    return hex_list_to_plaintext(plaintext)
