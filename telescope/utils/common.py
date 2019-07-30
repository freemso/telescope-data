import hashlib


def get_md5(src):
    src = src.encode() if type(src) == str else src
    myMd5 = hashlib.md5()
    myMd5.update(src)
    myMd5_Digest = myMd5.hexdigest()
    return myMd5_Digest
