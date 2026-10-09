"""Small contract/negative tests; no WSL, models, HMM searches or genome data."""
from pathlib import Path
from unittest import mock
from types import SimpleNamespace
import ast, json, tempfile, unittest
import stage5_atomic as R
import stage5_atomic_process as P


class Contracts(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='stage5_synthetic_', dir=Path(__file__).parent)
        self.root = Path(self.tmp.name).resolve()
        self.assertTrue(Path(__file__).parent.resolve() in self.root.parents)

    def tearDown(self):
        self.tmp.cleanup()

    def save(self, name, value):
        path = self.root / name
        P.atomic_json(path, value)
        return path

    def lease(self):
        return {'schema': 'STAGE05_WINDOWS_OWNER_LEASE_V1', 'nonce': 'one', 'workflow_lock_held': True,
                'owner_pid': 1, 'owner_creation_filetime': '123456789', 'measured_unix': 100,
                'expires_unix': 115, 'windows_available_bytes': 5, 'windows_commit_headroom_bytes': 6,
                'disk_available_bytes': {'SYNTHETIC_C_VOLUME': 7, 'SYNTHETIC_G_VOLUME': 8}}

    def test_fresh_lease(self):
        path = self.save('lease.json', self.lease())
        self.assertEqual(P.check_lease(path, 'one', {'lease_max_age_seconds': 20}, now=105)['owner_pid'], 1)

    def test_stale_lease_rejected(self):
        path = self.save('lease.json', self.lease())
        with self.assertRaises(P.Fatal):
            P.check_lease(path, 'one', {'lease_max_age_seconds': 20}, now=116)

    def test_owner_nonce_and_lock_rejected(self):
        path = self.save('lease.json', self.lease())
        with self.assertRaises(P.Fatal):
            P.check_lease(path, 'other', {'lease_max_age_seconds': 20}, now=105)
        value = self.lease(); value['workflow_lock_held'] = False
        P.atomic_json(path, value)
        with self.assertRaises(P.Fatal):
            P.check_lease(path, 'one', {'lease_max_age_seconds': 20}, now=105)

    def test_missing_commit_measurement_rejected(self):
        value = self.lease(); del value['windows_commit_headroom_bytes']
        path = self.save('lease.json', value)
        with self.assertRaises(P.Fatal):
            P.check_lease(path, 'one', {'lease_max_age_seconds': 20}, now=105)

    def test_missing_or_invalid_physical_disk_measurements_rejected(self):
        for disks in [None, {}, [], {'SYNTHETIC_C': -1}, {'SYNTHETIC_C': 1.5},
                      {'SYNTHETIC_C': True}, {'': 7}, {'   ': 7}]:
            with self.subTest(disks=disks):
                value = self.lease(); value['disk_available_bytes'] = disks
                path = self.save('lease.json', value)
                with self.assertRaises(P.Fatal):
                    P.check_lease(path, 'one', {'lease_max_age_seconds': 20}, now=105)

    def admission_fixture(self, disks):
        supervisor = P.Supervisor.__new__(P.Supervisor)
        supervisor.lease_path = self.root/'synthetic_lease.json'
        supervisor.policy = {'windows_reserve_bytes': 1, 'incremental_windows_requirement_bytes': 1,
                             'commit_requirement_bytes': 1, 'linux_job_requirement_bytes': 1,
                             'linux_reserve_bytes': 1, 'minimum_disk_free_bytes': 5,
                             'resource_wait_seconds': 0}
        supervisor.digest = lambda path: '0'*64
        lease = self.lease(); lease['disk_available_bytes'] = disks
        return supervisor, lease

    def test_each_physical_windows_volume_can_veto_virtual_linux_disk(self):
        for disks in [{'SYNTHETIC_C': 4, 'SYNTHETIC_G': 100},
                      {'SYNTHETIC_C': 100, 'SYNTHETIC_G': 4}]:
            with self.subTest(disks=disks):
                supervisor, lease = self.admission_fixture(disks)
                with mock.patch.object(supervisor, 'check_owner', return_value=lease), \
                     mock.patch.object(P, 'linux_available', return_value=100), \
                     mock.patch('shutil.disk_usage', return_value=SimpleNamespace(free=100)):
                    with self.assertRaises(P.Deferred):
                        supervisor.admission(self.root)
                receipt = P.read_json(self.root/'latest_admission.json')
                self.assertFalse(receipt['admitted'])
                self.assertFalse(receipt['windows_disks_sufficient'])
                self.assertEqual(receipt['disk_free_bytes'], 100)

    def test_all_physical_and_linux_disks_sufficient_admit(self):
        supervisor, lease = self.admission_fixture({'SYNTHETIC_C': 5, 'SYNTHETIC_G': 6})
        with mock.patch.object(supervisor, 'check_owner', return_value=lease), \
             mock.patch.object(P, 'linux_available', return_value=100), \
             mock.patch('shutil.disk_usage', return_value=SimpleNamespace(free=5)):
            result = supervisor.admission(self.root)
        self.assertTrue(result['admitted'] and result['windows_disks_sufficient'])

    def test_owner_birth_identity_stable_across_renewals(self):
        supervisor = P.Supervisor.__new__(P.Supervisor)
        supervisor.lease_path = Path('synthetic'); supervisor.nonce = 'one'; supervisor.policy = {}
        supervisor.owner_identity = (1,'123456789')
        with mock.patch.object(P,'check_lease',return_value=self.lease()):
            self.assertEqual(supervisor.check_owner()['owner_pid'],1)
        changed = self.lease(); changed['owner_creation_filetime'] = '123456790'
        with mock.patch.object(P,'check_lease',return_value=changed), self.assertRaises(P.Fatal):
            supervisor.check_owner()

    def test_nonfinite_or_unbounded_resource_policy_rejected(self):
        template = json.loads(Path(R.__file__).with_name('stage5_atomic_config.template.json').read_text())
        for key,value in list(template['resource_policy'].items()):
            if value is None: template['resource_policy'][key] = 1
        path = self.save('config.json',template)
        self.assertEqual(R.load_config(path)['resource_policy']['threads'],2)
        for field,value in [('command_timeout_seconds',float('inf')),('resource_wait_seconds',float('nan')),
                            ('job_timeout_seconds',86401),('drain_timeout_seconds',61)]:
            with self.subTest(field=field,value=value):
                modified = json.loads(json.dumps(template)); modified['resource_policy'][field] = value
                P.atomic_json(path,modified)
                with self.assertRaises(P.Fatal): R.load_config(path)

    def test_proc_stat_with_parentheses(self):
        directory = self.root / '42'; directory.mkdir()
        rest = ['S', '10', '42', '42'] + ['0'] * 15 + ['987']
        (directory / 'stat').write_text('42 (a tricky ) name) ' + ' '.join(rest))
        record = P.proc_record(42, self.root)
        self.assertEqual((record['ppid'], record['pgid'], record['sid'], record['start_ticks']), (10, 42, 42, '987'))

    def test_group_selection_does_not_include_other_groups(self):
        table = {1: {'pid': 1, 'pgid': 1}, 2: {'pid': 2, 'pgid': 1}, 3: {'pid': 3, 'pgid': 3}}
        self.assertEqual([row['pid'] for row in P.group_members(1, table)], [1, 2])

    def test_pidfd_reused_birth_rejected_without_signal(self):
        record = {'pid':42,'start_ticks':'old'}
        with mock.patch.object(P,'proc_record',side_effect=[record,{'pid':42,'start_ticks':'new'}]), \
             mock.patch.object(P.os,'pidfd_open',return_value=71,create=True), mock.patch.object(P.os,'close') as close:
            self.assertIsNone(P.verified_pidfd(record))
            close.assert_called_once_with(71)

    def test_pidfd_missing_birth_never_opened(self):
        with mock.patch.object(P,'proc_record',return_value=None), \
             mock.patch.object(P.os,'pidfd_open',create=True) as opened:
            self.assertIsNone(P.verified_pidfd({'pid':42,'start_ticks':'old'}))
            opened.assert_not_called()

    def test_pidfd_matching_birth_retained(self):
        record = {'pid':42,'start_ticks':'old'}
        with mock.patch.object(P,'proc_record',return_value=record), \
             mock.patch.object(P.os,'pidfd_open',return_value=71,create=True):
            self.assertEqual(P.verified_pidfd(record),71)

    def test_supervisor_has_no_numeric_pid_or_group_signal_calls(self):
        tree = ast.parse(Path(P.__file__).read_text())
        forbidden = [node for node in ast.walk(tree) if isinstance(node,ast.Call)
                     and isinstance(node.func,ast.Attribute) and isinstance(node.func.value,ast.Name)
                     and node.func.value.id == 'os' and node.func.attr in {'kill','killpg'}]
        self.assertFalse(forbidden)

    def test_missing_actual_closure_rejected(self):
        supervisor = P.Supervisor.__new__(P.Supervisor); supervisor.boot_id = 'boot'
        with self.assertRaises(P.Fatal):
            supervisor.assert_closed({'closure_path': str(self.root / 'missing'), 'command_nonce': 'x'})

    def test_launch_intent_without_actual_identity_blocks_new_child(self):
        intent = self.save('native.launch_intent.json',{'command_nonce':'x'})
        supervisor = P.Supervisor.__new__(P.Supervisor)
        with self.assertRaises(P.Fatal): supervisor.assert_intent_closed(intent)

    def test_launch_intent_requires_same_actual_nonce_and_closure(self):
        intent = self.save('native.launch_intent.json',{'command_nonce':'x'})
        launch = self.save('native.launch.json',{'command_nonce':'other'})
        supervisor = P.Supervisor.__new__(P.Supervisor)
        with self.assertRaises(P.Fatal): supervisor.assert_intent_closed(intent)
        P.atomic_json(launch,{'command_nonce':'x'})
        with mock.patch.object(supervisor,'assert_closed') as closed:
            supervisor.assert_intent_closed(intent)
            closed.assert_called_once_with({'command_nonce':'x'})

    def test_null_exit_cannot_be_success_or_retry_permission(self):
        path = self.save('closure.json', {'command_nonce': 'x', 'root_exit_code': None, 'group_empty': True,
                                         'tracked_descendants_empty': True})
        supervisor = P.Supervisor.__new__(P.Supervisor); supervisor.boot_id = 'boot'
        with self.assertRaises(P.Fatal):
            supervisor.assert_closed({'closure_path': str(path), 'command_nonce': 'x', 'boot_id': 'other'})

    def test_live_descendant_blocks_cache_resume(self):
        path = self.save('closure.json', {'command_nonce': 'x', 'root_exit_code': 0, 'group_empty': True,
                                         'tracked_descendants_empty': True, 'tracked_descendants': [{'pid': 7, 'start_ticks': '9'}]})
        supervisor = P.Supervisor.__new__(P.Supervisor); supervisor.boot_id = 'boot'
        launch = {'closure_path': str(path), 'command_nonce': 'x', 'boot_id': 'boot',
                  'child_pid': 1, 'child_start_ticks': '2', 'pgid': 1}
        with mock.patch.object(P, 'group_members', return_value=[]), mock.patch.object(P, 'proc_record', side_effect=[None, {'start_ticks': '9'}]):
            with self.assertRaises(P.Fatal):
                supervisor.assert_closed(launch)

    def test_completed_cache_hash_drift_rejected(self):
        path = self.root / 'raw.tsv'; path.write_text('original')
        members = {'raw.tsv': R.sha(path)}
        R.check_manifest(self.root, members)
        path.write_text('tampered')
        with self.assertRaises(P.Fatal):
            R.check_manifest(self.root, members)

    def test_manifest_traversal_and_empty_rejected(self):
        for relative in ['../outside', '/absolute', 'a\\b', 'a/../b']:
            with self.assertRaises(P.Fatal):
                R.safe_member(self.root, relative)
        with self.assertRaises(P.Fatal):
            R.check_manifest(self.root, {})

    def test_accession_outside_approved_panel_rejected(self):
        config = self.root / 'config'; config.mkdir()
        (config / 'approved_accessions.txt').write_text('\n'.join('GCF_' + str(i).zfill(9) + '.1' for i in range(196)))
        with mock.patch.object(R, 'sha', return_value=R.PINNED_PANEL):
            with self.assertRaises(P.Fatal):
                R.approved_accession(self.root, 'GCF_999999999.1')
            with self.assertRaises(P.Fatal):
                R.approved_accession(self.root, '../GCF_000000001.1')

    def test_old_four_scope_pass_is_not_new_primary_acceptance(self):
        validation = self.save('validation.json', {'status': 'PASS_HOST_PHYLOGENY_AND_SENSITIVITY_OUTPUT_INTEGRITY', 'primary_tip_ids': 196})
        publication = self.save('publication.json', {'status': 'UPLOAD_VERIFIED'})
        config = {'stage4_primary': {'validation_path': str(validation), 'validation_sha256': R.sha(validation),
                                    'publication_path': str(publication), 'publication_sha256': R.sha(publication)}}
        with self.assertRaises(P.Fatal):
            R.validate_upstream(config, self.root)

    def test_new_primary_certificate_binds_exact_relative_freeze_and_input_hashes(self):
        freeze = self.root/'.work/accepted'; freeze.mkdir(parents=True)
        members = {}
        pinned = {}
        for name in ['primary196_host_tree.nwk','primary196_host_tree.nex',
                     'accepted_primary196_concatenated.faa','accepted_original_config.json',
                     'accepted_approved_accessions.txt','accepted_primary196_partitions.nex']:
            path = freeze/name; path.write_bytes(b'SYNTHETIC '+name.encode())
            digest = {'accepted_primary196_concatenated.faa':R.PINNED_ALIGNMENT,
                      'accepted_approved_accessions.txt':R.PINNED_PANEL,
                      'accepted_primary196_partitions.nex':R.PINNED_PARTITIONS}.get(name,R.sha(path))
            pinned[path] = digest; members[path.relative_to(self.root).as_posix()] = digest
        validation = freeze/'independent_validation.json'
        record = {'schema':'STAGE04_PRIMARY_ACCEPTANCE_V1','state':'COMPLETE_VALIDATED',
            'approved_accessions_sha256':R.PINNED_PANEL,'unique_tips':196,'branch_lengths_valid':True,
            'support_completed':True,'mode':'partitioned','files':members,
            'native_tree_sha256':pinned[freeze/'primary196_host_tree.nwk'],
            'accepted_alignment_sha256':R.PINNED_ALIGNMENT}
        publication = self.root/'publication.json'
        config = {'stage4_primary':{'validation_path':str(validation),'publication_path':str(publication)}}
        actual_sha = R.sha
        def refresh():
            P.atomic_json(validation,record)
            P.atomic_json(publication,{'status':'UPLOAD_VERIFIED','final_validation_summary_sha256':actual_sha(validation),
                'remote_tag_commit_verified':True,'assets':[{'download_readback_verified':True,'all_zip_member_hashes_verified':True}]})
            config['stage4_primary'].update(validation_sha256=actual_sha(validation),publication_sha256=actual_sha(publication))
        with mock.patch.object(R,'sha',side_effect=lambda p:pinned[Path(p)] if Path(p) in pinned else actual_sha(p)):
            refresh()
            self.assertEqual(R.validate_upstream(config,self.root)['accepted_scientific_files'],members)
            record['native_tree_sha256'] = '0'*64; refresh()
            with self.assertRaises(P.Fatal): R.validate_upstream(config,self.root)
            record['native_tree_sha256'] = pinned[freeze/'primary196_host_tree.nwk']
            del members[(freeze/'primary196_host_tree.nex').relative_to(self.root).as_posix()]; refresh()
            with self.assertRaises(P.Fatal): R.validate_upstream(config,self.root)

    def test_primary_certificate_absolute_manifest_rejected(self):
        target = self.root/'native.nwk'; target.write_text('SYNTHETIC;')
        with self.assertRaises(P.Fatal): R.check_manifest(self.root,{str(target):R.sha(target)})

    def test_ambient_config_presence_bytes_and_environment_bound(self):
        env = self.root/'environment'; env.mkdir()
        home = self.root/'synthetic_home'; home.mkdir()
        prefix = env/'etc/macsyfinder'; prefix.mkdir(parents=True)
        config = prefix/'macsyfinder.conf'; config.write_text('[hmmer]\ne_value_search = 0.1\n')
        values = {'HOME':str(home),'VIRTUAL_ENV':str(env)}
        with mock.patch.dict(R.os.environ,values,clear=True),mock.patch.object(R.Path,'expanduser',return_value=home):
            frozen = R.ambient_configuration(self.root,env)
            self.assertEqual(frozen['files']['selected_system']['sha256'],R.sha(config))
            manifest = {'ambient_configuration':frozen}
            R.check_ambient_configuration(manifest,self.root,env)
            config.write_text('[hmmer]\ne_value_search = 1\n')
            with self.assertRaises(P.Fatal): R.check_ambient_configuration(manifest,self.root,env)
            config.write_text('[hmmer]\ne_value_search = 0.1\n')
            user = home/'.macsyfinder/macsyfinder.conf'; user.parent.mkdir(); user.write_text('[general]\n')
            with self.assertRaises(P.Fatal): R.check_ambient_configuration(manifest,self.root,env)
            user.unlink(); R.os.environ['MACSY_CONF'] = str(self.root/'other.conf')
            with self.assertRaises(P.Fatal): R.check_ambient_configuration(manifest,self.root,env)

    def test_relative_ambient_override_and_root_cwd_config_rejected(self):
        env = self.root/'environment'; env.mkdir()
        home = self.root/'synthetic_home'; home.mkdir()
        with mock.patch.dict(R.os.environ,{'HOME':str(home),'VIRTUAL_ENV':str(env),'MACSY_CONF':'relative.conf'},clear=True), \
             mock.patch.object(R.Path,'expanduser',return_value=home):
            with self.assertRaises(P.Fatal): R.ambient_configuration(self.root,env)
            del R.os.environ['MACSY_CONF']; (self.root/'macsyfinder.conf').write_text('[general]\n')
            with self.assertRaises(P.Fatal): R.ambient_configuration(self.root,env)

    def test_native_prelaunch_task_config_pinned_and_hmmer_resolution_checked(self):
        env = self.root/'environment'; env.mkdir()
        home = self.root/'synthetic_home'; home.mkdir()
        task = self.root/'task'; task.mkdir()
        config = task/'macsyfinder.conf'; config.write_text('[general]\nworker = 2\n')
        with mock.patch.dict(R.os.environ,{'HOME':str(home),'VIRTUAL_ENV':str(env)},clear=True), \
             mock.patch.object(R.Path,'expanduser',return_value=home):
            manifest = {'ambient_configuration':R.ambient_configuration(self.root,env)}
            guard = R.native_configuration_guard(manifest,self.root,env,{task:R.sha(config)})
            args = SimpleNamespace(environment=dict(R.os.environ,PATH='synthetic'))
            with mock.patch.object(R.shutil,'which',return_value=str(env/'bin/hmmsearch')):
                self.assertIn('ambient_configuration_sha256',guard(args,task,['macsyfinder']))
                args.environment['HOME'] = str(self.root/'other_home')
                with self.assertRaises(P.Fatal): guard(args,task,['macsyfinder'])
                args.environment['HOME'] = str(home)
                config.write_text('[general]\nworker = 8\n')
                with self.assertRaises(P.Fatal): guard(args,task,['macsyfinder'])
            config.write_text('[general]\nworker = 2\n')
            with mock.patch.object(R.shutil,'which',return_value=str(self.root/'other/hmmsearch')):
                with self.assertRaises(P.Fatal): guard(args,task,['macsyfinder'])

    def test_retained_helper_hashes_and_function_interfaces(self):
        root = Path(r'G:\My Drive\LAB_RM\lab-rm-phylogenomics-196')
        if not root.is_dir():
            self.skipTest('WD preserved source root not mounted')
        R.check_manifest(root, R.SOURCE_FILES)
        expected = {
            '.work/detector_review/build_detector_bundles.py': {'resume_one': ['source', 'out', 'accession', 'namespace_sha256']},
            '.work/detector_review/validate_detector_bundles.py': {'audit_one': ['source', 'bundle', 'out']},
            '.work/detector_review/stage05_inventory.py': {'inventory_one': ['bundle', 'execution', 'out', 'freeze', 'freeze_sha', 'padloc_roles', 'padloc_meta']},
            'scripts/validate_stage05_raw_v6.py': {'audit_assembly': ['a', 'accession', 'frozen', 'freeze_sha', 'scopes', 'source_gate', 'pad_roles', 'pad_meta', 'model_hashes']},
        }
        for filename, functions in expected.items():
            tree = ast.parse((root / filename).read_text(encoding='utf-8-sig'))
            found = {node.name: [arg.arg for arg in node.args.args] for node in tree.body if isinstance(node, ast.FunctionDef)}
            for name, signature in functions.items():
                self.assertEqual(found[name], signature)


if __name__ == '__main__':
    unittest.main()
