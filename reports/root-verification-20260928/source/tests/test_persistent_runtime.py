"""Persistent policy/filesystem fault tests; adapter is an explicit host double."""
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from contextlib import redirect_stdout
import io
import json

from controller_config.model import ConfigurationError
from controller_config.persistent_runtime import PersistentRuntimeService, _sealed, _write
from controller_config.service import read_json
from controller_config.runtime import RuntimeConfigurationService
from test_runtime_configuration import Adapter


class PersistentAdapter(Adapter):
    def __init__(self):
        super().__init__()
        self.value.update(persistence_required=True, persistence_pending=True,
                          persistence_generation=0, persistence_hash='0'*64,
                          config_locked=True, machine_id='29ec6d59-6e25-4986-95a2-92cc10cfdc1d',
                          profile_sha256='a'*64)

    def transaction(self, op, state, scales=None, persistent=None, *, deadline=None):
        if op == 4:
            self.operations.append(op)
            self.value.update(config_locked=True, persistence_pending=True)
        elif op == 5:
            self.operations.append(op)
            self.value.update(persistence_pending=False, persistence_generation=persistent['generation'], persistence_hash=persistent['sha256'])
        elif op == 3 and self.value['persistence_pending']:
            raise ConfigurationError('COMPILED_GUARD_REJECTED', 'Pending persistence')
        else:
            super().transaction(op, state, scales, deadline=deadline)


class Interrupted(Exception):
    pass


class PersistentRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.adapter = PersistentAdapter()
        self.now = 1_000_000_000
        self.service = PersistentRuntimeService(self.adapter,self.temp.name,clock=lambda:self.now)

    def reject(self, code, function, *args):
        with self.assertRaises(ConfigurationError) as caught:
            function(*args)
        self.assertEqual(caught.exception.code,code)

    def initialize(self):
        return self.service.initialize([250,200,200,200,200,200])

    def restart(self):
        self.adapter = PersistentAdapter()
        self.adapter.value['instance'][2] += 1
        self.service = PersistentRuntimeService(self.adapter,self.temp.name,clock=lambda:self.now)

    def test_new_machine_init_is_explicit_and_unhomed(self):
        self.reject('PERSISTENCE_MISSING',self.service.status)
        result = self.initialize()
        self.assertEqual(result['generation'],1)
        self.assertEqual(result['runtime']['scales'][0],250)
        self.assertFalse(any(result['runtime']['homed']))
        self.assertFalse(result['runtime']['enabled'])
        self.assertEqual(self.adapter.operations,[4,2,5,3])

    def test_separate_instance_reconciles_saved_scale(self):
        self.initialize(); self.restart()
        self.assertTrue(self.adapter.value['config_locked'])
        self.assertEqual(self.adapter.value['scales'][0],200)
        result=self.service.reconcile()
        self.assertEqual(result['runtime']['scales'][0],250)
        self.assertFalse(result['runtime']['enabled'])

    def test_init_cannot_overwrite(self):
        self.initialize(); self.restart()
        self.reject('PERSISTENCE_EXISTS',self.initialize)

    def test_public_volatile_apply_and_recovery_cannot_bypass(self):
        self.reject('PERSISTENT_AUTHORITY_REQUIRED',RuntimeConfigurationService(self.adapter).recover_inhibit)
        self.initialize()
        core=RuntimeConfigurationService(self.adapter,clock=lambda:self.now)
        plan=core.preview([300,200,200,200,200,200])
        self.reject('PERSISTENT_AUTHORITY_REQUIRED',core.apply,plan)

    def test_durable_change_and_reversal_advance_generation(self):
        self.initialize()
        self.service.apply(self.service.preview([300,200,200,200,200,200]))
        result=self.service.apply(self.service.preview([250,200,200,200,200,200]))
        self.assertEqual(result['generation'],3)
        self.assertEqual(result['runtime']['scales'][0],250)

    def test_init_interruption_each_phase_reconciles(self):
        for phase in ('journal_durable','witness_durable','runtime_activated','committed_durable','gate_committed','released'):
            with self.subTest(phase=phase), tempfile.TemporaryDirectory() as directory:
                adapter=PersistentAdapter()
                def checkpoint(current):
                    if current==phase: raise Interrupted(phase)
                service=PersistentRuntimeService(adapter,directory,checkpoint=checkpoint)
                with self.assertRaises(Interrupted): service.initialize([250,200,200,200,200,200])
                if phase!='released': self.assertTrue(adapter.value['config_locked'])
                restarted=PersistentRuntimeService(PersistentAdapter(),directory)
                self.assertEqual(restarted.recover()['runtime']['scales'][0],250)

    def test_apply_interruption_each_phase_reconciles(self):
        for phase in ('journal_durable','witness_durable','runtime_activated','committed_durable','gate_committed','released'):
            with self.subTest(phase=phase), tempfile.TemporaryDirectory() as directory:
                adapter=PersistentAdapter(); service=PersistentRuntimeService(adapter,directory)
                service.initialize([200]*6)
                plan=service.preview([250,200,200,200,200,200])
                def checkpoint(current):
                    if current==phase: raise Interrupted(phase)
                service.checkpoint=checkpoint
                with self.assertRaises(Interrupted): service.apply(plan)
                restarted=PersistentRuntimeService(PersistentAdapter(),directory)
                result=restarted.recover()
                self.assertEqual(result['runtime']['scales'][0],250)
                self.assertEqual(result['generation'],2)

    def test_interrupted_same_instance_recovers_after_gate_ack(self):
        self.initialize()
        def checkpoint(phase):
            if phase=='gate_committed': raise Interrupted()
        self.service.checkpoint=checkpoint
        with self.assertRaises(Interrupted):self.service.apply(self.service.preview([300,200,200,200,200,200]))
        self.assertTrue(self.adapter.value['config_locked'])
        self.service.checkpoint=lambda phase:None
        self.assertEqual(self.service.recover()['runtime']['scales'][0],300)

    def test_corrupt_journal_remains_inhibited(self):
        self.initialize(); self.restart()
        self.service.journal.write_text('{broken')
        self.reject('INVALID_JSON',self.service.reconcile)
        self.assertTrue(self.adapter.value['config_locked'])

    def test_valid_older_authority_conflicts_with_witness(self):
        self.initialize(); old=self.service.journal.read_bytes()
        self.service.apply(self.service.preview([300,200,200,200,200,200]))
        self.service.journal.write_bytes(old); self.restart()
        self.reject('PERSISTENCE_CONFLICT',self.service.reconcile)

    def test_same_generation_different_record_hash_conflicts(self):
        self.initialize(); self.restart()
        journal=read_json(self.service.journal); record=journal['committed']; record.pop('sha256');record['scales'][0]=300
        journal.pop('sha256');journal['committed']=_sealed(record);_write(self.service.journal,_sealed(journal))
        self.reject('PERSISTENCE_CONFLICT',self.service.reconcile)

    def test_foreign_machine_profile_caps_refused(self):
        self.initialize()
        original=self.service.journal.read_bytes()
        for key,value in (('machine_id','393e2a66-b026-4543-943e-8bff02e70fa1'),('profile_sha256','b'*64),('capabilities',{})):
            with self.subTest(key=key):
                self.service.journal.write_bytes(original); self.restart()
                journal=read_json(self.service.journal); record=journal['committed'];record.pop('sha256');record[key]=value
                journal.pop('sha256');journal['committed']=_sealed(record);_write(self.service.journal,_sealed(journal))
                self.reject('PERSISTENCE_IDENTITY',self.service.reconcile)

    def test_missing_witness_for_committed_authority_refused(self):
        self.initialize(); self.service.witness.unlink(); self.restart()
        self.reject('PERSISTENCE_WITNESS_MISSING',self.service.reconcile)

    def test_stale_preview_cannot_replace_new_generation(self):
        self.initialize(); plan=self.service.preview([300,200,200,200,200,200])
        self.service.apply(plan)
        self.reject('PERSISTENCE_STALE',self.service.apply,plan)

    def test_expiry_during_journal_write_retains_pending_inhibit(self):
        self.initialize();plan=self.service.preview([300,200,200,200,200,200])
        def checkpoint(phase):
            if phase=='journal_durable':self.now+=60_000_000_001
        self.service.checkpoint=checkpoint
        self.reject('RUNTIME_EXPIRED',self.service.apply,plan)
        self.assertTrue(self.adapter.value['persistence_pending'])
        self.assertEqual(self.adapter.value['scales'][0],250)

    def test_epoch_change_during_fsync_refused(self):
        self.initialize();plan=self.service.preview([300,200,200,200,200,200])
        def checkpoint(phase):
            if phase=='journal_durable':self.adapter.value['epoch']+=1
        self.service.checkpoint=checkpoint
        self.reject('RUNTIME_STALE',self.service.apply,plan)
        self.assertTrue(self.adapter.value['config_locked'])

    def test_machine_enable_during_fsync_refused(self):
        self.initialize();plan=self.service.preview([300,200,200,200,200,200])
        def checkpoint(phase):
            if phase=='committed_durable':self.adapter.value['enabled']=True
        self.service.checkpoint=checkpoint
        self.reject('RUNTIME_UNSAFE',self.service.apply,plan)
        self.assertTrue(self.adapter.value['persistence_pending'])

    def test_changed_durable_readback_cannot_release(self):
        self.initialize();plan=self.service.preview([300,200,200,200,200,200])
        def checkpoint(phase):
            if phase=='committed_durable':self.service.witness.write_text('{}')
        self.service.checkpoint=checkpoint
        self.reject('PERSISTENCE_FORMAT',self.service.apply,plan)
        self.assertTrue(self.adapter.value['config_locked'])

    def test_live_generation_prevents_rollback_even_both_files_old(self):
        self.initialize();journal=self.service.journal.read_bytes();witness=self.service.witness.read_bytes()
        self.service.apply(self.service.preview([300,200,200,200,200,200]))
        self.service.journal.write_bytes(journal);self.service.witness.write_bytes(witness)
        self.reject('PERSISTENCE_ROLLBACK',self.service.reconcile)

    def test_modified_caller_plan_cannot_change_commit(self):
        self.initialize();plan=self.service.preview([300,200,200,200,200,200])
        def checkpoint(phase):
            if phase=='journal_durable':plan['runtime']['after'][0]=350
        self.service.checkpoint=checkpoint
        self.assertEqual(self.service.apply(plan)['runtime']['scales'][0],300)

    def test_expiry_during_final_disk_read_keeps_inhibit(self):
        self.initialize();plan=self.service.preview([300,200,200,200,200,200])
        original=self.service._read
        def slow_read(state):
            result=original(state)
            if not state['persistence_pending'] and state['config_locked']:
                self.now+=60_000_000_001
            return result
        self.service._read=slow_read
        self.reject('RUNTIME_EXPIRED',self.service.apply,plan)
        self.assertTrue(self.adapter.value['config_locked'])

    def test_epoch_change_during_final_disk_read_keeps_inhibit(self):
        self.initialize();plan=self.service.preview([300,200,200,200,200,200])
        original=self.service._read
        def changed_read(state):
            result=original(state)
            if not state['persistence_pending'] and state['config_locked']:
                self.adapter.value['epoch']+=1
            return result
        self.service._read=changed_read
        self.reject('RUNTIME_STALE',self.service.apply,plan)
        self.assertTrue(self.adapter.value['config_locked'])

    def test_exponent_overflow_corrupt_record_returns_structured_error(self):
        self.initialize();self.restart()
        text=self.service.journal.read_text()
        self.service.journal.write_text(text.replace('250.0','1e1000',1))
        self.reject('PERSISTENCE_FORMAT',self.service.reconcile)
        self.assertTrue(self.adapter.value['config_locked'])

    def test_new_directory_chain_syncs_parent_names_before_file_commit(self):
        root=Path(self.temp.name); target=root/'new'/'nested'/'record.json';calls=[]
        with patch('controller_config.persistent_runtime._sync_directory',side_effect=lambda p:calls.append(Path(p))):
            _write(target,{'test':True})
        self.assertEqual(calls,[root,root/'new',root/'new',root/'new'/'nested',root/'new'/'nested'])

    def test_directory_fsync_failure_keeps_pending_inhibit(self):
        self.service=PersistentRuntimeService(self.adapter,Path(self.temp.name)/'new')
        with patch('controller_config.persistent_runtime._sync_directory',side_effect=OSError('injected fsync failure')):
            self.reject('PERSISTENCE_IO',self.initialize)
        self.assertTrue(self.adapter.value['config_locked'])
        self.assertTrue(self.adapter.value['persistence_pending'])

    def test_activation_and_release_receive_original_deadline(self):
        self.initialize();plan=self.service.preview([300,200,200,200,200,200])
        received=[];original=self.adapter.transaction
        def observed(op,state,scales=None,persistent=None,*,deadline=None):
            received.append((op,deadline))
            return original(op,state,scales,persistent,deadline=deadline)
        self.adapter.transaction=observed
        self.service.apply(plan)
        self.assertEqual(received,[(op,plan['runtime']['expires_monotonic_ns']) for op in (4,2,5,3)])

    def test_cli_versioned_success_and_structured_failures(self):
        from controller_config.persistent_runtime import main
        self.initialize()
        for error,code in ((None,None),(ConfigurationError('PERSISTENCE_MISSING','no store'),'PERSISTENCE_MISSING'),(OSError('unavailable directory'),'IO_ERROR')):
            with self.subTest(code=code),patch('controller_config.persistent_runtime.LinuxCNCRTLAdapter',return_value=self.adapter,side_effect=error),redirect_stdout(io.StringIO()) as output:
                result=main(['--directory',self.temp.name,'status'])
            value=json.loads(output.getvalue())
            self.assertEqual(value['schema_version'],1)
            self.assertEqual(result,2 if error else 0)
            self.assertEqual(value['ok'],not bool(error))
            if error:self.assertEqual(value['error']['code'],code)


if __name__=='__main__':unittest.main()
