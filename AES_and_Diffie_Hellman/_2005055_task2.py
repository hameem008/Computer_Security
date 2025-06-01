from _2005055_Diffie_Hellman import *
from sympy import randprime
import time


def average(times):
    return sum(times) / len(times)


def Diffie_Hellman(bit):
    print(f"Average computation time for {bit}-bit:")

    A_times = []
    B_times = []
    shared_key_times = []

    for _ in range(5):
        # Generate a random prime and curve
        P = randprime(2 ** (bit - 1), 2**bit)
        a, b = generate_valid_curve_parameters(P)
        G = find_point_on_curve(a, b, P)
        ka = random.randint(1, P - 1)
        kb = random.randint(1, P - 1)

        # A = ka * G
        start_time = time.time()
        A = scalar_mult(ka, G, a, P)
        A_times.append((time.time() - start_time) * 1000)

        # B = kb * G
        start_time = time.time()
        B = scalar_mult(kb, G, a, P)
        B_times.append((time.time() - start_time) * 1000)

        # Shared key computation
        start_time = time.time()
        shared_key_Alice = scalar_mult(ka, B, a, P)
        shared_key_times.append((time.time() - start_time) * 1000)

        # Verify they match
        shared_key_Bob = scalar_mult(kb, A, a, P)
        assert shared_key_Alice == shared_key_Bob, "Shared keys do not match"

    # Print average results
    print(f"A: {average(A_times):.6f} ms")
    print(f"B: {average(B_times):.6f} ms")
    print(f"Shared key: {average(shared_key_times):.6f} ms\n")


# Run for different key sizes
Diffie_Hellman(128)
Diffie_Hellman(192)
Diffie_Hellman(256)
