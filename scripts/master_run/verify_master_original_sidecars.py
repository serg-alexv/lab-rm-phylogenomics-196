"""Verify fixed Release assets and original LF/CRLF sidecars without replacing them."""

def begin(A,args,assets,sidecars,out,result):
    A.require(len(assets)==len(sidecars)>0,'Exact sidecar accounting differs')
    expected=assets+sidecars
    A.require(len({r['name'] for r in expected})==len(expected),'Duplicate expected asset name')
    for asset,side in zip(assets,sidecars):
        A.require(side['name']==asset['name']+'.sha256' and side['newline'] in ('\n','\r\n'),'Sidecar scope differs')
        raw=(asset['sha256']+'  '+asset['name']+side['newline']).encode('ascii')
        A.require(len(raw)==side['bytes'] and A.sha(raw)==side['sha256'],'Independent original sidecar pin differs')
    A.require(A.api('commits/'+args.tag)['sha']==args.expected_tag_commit,'Release tag target differs')
    release=A.api('releases/tags/'+args.tag)
    A.require(release['tag_name']==args.tag and release['draft'] is False,'Release identity/draft differs')
    selected={}
    for row in expected:
        matches=[a for a in release['assets'] if a['name']==row['name']]
        A.require(len(matches)==1,'Missing/duplicate original Release asset: '+row['name'])
        item=matches[0]
        A.require(item['state']=='uploaded' and item['size']==row['bytes']
            and item['digest']=='sha256:'+row['sha256'],'Exact original asset metadata differs')
        selected[row['name']]=item
    result.update(tag=args.tag,expected_tag_commit=args.expected_tag_commit,source_commit=args.source_commit,
        release_url=release['html_url'],release_id=release['id'])
    for asset,side in zip(assets,sidecars):
        A.run(['gh','release','download',args.tag,'--repo',A.REPO,'--pattern',asset['name'],
            '--pattern',side['name'],'--dir',str(out)],timeout=300)
        raw=(asset['sha256']+'  '+asset['name']+side['newline']).encode('ascii')
        A.require((out/side['name']).read_bytes()==raw,'Actual original sidecar bytes differ')
    result['downloaded_assets']=[dict(name=r['name'],remote_asset_id=selected[r['name']]['id'],
        bytes=(out/r['name']).stat().st_size,sha256=A.digest(out/r['name']),remote_digest=selected[r['name']]['digest'])
        for r in expected]
    A.require(all(actual['bytes']==r['bytes'] and actual['sha256']==r['sha256']
        for actual,r in zip(result['downloaded_assets'],expected)),'Actual original asset download differs')
    return release,selected
