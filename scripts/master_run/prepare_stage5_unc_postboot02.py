"""Fill only actual runtime/storage pins in the existing UNC probe template."""
from pathlib import Path
import hashlib,json
W=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    template=W/'stage5_atomic_config.template.json'
    assert sha(template)=='94137787139276a70cd10e0c85e13597c860950c2fba04c5c05580601ddc11cf'
    runtime=W/'stage5_runtime_actual_postiq_06.json'
    storage=W/'stage5_storage_actual_postiq_05.json'
    assert sha(runtime)=='f64edf88129b9fcf294cdb19db1d754d084b676ec99560f848ecb253b29a55d1'
    assert sha(storage)=='47d23f11135f506d26892b40f1e0f684001970445cec1d166e69c6822578fc54'
    value=json.loads(template.read_bytes())
    for key,p in [('runtime',runtime),('work_storage',storage)]:
        prefix='manifest' if key=='runtime' else 'proof'
        value[key][prefix+'_path']='/mnt/c/'+'/'.join(p.parts[1:])
        value[key][prefix+'_sha256']=sha(p)
    out=W/'stage5_unc_config_actual_postboot_02.json'
    with out.open('x',encoding='utf-8',newline='\n') as f:json.dump(value,f,indent=2);f.write('\n')
    print(json.dumps({'path':str(out),'sha256':sha(out),'scope':'NONSCIENTIFIC_UNC_ONLY_NATIVE_BUDGETS_REMAIN_NULL'}))
if __name__=='__main__':main()
