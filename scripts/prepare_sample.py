"""외부 연결 없이 공통 블록과 세 플랫폼 검증 패키지를 생성한다."""
from pathlib import Path
import hashlib, html, json, struct, zlib
ROOT=Path(__file__).resolve().parents[1]

def png():
    width,height=600,300
    rows=[]
    for y in range(height):
        row=bytearray()
        for x in range(width):
            row.extend((243,164,66) if 210<x<390 and 80<y<220 else (21,92,98))
        rows.append(b'\x00'+row)
    def chunk(kind,data):
        return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',width,height,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(b''.join(rows)))+chunk(b'IEND',b'')

def main():
    sample=json.loads((ROOT/'fixtures/sample.json').read_text())
    ids=[b['id'] for b in sample['blocks']]
    if len(ids)!=len(set(ids)):raise ValueError('중복 블록 id')
    out=ROOT/'artifacts/sample';out.mkdir(parents=True,exist_ok=True)
    asset=png();(out/'sample.png').write_bytes(asset)
    esc=html.escape
    parts=['<h1>'+esc(sample['title'])+'</h1>']
    for b in sample['blocks']:
        kind=b['type'];bid=esc(b['id'])
        if kind=='heading':s=f'<h2 id="{bid}">{esc(b["text"])}</h2>'
        elif kind=='paragraph':s=f'<p id="{bid}">{esc(b["text"])}</p>'
        elif kind=='list':s=f'<ul id="{bid}">'+''.join('<li>'+esc(t)+'</li>' for t in b['items'])+'</ul>'
        elif kind=='image':s=f'<figure id="{bid}"><img src="sample.png" alt="{esc(b["alt"])}"><figcaption>{esc(b["caption"])}</figcaption></figure>'
        elif kind=='link':s=f'<p id="{bid}"><a href="{esc(b["url"],quote=True)}">{esc(b["text"])}</a></p>'
        else:raise ValueError(kind)
        parts.append(s)
    body='\n'.join(parts)
    page='<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>O.S.M.U 샘플</title><style>body{max-width:760px;margin:40px auto;padding:0 24px;font:18px/1.8 sans-serif;color:#253337}img{max-width:100%;height:auto}figure{margin:24px 0}figcaption{font-size:14px;color:#53666a}</style><body>'+body+'</body></html>'
    (out/'preview.html').write_text(page)
    revision_data={'content':sample,'asset_sha256':hashlib.sha256(asset).hexdigest()}
    digest=hashlib.sha256(json.dumps(revision_data,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
    for platform in ['tistory','wordpress','naver']:
        package={'platform':platform,'destination_id':None,'status':'prepared_locally','revision_sha256':digest,'source':sample,'asset':'sample.png','external_validation':'not_run','note':'로컬 준비본. 인증·저장·예약·발행 미수행. 실제 대상과 변환 방식은 검증 필요.'}
        (out/f'{platform}.json').write_text(json.dumps(package,ensure_ascii=False,indent=2)+'\n')
    report={'local_preparation':'passed','unique_blocks':len(ids),'revision_sha256':digest,'external_validation':'not_run','files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.iterdir()) if p.name!='verification.json' and p.is_file()}}
    (out/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
