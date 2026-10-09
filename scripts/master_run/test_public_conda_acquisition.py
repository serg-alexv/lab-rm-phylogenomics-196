"""Small non-network guards; no package execution, extraction, or installation."""
import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('acquire',Path(__file__).with_name('acquire_public_conda_packages01.py'))
A=importlib.util.module_from_spec(spec);spec.loader.exec_module(A)

class Contracts(unittest.TestCase):
    def test_exact_existing_public_manifests(self):
        originals,records,packages=A.selected_packages()
        self.assertEqual((len(originals),len(records),len(packages),sum(p['bytes'] for p in packages)),(2,397,339,660114049))
        self.assertEqual({p['url'].split('/')[3] for p in packages},{'bioconda','conda-forge'})
    def test_forbidden_url_forms(self):
        for url in ('http://conda.anaconda.org/conda-forge/noarch/x.conda',
            'https://user@conda.anaconda.org/conda-forge/noarch/x.conda',
            'https://conda.anaconda.org/conda-forge/noarch/x.conda?token=x',
            'https://example.org/conda-forge/noarch/x.conda',
            'https://conda.anaconda.org/other/noarch/x.conda'):
            with self.subTest(url=url),self.assertRaises(ValueError):A.public_url(url)
    def test_each_resource_boundary(self):
        row=dict(physical_available_bytes=A.RESERVE,commit_headroom_bytes=A.RESERVE,c_disk_free_bytes=A.MIN_DISK)
        self.assertTrue(A.resource_passes(row))
        for key in row:
            with self.subTest(resource=key):
                below={**row,key:row[key]-1};self.assertFalse(A.resource_passes(below))

if __name__=='__main__':unittest.main()
