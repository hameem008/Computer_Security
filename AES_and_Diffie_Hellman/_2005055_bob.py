import socket
import pickle
from _2005055_AES import *
from _2005055_Diffie_Hellman import *


def start_bob():
    HOST = "localhost"
    PORT = 65432

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print("BOB: Waiting for connection...")
        conn, addr = s.accept()
        with conn:
            print(f"BOB: Connected by {addr}")

            # Receive a, b, G, P, and A = ka * G
            data = conn.recv(4096)
            a, b, G, P, A = pickle.loads(data)

            # Generate Kb and compute B = Kb * G
            kb = random.randint(1, P - 1)
            B = scalar_mult(kb, G, a, P)

            # Send B back to Alice
            conn.sendall(pickle.dumps(B))
            print("BOB: Sent B = Kb * G")

            # Compute shared key
            shared_key = scalar_mult(kb, A, a, P)[0] # taking the x value of the returned point
            # compute round key and inverse round key
            expand_key(shared_key)

            # Notify Alice ready for transmission
            conn.sendall(b"READY")

            # Step 6: Receive AES ciphertext
            ct = conn.recv(4096)
            print("BOB: Received ciphertext")
            # converting to bytes to list
            ct_list = list(ct)

            # Decrypt using shared key
            plaintext = decrypt(ct_list) # parameter of the decrypt must be a list
            print(plaintext)


if __name__ == "__main__":
    start_bob()
