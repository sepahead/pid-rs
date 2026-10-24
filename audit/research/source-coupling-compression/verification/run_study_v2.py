"""Frozen exposed-data research orchestration; no production or calibration claim."""

from collections import Counter
import csv
from datetime import datetime, timedelta
from decimal import Decimal
from fractions import Fraction
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import re
import resource
import sys
import time

ROOT = Path(__file__).resolve().parent
RAW = ROOT.parents[1] / '.local/research-and-storage-20261005/application-benchmarks-v1/native-attempt-2/raw'
spec = importlib.util.spec_from_file_location('study_adapter', ROOT / 'adapter_v2.py')
A = importlib.util.module_from_spec(spec)
spec.loader.exec_module(A)
C = A.C
PINS = {
    'uci864-data.csv': 'c090ee5c94b61762bfec9d22767864490b51030f98cca030f02822468db25d9c',
    'datatraining.txt': 'b2c4d0ce2b9e4e453c476f7125ef31aeec2d1f5c7f5572d0e80de3df6521ab56',
    'datatest.txt': '1b92c7c1b2838963464fa891a610cf3c5db4becb7189189b29b330107a584c7f',
    'datatest2.txt': 'd026d1bd5aeccd4aff4f3b3710d48e40613bd5fc370db7e61bbdcaa50d985095',
}
ROOM_HEADER = ('Date,Time,S1_Temp,S2_Temp,S3_Temp,S4_Temp,S1_Light,S2_Light,S3_Light,S4_Light,'
               'S1_Sound,S2_Sound,S3_Sound,S4_Sound,S5_CO2,S5_CO2_Slope,S6_PIR,S7_PIR,Room_Occupancy_Count').split(',')
OFFICE_HEADER = 'date,Temperature,Humidity,Light,CO2,HumidityRatio,Occupancy'.split(',')
LEGAL = [(0,0),(0,1),(1,0),(1,1)]


def encoded(obj):
    return (json.dumps(obj, sort_keys=True, separators=(',', ':'), allow_nan=False)+'\n').encode()


