"""Standard-library-only regression checks for the reusable snippets."""
import errno
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import Mock, patch

import exponential_backoff as backoff
import file_locations as locations


class BackoffTests(unittest.TestCase):
    def test_exponential_delays_and_cap(self):
        event=threading.Event()
        operation=Mock(side_effect=[TimeoutError('offline')]*4+['done'])
        with patch.object(event,'wait',return_value=False) as wait:
            result=backoff.exponential_backoff(operation,retries=4,delay=1,max_delay=3,
                                               jitter=0,stop_event=event,on_retry=None)
        self.assertEqual(result,'done')
        self.assertEqual([call.args[0] for call in wait.call_args_list],[1,2,3,3])

    def test_finite_budget_preserves_error(self):
        error=OSError(errno.EIO,'offline')
        operation=Mock(side_effect=error)
        with self.assertRaises(OSError) as caught:
            backoff.exponential_backoff(operation,retries=2,delay=0,max_delay=0,on_retry=None)
        self.assertIs(caught.exception,error)
        self.assertEqual(operation.call_count,3)

    def test_permanent_failure_is_not_retried(self):
        operation=Mock(side_effect=PermissionError(errno.EACCES,'denied'))
        with self.assertRaises(PermissionError):
            backoff.exponential_backoff(operation,on_retry=None)
        self.assertEqual(operation.call_count,1)

    def test_custom_predicate_supports_service_errors(self):
        operation=Mock(side_effect=[RuntimeError('busy'),42])
        result=backoff.exponential_backoff(operation,retries=1,delay=0,max_delay=0,
                    retry_if=lambda error:isinstance(error,RuntimeError),on_retry=None)
        self.assertEqual(result,42)

    def test_cancellation_wakes_wait(self):
        event=threading.Event()
        operation=Mock(side_effect=TimeoutError('offline'))
        with self.assertRaises(backoff.RetryCancelled):
            backoff.exponential_backoff(operation,delay=30,max_delay=30,stop_event=event,
                                        on_retry=lambda *args:event.set())
        self.assertEqual(operation.call_count,1)

    def test_invalid_configuration(self):
        with self.assertRaises(ValueError):
            backoff.exponential_backoff(lambda:None,retries=-1)


class LocationTests(unittest.TestCase):
    def test_local_files_and_directories(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory).resolve()
            file=root/'a file.txt';file.write_text('hello')
            self.assertEqual(locations.resolve_file_location(file),(file,None))
            self.assertEqual(locations.resolve_file_location(root,require_directory=True),(root,None))
            with self.assertRaises(ValueError):
                locations.resolve_file_location(file,require_directory=True)

    def test_encoded_smb_names(self):
        parsed=locations.parse_smb('smb://reader@fileserver.example/books/Library%20With%20Spaces/file%23.txt')
        self.assertEqual(parsed.parts,('Library With Spaces','file#.txt'))
        self.assertEqual(locations.parse_smb(parsed.uri),parsed)

    @unittest.skipIf(os.name=='nt','Linux mount discovery fixture')
    def test_kio_fuse_file_and_directory(self):
        url='smb://reader@fileserver.example/books/Library With Spaces'
        with tempfile.TemporaryDirectory() as directory:
            mount=Path(directory)/'kio-fuse-session'
            folder=mount/'smb'/'reader@fileserver.example'/'books'/'Library With Spaces'
            folder.mkdir(parents=True)
            file=folder/'a file.txt';file.write_text('hello')
            with patch.object(locations,'linux_smb_mounts',return_value=[]), \
                 patch.object(locations,'gvfs_smb_mounts',return_value=[]), \
                 patch.object(locations,'kio_fuse_roots',return_value=[mount]):
                self.assertEqual(locations.resolve_file_location(url,require_directory=True)[0],folder.resolve())
                self.assertEqual(locations.resolve_file_location(url+'/a%20file.txt')[0],file.resolve())

    def test_explicit_native_mapping(self):
        with tempfile.TemporaryDirectory() as directory:
            file=Path(directory)/'a.txt';file.write_text('hello')
            result=locations.resolve_file_location('smb://reader@fileserver.example/books/a.txt',mount_path=file)
            self.assertEqual(result[0],file.resolve())

    def test_traversal_and_passwords_are_rejected(self):
        for url in ('smb://server/books/../other','smb://reader:password@server/books'):
            with self.subTest(url=url),self.assertRaises(ValueError):locations.parse_smb(url)


class ImportTests(unittest.TestCase):
    def test_each_helper_works_without_the_other_helper_file(self):
        root=Path(__file__).resolve().parents[1]
        for helper,call in (
            ('exponential_backoff','assert easy_mode.exponential_backoff(lambda:42,on_retry=None)==42'),
            ('file_locations','assert easy_mode.resolve_file_location(sys.argv[1])[0].is_dir()'),
        ):
            with self.subTest(helper=helper),tempfile.TemporaryDirectory() as directory:
                stage=Path(directory)
                for name in ('easy_mode',helper):
                    (stage/(name+'.py')).write_bytes((root/(name+'.py')).read_bytes())
                code='import sys;sys.path.insert(0,sys.argv[1]);import easy_mode;'+call
                result=subprocess.run([sys.executable,'-I','-S','-c',code,str(stage)],
                                      capture_output=True,text=True,timeout=10)
                self.assertEqual(result.returncode,0,result.stderr)

    def test_lazy_entry_points_without_site_packages(self):
        root=Path(__file__).resolve().parents[1]
        code="""
import sys
sys.path.insert(0,sys.argv[1])
import easy_mode
assert 'exponential_backoff' not in sys.modules
assert 'file_locations' not in sys.modules
assert easy_mode.exponential_backoff(lambda:42,on_retry=None)==42
assert 'file_locations' not in sys.modules
path,uri=easy_mode.resolve_file_location(sys.argv[1],require_directory=True)
assert path.is_dir() and uri is None
assert not any(name in sys.modules for name in ('PIL','numpy','flask','selenium','requests'))
"""
        result=subprocess.run([sys.executable,'-I','-S','-c',code,str(root)],
                              capture_output=True,text=True,timeout=10)
        self.assertEqual(result.returncode,0,result.stderr)


if __name__=='__main__':unittest.main()
