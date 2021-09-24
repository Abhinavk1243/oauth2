import hashlib
password=bytes("Abhi13",'utf-8')
pass_hash = hashlib.md5()
pass_hash.update(password)
password=pass_hash.hexdigest()

print(password)