def write_new(path, raw):
    # Aggregate mode budget is checked against the mode root, including partial laws.
    parent = path.parent if path.parent.name not in ('wire','laws') else path.parent.parent
    used = sum(p.stat().st_size for p in parent.rglob('*') if p.is_file())
    C.require(used + len(raw) <= 15 * 1024**2 // 2, 'mode output byte cap')
    with path.open('xb') as handle:
        handle.write(raw)


def decimal(text):
    C.require(0 < len(text) <= 128 and text == text.strip()
              and re.fullmatch(r'[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?',text) is not None,
              'decimal syntax')
    value = Decimal(text)
    C.require(value.is_finite() and value >= 0, 'measurement domain')
    return value


def integer(text, top):
    C.require(re.fullmatch(r'0|[1-9][0-9]*', text) is not None, 'integer syntax')
    value = int(text)
    C.require(value <= top, 'integer alphabet')
    return value


def timestamp(text, pattern):
    value = datetime.strptime(text, pattern)
    C.require(value.strftime(pattern) == text, 'timestamp spelling')
    return value


def dates(first, last):
    a, b = datetime.fromisoformat(first), datetime.fromisoformat(last)
    return [(a+timedelta(days=i)).date().isoformat() for i in range((b-a).days+1)]


def input_recordings():
    room, office, inventory = [], [], []
    total = 0
    for name, expected in PINS.items():
        raw = (RAW/name).read_bytes();total += len(raw)
        C.require(len(raw)<=1024**2 and total<=3*1024**2, 'raw byte cap')
        C.require(hashlib.sha256(raw).hexdigest()==expected, 'raw digest')
        reader = csv.reader(io.StringIO(raw.decode('utf-8')), strict=True)
        is_room = name=='uci864-data.csv'
        C.require(next(reader)==(ROOM_HEADER if is_room else OFFICE_HEADER), 'raw header')
        parsed = []
        for row in reader:
            C.require(len(row)==(19 if is_room else 8) and all(v!='' for v in row), 'row shape/missing')
            if is_room:
                when=timestamp(row[0]+' '+row[1],'%Y/%m/%d %H:%M:%S')
                features=(decimal(row[6]),integer(row[16],1),integer(row[17],1))
                target=integer(row[18],3)
            else:
                C.require(integer(row[0],2**63-1)>0,'row identifier')
                when=timestamp(row[1],'%Y-%m-%d %H:%M:%S')
                features=(decimal(row[4]),decimal(row[5]),decimal(row[2]))
                target=integer(row[7],1)
            parsed.append((when,features,target))
        C.require(0<len(parsed)<=32768,'file row cap')
        (room if is_room else office).extend(parsed)
        inventory.append({'file':name,'bytes':len(raw),'sha256':expected,'rows':len(parsed)})
    configs=[('room',room,4,['S1_Light','S6_PIR','S7_PIR'],
              dates('2017-12-22','2017-12-25'),['2017-12-26'],dates('2018-01-10','2018-01-11')),
             ('office',office,2,['Light','CO2','Temperature'],
              dates('2015-02-02','2015-02-08'),dates('2015-02-09','2015-02-10'),dates('2015-02-11','2015-02-18'))]
    return configs,inventory


def fit(config):
    name,raw,m,features,train,validation,test=config
    raw.sort(key=lambda r:r[0])
    C.require(0<len(raw)<=32768 and len({r[0] for r in raw})==len(raw),'recording rows/duplicate times')
    observed=sorted({r[0].date().isoformat() for r in raw})
    C.require(set(observed)==set(train+validation+test),'unexpected/missing dates')
    fitting=[r for r in raw if r[0].date().isoformat() in train]
    C.require(bool(fitting),'empty training')
    thresholds=[None]*3
    for i in range(1 if name=='room' else 3):
        thresholds[i]=sorted(r[1][i] for r in fitting)[(len(fitting)-1)//2]
    rows=[(when.date().isoformat(),tuple(int(value>thresholds[i]) if thresholds[i] is not None else value
                                      for i,value in enumerate(values)),t) for when,values,t in raw]
    training=[r for r in rows if r[0] in train]
    tuple_counts=Counter(r[1][1:] for r in training)
    ranked=sorted(tuple_counts,key=lambda t:(-tuple_counts[t],t))
    a=ranked[0];b=ranked[1] if len(ranked)>1 else next(t for t in LEGAL if t!=a)
    roles={'train':train,'validation':validation,'test':test}
    metadata={'recording':name,'target_size':m,'source_names':features,'thresholds':[None if t is None else str(t) for t in thresholds],
              'heads':[list(a),list(b)],'training_tuple_counts':[[*t,c] for t,c in sorted(tuple_counts.items())],
              'roles':roles,'first_timestamp':raw[0][0].isoformat(),'last_timestamp':raw[-1][0].isoformat(),'timezone':'unknown'}
    return rows,training,(a,b),roles,metadata


def context(s,arm,heads):
    if arm=='target_only':return ()
    if arm=='x_only':return (s[0],)
    if arm in ('compressed_refit','fixed_remap'):
        return s if s[1:] in heads else (s[0],*heads[0])
    return s


def train_models(rows,heads,m):
    result={}
    for arm in ('full','compressed_refit','x_only','target_only'):
        table={}
        for _,s,t in rows:
            ctx=context(s,arm,heads)
            if ctx not in table:table[ctx]=[0]*m
            table[ctx][t]+=1
        result[arm]=table
    return result


def prediction(counts,arm,models,heads,m):
    table=models['full' if arm=='fixed_remap' else arm]
    def score(selected):
        n=sum(c for _,c in selected)
        if n==0:return {'status':'unavailable','rows':0,'reason':'class absent'}
        terms=[];brier=Fraction(0);unseen=0
        for z,c in selected:
            ctx=context(z[:3],arm,heads);training=table.get(ctx,[0]*m)
            if ctx not in table:unseen+=c
            probabilities=[Fraction(v+1,sum(training)+m) for v in training]
            terms.append((1/probabilities[z[3]],c))
            brier+=c*(sum(v*v for v in probabilities)-2*probabilities[z[3]]+1)
        loss=C.record(C.factors(terms),n)
        C.require(0<=brier<=2*n,'Brier range')
        return {'status':'evaluated','rows':n,'log_loss':loss,'brier':str(brier/n),
                'brier_display':float(brier/n),'unseen_context_rows':unseen}
    allcells=sorted(counts.items())
    return {'overall':score(allcells),'classes':[{'target':t,**score([(z,c) for z,c in allcells if z[3]==t])} for t in range(m)]}


def wire(rows,mode,heads,metadata):
    source=[s for _,s,_ in rows]
    book=LEGAL if mode=='fixed' else sorted({s[1:] for s in source}) if mode=='lossless' else list(heads)
    width=(len(book)-1).bit_length()
    expected=[s if mode!='lossy' or s[1:] in heads else (s[0],*heads[0]) for s in source]
    header={'format':'pid-reference-wire-v1','mode':mode,'rows':len(rows),'features':metadata['source_names'],
            'thresholds':metadata['thresholds'],'tuples':[list(t) for t in book],'tuple_bits':width,
            'target_included':False,'timestamps_included':False,'original_continuous_values_included':False}
    h=encoded(header);payload=bytearray();pending=bits=0
    for s in expected:
        code=(s[0]<<width)|book.index(s[1:])
        pending=(pending<<(width+1))|code;bits+=width+1
        while bits>=8:
            bits-=8;payload.append((pending>>bits)&255);pending&=(1<<bits)-1
    if bits:payload.append(pending<<(8-bits))
    # Rehydrate from actual serialized header and payload, including padding.
    blob=b'PIDW1'+len(h).to_bytes(4,'big')+h+payload
    length=int.from_bytes(blob[5:9],'big');decoded_header=json.loads(blob[9:9+length]);body=blob[9+length:]
    cursor=0
    def read(count):
        nonlocal cursor
        out=0
        for _ in range(count):
            out=(out<<1)|((body[cursor//8]>>(7-cursor%8))&1);cursor+=1
        return out
    decoded=[]
    for _ in range(decoded_header['rows']):
        x=read(1);idx=read(decoded_header['tuple_bits'])
        C.require(idx<len(decoded_header['tuples']),'wire code')
        decoded.append((x,*decoded_header['tuples'][idx]))
    C.require(decoded==expected,'wire round trip')
    C.require(all(read(1)==0 for _ in range(len(body)*8-cursor)),'wire padding')
    return blob,{'mode':mode,'header_bytes':9+len(h),'payload_bytes':len(payload),'total_bytes':len(blob),
                 'sha256':hashlib.sha256(blob).hexdigest(),'round_trip':'exact encoded original coordinates' if mode!='lossy' else 'exact mapped coordinates'}


def run(output):
    started=time.monotonic();output.mkdir(exist_ok=False);(output/'wire').mkdir();(output/'laws').mkdir()
    configs,inventory=input_recordings();recordings=[]
    for config in configs:
        rows,training,heads,roles,metadata=fit(config);m=metadata['target_size']
        models=train_models(training,heads,m)
        metadata['model_bytes']={arm:len(encoded({'target_size':m,'smoothing':1,'counts':[[list(k),v] for k,v in sorted(table.items())]})) for arm,table in models.items()}
        laws=[]
        for label,days in [(d,[d]) for d in sorted({r[0] for r in rows})]+list(roles.items()):
            selected=[r for r in rows if r[0] in days];C.require(bool(selected),'empty law')
            counts=dict(Counter((*s,t) for _,s,t in selected))
            result=C.compare_laws(counts,heads,m,A.compare)
            selected_terms={}
            for item in result['coordinates']:
                if item['stage']=='cumulative' and item['component']=='net' and item['branches'] in ([1],[7]):
                    for version in ('before','after'):
                        selected_terms[tuple(item['branches']),version]=tuple((Fraction(a,b),e) for a,b,e in item[version]['factors'])
            extra={version:C.combine([(selected_terms[(7,),version],1),(selected_terms[(1,),version],-1)])
                   for version in ('before','after')}
            result['original_extra_information']=C.record(extra['before'],result['rows'])
            result['compressed_extra_information']=C.record(extra['after'],result['rows'])
            lost_from_extra=C.combine([(extra['before'],1),(extra['after'],-1)])
            C.require(C.record(lost_from_extra,result['rows'])['product_sha256']==result['lost_information']['product_sha256'],
                      'conditional information difference identity')
            d=Fraction(result['tail']);ln8=C.interval(((Fraction(8),1),))
            if d:
                term=C.interval(((Fraction(8)/d,1),))
                local=(d*term[0]+8*d,d*term[1]+8*d)
                bound=tuple(130*min(ln8[i],local[i]) for i in (0,1))
            else:bound=(Fraction(0),Fraction(0))
            C.require(Fraction(result['allocation_interval'][1])<=bound[0],'continuity bound separation')
            result.update({'law':label,'dates':days,'class_counts':[sum(c for z,c in counts.items() if z[3]==t) for t in range(m)],
                           'predictions':{arm:prediction(counts,arm,models,heads,m) for arm in ('full','fixed_remap','compressed_refit','x_only','target_only')},
                           'continuity_upper_interval':[str(v) for v in bound]})
            result['wire']=[]
            for mode in ('fixed','lossless','lossy'):
                blob,info=wire(selected,mode,heads,metadata)
                write_new(output/'wire'/f'{metadata["recording"]}-{label}-{mode}.bin',blob)
                result['wire'].append(info)
            law_raw=encoded(result)
            law_path=output/'laws'/f'{metadata["recording"]}-{label}.json'
            write_new(law_path,law_raw)
            laws.append({'law':label,'rows':result['rows'],'path':str(law_path.relative_to(output)),
                         'bytes':len(law_raw),'sha256':hashlib.sha256(law_raw).hexdigest()})
            print(json.dumps({'recording':metadata['recording'],'law':label,'status':'computed'}),flush=True)
        recordings.append({'metadata':metadata,'laws':laws})
    report={'schema':'original-three-source-development-v3-index','scope':'two exposed recordings; thirty overlapping empirical laws; no population or production claim',
            'raw':inventory,'recordings':recordings}
    raw=encoded(report)
    C.require(len(raw)<=8*1024**2,'report byte cap')
    write_new(output/'REPORT.json',raw)
    write_new(output/'EXECUTION.json',encoded({'elapsed_seconds':time.monotonic()-started,
               'peak_rss_native_units':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
               'rss_units':'bytes on Darwin; process high-water mark, not incremental algorithm allocation',
               'report_bytes':len(raw),'report_sha256':hashlib.sha256(raw).hexdigest()}))


if __name__=='__main__':
    C.require(len(sys.argv)==2,'expected new output directory')
    run(Path(sys.argv[1]))

