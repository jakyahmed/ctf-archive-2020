#!/usr/bin/env python

import string
from Crypto.Cipher import AES
import random
from pwn import *


class Exploit(object):
  def __init__(self, ip, port):
    self.IP = ip
    self.PORT = port
    self.conn = remote(self.IP, self.PORT)
    self.recovered_plaintext = list()
    self.forged_ciphertext = list()
    self.BLOCK_SIZE = 16
    self.list_string = string.ascii_letters + string.digits

  def set_original_safe_identity(self, safe_identity):
    # pecah setiap blok
    self.original_safe_identity = list()
    for i in range(0, len(safe_identity), self.BLOCK_SIZE):
      self.original_safe_identity.append(safe_identity[i:i+self.BLOCK_SIZE])

    return True


  def set_target_plaintext(self, target_plaintext):
    target_plaintext = self.pad(target_plaintext)
    self.target_plaintext = list()
    for i in range(0, len(target_plaintext), self.BLOCK_SIZE):
      self.target_plaintext.append(target_plaintext[i:i+self.BLOCK_SIZE])

    return True


  def get_initial_safe_identity(self):
    self.conn.sendlineafter("Choice : ", "1")
    self.conn.sendlineafter("Username : ", "A")
    self.conn.sendlineafter("UID : ", "1")
    self.conn.sendlineafter("Role : ", "A")
    orig_safe_identity = self.conn.recvline().split(": ")[1][:-1]
    self.set_original_safe_identity(orig_safe_identity.decode("hex"))


  def find_per_char(self, random_sequence, padded_sequence, target_block, byte_pad):
    for brute_byte in map(chr, range(0x100)):
      payload = random_sequence + brute_byte + padded_sequence + target_block
      payload = payload.encode("hex")
      self.conn.sendlineafter("Choice : ", "2")
      self.conn.sendlineafter("(in hex) : ", payload)
      hasil = self.conn.recvuntil("1.) Send")

      if "Error slurrrr" not in hasil:
        tmp_chr_intermediate = chr(ord(brute_byte) ^ (byte_pad))
        return tmp_chr_intermediate

    return False


  def find_per_block(self, target_block, previous_block=None):
    intermediate_per_block = ""

    for char_index in range(self.BLOCK_SIZE):
      random_sequence = self.generate_random_string(self.BLOCK_SIZE-char_index-1)
      padded_sequence = self.xor_string(intermediate_per_block, chr(char_index+1))
      char_intermediate = None
      # make while loop in case there is not found a invalid pad error in the brute force
      while not char_intermediate:
        char_intermediate = self.find_per_char(random_sequence, padded_sequence, target_block, char_index+1 )
      print("char ke", char_index)
      intermediate_per_block = char_intermediate + intermediate_per_block
    
    if previous_block:
      plain_block = self.xor_string(previous_block, intermediate_per_block)
      return intermediate_per_block, plain_block
    else:
      return intermediate_per_block


  def recover_plaintext(self):
    for block_index in range(len(self.original_safe_identity)-1):
      print block_index
      target_block = self.original_safe_identity[block_index+1]

      if block_index == 0:
        previous_block = self.original_safe_identity[block_index]
      else:
        previous_block = self.xor_string(self.recovered_plaintext[block_index-1], self.original_safe_identity[block_index])
      
      intermediate_per_block, tmp_plain = self.find_per_block(target_block, previous_block)
      self.recovered_plaintext.append(tmp_plain)
      print(self.recovered_plaintext)

    return self.recovered_plaintext


  def forge_ciphertext(self, target_plaintext):
    self.set_target_plaintext(target_plaintext)
    self.forged_ciphertext.insert(0, self.original_safe_identity[-1])

    for block_index in range(len(self.target_plaintext)-1, -1, -1):
      print block_index
      target_block = self.forged_ciphertext[0]
      intermediate_per_block = self.find_per_block(target_block)
      tmp_cipher = self.xor_string(intermediate_per_block, self.target_plaintext[block_index])
      if block_index != 0:
        tmp_cipher = self.xor_string(tmp_cipher, self.target_plaintext[block_index-1])

      self.forged_ciphertext.insert(0, tmp_cipher)

    return self.forged_ciphertext

  def xor_string(self, str_a, str_b):
    xored_str = ""
    for i in range(len(str_a)):
      xored_str += chr(ord(str_a[i]) ^ ord(str_b[i % len(str_b)]))
    
    return xored_str

  
  def generate_random_string(self, len_str):
    random_string = ""
    for i in range(len_str):
      random_string += random.choice(self.list_string)
    
    return random_string


  def pad(self, strs):
    byte = 16 - len(strs) % 16
    return strs + (chr(byte) * byte)

  
  def get_flag(self):
    final_payload = "".join(self.forged_ciphertext).encode("hex")
    self.conn.sendlineafter("Choice : ", "2")
    self.conn.sendlineafter("(in hex) : ", final_payload)
    print self.conn.recvuntil("}")

    
def main():
  exploit_object = Exploit("localhost", 9997)
  exploit_object.get_initial_safe_identity()

  # Sebenernya harus recover plaintext dulu biar tau beberapa key di object nya yang ga di expose, tapi ini solvernya langsung forging aja wkwk
  # exploit_object.recover_plaintext()
  # print "".join(exploit_object.recovered_plaintext)

  intended_plaintext = '{"agent_uid": 1337, "agent_status": 1, "agent_username": "lord", "agent_role": "admin", "agent_age": 2}'
  exploit_object.forge_ciphertext(intended_plaintext) 
  exploit_object.get_flag()

main()
