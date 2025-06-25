import subprocess
import shutil
import unittest

import yaml


def load_compose():
    with open('docker-compose.yml') as f:
        return yaml.safe_load(f)


class DockerComposeTest(unittest.TestCase):
    def test_services_present(self):
        data = load_compose()
        services = data.get('services', {})
        self.assertIn('mcp-server', services)
        self.assertIn('espocrm', services)
        self.assertIn('espocrm-db', services)
        volumes = data.get('volumes', {})
        self.assertIn('espocrm_db', volumes)
        self.assertIn('espocrm_data', volumes)

    def test_compose_config_valid(self):
        docker = shutil.which('docker')
        if not docker:
            self.skipTest('Docker not available')
        try:
            subprocess.run(
                [docker, 'compose', '-f', 'docker-compose.yml', 'config'],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except subprocess.CalledProcessError as e:
            self.fail(f'Docker compose config failed: {e.stderr.decode()}')


if __name__ == '__main__':
    unittest.main()
