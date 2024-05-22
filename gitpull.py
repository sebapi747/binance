import os
filedir = os.path.dirname(__file__)
os.chdir("./" if filedir=="" else filedir)

for d in os.listdir(".."):
    otherdir = "../"+d
    if os.path.isdir(otherdir) and os.path.exists(otherdir+"/.git"):
        print(otherdir)
        os.chdir(otherdir)
        os.system("git pull --rebase")
