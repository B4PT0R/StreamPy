#Module providing encryption utilities

import random

def extended_euclid(a,b):
    l1=[r1,u1,v1]=[a,1,0]
    l2=[r2,u2,v2]=[b,0,1]
    while not r2==0:
        l=[r1-(r1//r2)*r2,u1-(r1//r2)*u2,v1-(r1//r2)*v2]
        l1=[r1,u1,v1]=l2
        l2=[r2,u2,v2]=l
    return l1

def init_prev(key):
    s=0
    for i in range(len(key)):
        s=s+ord(key[i])
    return s

def ct():
    i=1
    special=[9,10,8364]
    t={}
    for c in special:
        t[i]=c
        i+=1
    for c in range(32,127):
        t[i]=c
        i+=1
    for c in range(161,256):
        t[i]=c
        i+=1    
    return t

def ict():
    t={}
    c=ct()
    for i in range(1,len(c)+1):
        k=c[i]
        t[k]=i
    return t

table=ct()
inverse_table=ict()

def random_char():
    return chr(table[random.choice(list(range(1,194)))])

def rnd_str_fill(string,length):
    if len(string)>=length:
        return string
    else:
        filled_string=string
        while len(filled_string)<length:
            filled_string+=random_char()
        return filled_string    

def gen_lock(key,min_length):
    filled_key=rnd_str_fill(key,min_length)
    lock=encrypt(filled_key,key)
    return lock

def check_lock(key,lock):
    n=len(key)
    return key==decrypt(lock,key)[:n]


def encrypt(string,key):
    t=ct()
    it=ict()
    if key=='':
        k=lambda i:1
        p=0
    else:
        k=lambda i:ord(key[i%len(key)])
        p=1
    r=''
    n=len(string)
    init=init_prev(key)
    prev=init
    for i in range(n):
        c1=string[i]
        n1=ord(c1)
        if not n1 in it.keys():
            n1=ord('?')
        v1=it[n1]-1
        K1=k(i)+prev+init
        K2=K1%(len(t)-1)+1
        K3=p*K2+(1-p)*1
        v2=((v1*K3+prev*p)%len(t))+1
        prev=v2
        n2=t[v2]
        c2=chr(n2)
        r=r+c2
    return r
    
def decrypt(string,key):
    t=ct()
    it=ict()
    if key=='':
        k=lambda i:1
        p=0
    else:
        k=lambda i:ord(key[i%len(key)])
        p=1
    r=''
    n=len(string)
    init=init_prev(key)
    prev=init
    for i in range(n):
        c1= string[i]
        n1=ord(c1)   
        v1=it[n1]-1
        K1=k(i)+prev+init
        K2=K1%(len(t)-1)+1
        K3=p*K2+(1-p)*1
        [_,invk,_]=extended_euclid(K3,len(t))
        v2=(((v1-prev*p)*invk)%len(t))+1
        prev=v1+1
        n2=t[v2]
        c2=chr(n2)
        r=r+c2
    return r
