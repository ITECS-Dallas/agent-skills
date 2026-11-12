#!/usr/bin/env python3
"""Actual Codex legacy-to-thin marketplace migration in an isolated profile."""
import argparse, hashlib, io, json, os, pathlib, shutil, subprocess, sys, tarfile, tempfile, time, tomllib

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--codex', default='codex')
parser.add_argument('--catalog', type=pathlib.Path, required=True)
parser.add_argument('--catalog-url', required=True)
parser.add_argument('--ref', required=True)
args=parser.parse_args()
EXE=args.codex
REPO=pathlib.Path(__file__).resolve().parents[1]
expected_version=json.loads((args.catalog/'plugins/itecs-halopsa/.codex-plugin/plugin.json').read_text(encoding='utf-8'))['version']
expected_tools=len(json.loads((args.catalog/'plugins/itecs-halopsa/BUILD-MANIFEST.json').read_text(encoding='utf-8'))['tools'])
with tempfile.TemporaryDirectory(prefix='itecs-host-update-') as directory:
    root=pathlib.Path(directory);profile=root/'profile';profile.mkdir()
    old=root/'legacy-catalog'
    shutil.copytree(args.catalog,old)
    shutil.rmtree(old/'plugins/itecs-halopsa')
    archive=subprocess.check_output(['git','archive','45c6517036e4a6a2f57ec86b32ffc7903cbf9aed','plugins/itecs-halopsa'],cwd=REPO)
    with tarfile.open(fileobj=io.BytesIO(archive)) as stream: stream.extractall(old,filter='data')
    env=dict(os.environ,CODEX_HOME=str(profile),**{('USERPROFILE' if os.name=='nt' else 'HOME'):str(profile)},GIT_TERMINAL_PROMPT='0',GCM_INTERACTIVE='never')
    fixture=profile/'.codex/halopsa-mcp/config.json';fixture.parent.mkdir(parents=True)
    config=json.loads((REPO/'tests/runtime-configs/halopsa.json').read_text())
    for server in config['servers']:
        for key in list(server):
            if key.endswith('_command'): server[key]=[sys.executable,'-c',"print('synthetic-migration-test')"]
    fixture.write_text(json.dumps(config),encoding='utf-8');before=hashlib.sha256(fixture.read_bytes()).hexdigest()
    def cli(*args):
        start=time.monotonic();p=subprocess.run([EXE,*args,'--json'],cwd=root,env=env,capture_output=True,text=True,encoding='utf-8',timeout=40)
        if p.returncode: raise RuntimeError('Codex '+ ' '.join(args[:3])+' failed: '+p.stderr)
        result=json.loads(p.stdout)
        print(json.dumps({'operation':' '.join(args[:3]),'seconds':round(time.monotonic()-start,2),'result':'passed','version':result.get('version')}),flush=True)
        return result
    cli('plugin','marketplace','add',str(old))
    legacy=cli('plugin','add','itecs-halopsa@itecs-agent-skills')
    assert legacy['version']=='0.18.2'
    cli('plugin','add','portable-development-workflow@itecs-agent-skills')
    settings_before=tomllib.loads((profile/'config.toml').read_text())['plugins']
    cli('plugin','marketplace','remove','itecs-agent-skills')
    cli('plugin','marketplace','add',args.catalog_url,'--ref',args.ref)
    cli('plugin','marketplace','upgrade','itecs-agent-skills')
    updated=cli('plugin','add','itecs-halopsa@itecs-agent-skills')
    assert updated['version']==expected_version
    installed=pathlib.Path(updated['installedPath'])
    assert (installed/'runtime-mode').read_text().strip()=='release'
    p=subprocess.run([sys.executable,'-X','utf8',str(installed/'scripts/doctor.py'),'--discover','--config',str(fixture),'--timeout','35'],cwd=installed,env=env,capture_output=True,text=True,encoding='utf-8',timeout=45)
    assert p.returncode==0,p.stderr
    report=json.loads(p.stdout);assert report['tool_count']==expected_tools and report['discovery']=='ok'
    assert hashlib.sha256(fixture.read_bytes()).hexdigest()==before
    settings_after=tomllib.loads((profile/'config.toml').read_text())['plugins']
    assert all(settings_after.get(key)==value for key,value in settings_before.items())
    print(json.dumps({'result':'passed','legacy_version':legacy['version'],'updated_version':updated['version'],'tools_after_update':report['tool_count'],'external_config_preserved':True,'plugin_settings_preserved':True,'vendor_calls':False}),flush=True)
