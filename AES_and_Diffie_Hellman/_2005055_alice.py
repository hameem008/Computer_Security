import socket
import pickle
from _2005055_AES import *
from _2005055_Diffie_Hellman import *
from sympy import randprime


def start_alice():
    HOST = "localhost"
    PORT = 65432

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        print("ALICE: Connected to BOB")

        # Send a, b, G, P, and A = ka * G
        bit = 128
        P = randprime(2 ** (bit - 1), 2**bit)
        param = generate_valid_curve_parameters(P)
        a = param[0]
        b = param[1]
        G = find_point_on_curve(a, b, P)
        ka = random.randint(1, P - 1)
        A = scalar_mult(ka, G, a, P)
        s.sendall(pickle.dumps((a, b, G, P, A)))

        # Receive B from Bob
        B = pickle.loads(s.recv(4096))
        print("ALICE: Received B = Kb * G")

        # Compute shared key
        shared_key = scalar_mult(ka, B, a, P)[
            0
        ]  # taking the x value of the returned point
        # compute round key and inverse round key
        expand_key(shared_key)

        # Wait for Bob's ready signal
        ready = s.recv(1024)
        if ready == b"READY":
            print("ALICE: Bob is ready, sending ciphertext")

            # Encrypt message with AES
            message = "hello bob"
            ciphertext = encrypt(message)
            # ciphertext is a list, needs to be converted
            s.sendall(bytes(ciphertext))


if __name__ == "__main__":
    start_alice()
