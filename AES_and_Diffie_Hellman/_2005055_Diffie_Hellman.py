import random


# Euler’s Criterion
def quadratic_residue(a, p):
    return pow(a, (p - 1) // 2, p)


# Tonelli-Shanks Algorithm
# computes the modular square root of a number n modulo a prime p
def tonelli_shanks(n, p):
    # Step 1: Find Q and S such that p−1 = Q * 2^S, with Q odd
    Q = p - 1
    S = 0
    while Q % 2 == 0:
        Q //= 2
        S += 1

    # Step 2: Find a quadratic non-residue z
    for z in range(2, p):
        if quadratic_residue(z, p) == p - 1:
            break

    # Initialization
    M = S
    c = pow(z, Q, p)
    t = pow(n, Q, p)
    R = pow(n, (Q + 1) // 2, p)

    # Step 3: Loop
    while t != 1:
        i = 0
        temp = t
        while temp != 1:
            temp = pow(temp, 2, p)
            i += 1

        b = pow(c, 2 ** (M - i - 1), p)
        M = i
        c = pow(b, 2, p)
        t = (t * c) % p
        R = (R * b) % p

    return R


# checking for non-singularity of the curve
def is_curve_non_singular(a, b, p):
    is_non_singular = (4 * pow(a, 3, p) + 27 * pow(b, 2, p)) % p
    return is_non_singular != 0


# generate curve parameters a and b
def generate_valid_curve_parameters(p):
    while True:
        a = random.randint(0, p - 1)
        b = random.randint(0, p - 1)
        if is_curve_non_singular(a, b, p):
            return (a, b)


# find a point on the curve
def find_point_on_curve(a, b, p):
    while True:
        x = random.randrange(p)
        y_sq = (x**3 + a * x + b) % p
        if quadratic_residue(y_sq, p) == 1:
            y = tonelli_shanks(y_sq, p)
            return (x, y)


# a^(-1) mod p using Fermat's little theorem
def modinv(a, p):
    return pow(a, -1, p)


def elliptic_add(P, Q, a, p):
    if P == Q:
        # Point doubling
        lam = ((3 * P[0] ** 2 + a) * modinv(2 * P[1], p)) % p
    else:
        # Point addition
        if P[0] == Q[0] and (P[1] + Q[1]) % p == 0:
            return None  # Point at infinity
        lam = ((Q[1] - P[1]) * modinv(Q[0] - P[0], p)) % p

    x_r = (lam**2 - P[0] - Q[0]) % p
    y_r = (lam * (P[0] - x_r) - P[1]) % p
    return (x_r, y_r)


# Scalar multiplication with k and point p
def scalar_mult(k, P, a, p):
    result = None  # Start with point at infinity
    addend = P

    while k > 0:
        if k & 1:
            if result is None:
                result = addend
            else:
                result = elliptic_add(result, addend, a, p)
        addend = elliptic_add(addend, addend, a, p)
        k >>= 1
    return result
