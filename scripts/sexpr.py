import re,json,copy
class Atom(str): pass
def parse(s):
    ts=re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+',s); stack=[]; root=None
    for t in ts:
        if t=='(':
            n=[]
            if stack: stack[-1].append(n)
            stack.append(n)
        elif t==')': root=stack.pop()
        else: stack[-1].append(json.loads(t) if t.startswith('"') else Atom(t))
    return root
def dump(n):
    if isinstance(n,list): return '('+' '.join(dump(x) for x in n)+')'
    return str(n) if isinstance(n,Atom) else json.dumps(n,ensure_ascii=False)
def children(n,k): return [x for x in n if isinstance(x,list) and x and x[0]==k]
def child(n,k): return next(iter(children(n,k)),None)
def A(s): return Atom(str(s))
def node(k,*v): return [A(k),*v]
