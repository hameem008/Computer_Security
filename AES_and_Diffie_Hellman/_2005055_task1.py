from _2005055_AES import *
import time

key = "Thats my Kung Fu"
expand_key(key)

start_time = time.time()
ciphertext_with_initial_iv = encrypt("We want picnic.")
end_time = time.time()
execution_time = (end_time - start_time) * 1000
print(f"Encryption took {execution_time:.6f} ms")

start_time = time.time()
msz = decrypt(ciphertext_with_initial_iv)
end_time = time.time()
execution_time = (end_time - start_time) * 1000
print(f"Decryption took {execution_time:.6f} ms")
print(msz)

ciphertext_with_initial_iv = encrypt("We want picnic in 2025.")
msz = decrypt(ciphertext_with_initial_iv)
print(msz)
