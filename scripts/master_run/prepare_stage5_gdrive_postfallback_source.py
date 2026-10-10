"""Default NOOP; derive one C-only G08 pin refresh after actual receipts close."""
from pathlib import Path
import argparse, ast, hashlib, json, os, re

WORK=Path(__file__).resolve().parent
BASE='stage5_gdrive_view_postprofile.py'
BASE_SHA='1ec2380d218128e325954552057ed1215268297862e2910550b2eb7c46a112e9'
OLD_DIR='stage5_setup_toolchain_actual_postiq_07'
NEW_DIR='stage5_setup_toolchain_actual_postiq_08'
OLD_REVIEW='stage5_toolchain07_postprofile_independent_review.json'
NEW_REVIEW='stage5_toolchain08_postfallback_independent_review.json'
OUTPUT='stage5_gdrive_view_postfallback.py'
OLD_BOOT='f0ffcebc-4901-479d-9559-89d45e9cfa38'
LEAVES=('result.json','lock_released.json','toolchain_proof.json','linux_terminal.json','wsl_exit.json')


def need(ok,message):
    if not ok:raise ValueError(message)


def digest(raw):return hashlib.sha256(raw).hexdigest()


def render(raw,pins):
    need(isinstance(raw,bytes) and digest(raw)==BASE_SHA,'Frozen G1ec source required')
    names={NEW_DIR+'/'+leaf for leaf in LEAVES}|{NEW_REVIEW}
    need(isinstance(pins,dict) and set(pins)==names and all(isinstance(h,str) and re.fullmatch('[a-f0-9]{64}',h) for h in pins.values()),
         'Exactly six explicit actual toolchain08/review pins required')
    tree=ast.parse(raw);old=next(ast.literal_eval(n.value) for n in tree.body
        if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='FRESH_PINS' for x in n.targets))
    source=raw.decode();source=source.replace(OLD_DIR,NEW_DIR).replace(OLD_REVIEW,NEW_REVIEW)
    for name,pin in old.items():
        changed=name.replace(OLD_DIR,NEW_DIR).replace(OLD_REVIEW,NEW_REVIEW)
        before=repr(changed)+':'+repr(pin);after=repr(changed)+':'+repr(pins[changed])
        need(source.count(before)==1,'One exact fresh pin assignment required');source=source.replace(before,after)
    compile(source,OUTPUT,'exec')
    class Review(ast.NodeTransformer):
        def visit_Constant(self,node):
            if node.value==NEW_REVIEW:node.value=OLD_REVIEW
            return node
    def funcs(t):return {n.name:ast.dump(n,include_attributes=False) for n in t.body if isinstance(n,ast.FunctionDef)}
    need(funcs(Review().visit(ast.parse(source)))==funcs(tree),'G scientific/topology/ownership function behavior changed')
    return source.encode()


def read_plain(path,limit=8*1024**2):
    path=Path(path);need(WORK in path.parents and path==path.resolve(),'Exact plain C-work input required')
    for node in (path,*path.parents):
        info=node.lstat();need(not node.is_symlink() and not getattr(info,'st_file_attributes',0)&0x400,'Input alias/reparse forbidden')
    need(path.is_file() and path.stat().st_nlink==1 and path.stat().st_size<=limit,'Bounded single-link input required')
    with path.open('rb') as stream:
        before=os.fstat(stream.fileno());raw=stream.read(limit+1);after=os.fstat(stream.fileno())
    identity=lambda x:(x.st_dev,x.st_ino,x.st_size,x.st_mtime_ns)
    need(len(raw)<=limit and identity(before)==identity(after)==identity(path.lstat()) and len(raw)==before.st_size,'Input identity/bytes drift')
    return raw


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--prepare',action='store_true')
    p.add_argument('--proof-sha256');p.add_argument('--review-sha256');a=p.parse_args()
    if not a.prepare:
        print(json.dumps({'state':'PREPARED_NOT_RUN','source_written':False,'future_pins':'NOT_GUESSED','WSL_launches':0}));return 0
    raw=read_plain(WORK/BASE);files={NEW_DIR+'/'+leaf:read_plain(WORK/NEW_DIR/leaf) for leaf in LEAVES}
    files[NEW_REVIEW]=read_plain(WORK/NEW_REVIEW)
    pins={name:digest(data) for name,data in files.items()}
    need(pins[NEW_DIR+'/toolchain_proof.json']==a.proof_sha256 and pins[NEW_REVIEW]==a.review_sha256,
         'Explicit published actual08 proof/review SHA required')
    candidate=render(raw,pins)
    namespace={'__name__':'_postfallback_G_source_validation','__file__':str(WORK/OUTPUT)}
    exec(compile(candidate,str(WORK/OUTPUT),'exec'),namespace)
    boot=namespace['fresh_toolchain_gate'](WORK,WORK/NEW_DIR/'toolchain_proof.json',a.proof_sha256)
    need(boot!=OLD_BOOT,'Fallback requires a genuinely new Linux boot')
    need(read_plain(WORK/BASE)==raw and all(read_plain(WORK/name)==data for name,data in files.items()),'Final frozen input drift')
    output=WORK/OUTPUT;need(not output.exists() and not output.is_symlink(),'Preserve existing derived source')
    with output.open('xb') as stream:need(stream.write(candidate)==len(candidate),'Short source write');stream.flush();os.fsync(stream.fileno())
    need(output.read_bytes()==candidate,'Derived source readback differs')
    print(json.dumps({'state':'PASS_C_SOURCE_PIN_REFRESH_ONLY_ACTUAL_G_NOT_RUN','source':str(output),
        'sha256':digest(candidate),'actual_boot':boot,'fresh_pins':pins,
        'adoption':'Independent derived-source review and root publication required before G invocation'}));return 0


if __name__=='__main__':raise SystemExit(main())
