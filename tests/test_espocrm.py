import asyncio
import json
import os
import unittest
from unittest.mock import patch

import httpx

from app.tools import espocrm


class EspoCRMToolTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        os.environ['ESPOCRM_BASE_URL'] = 'http://testserver'
        os.environ['ESPOCRM_API_KEY'] = 'dummy'
        espocrm._espocrm_service = espocrm.EspoCRMService('http://testserver', 'dummy')

    async def test_get_contacts(self):
        expected = {"list": [{"name": "John Doe"}]}

        async def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=expected)

        transport = httpx.MockTransport(handler)

        class PatchedAsyncClient(httpx.AsyncClient):
            def __init__(self, *args, **kwargs):
                super().__init__(transport=transport)

        with patch('app.tools.espocrm.httpx.AsyncClient', PatchedAsyncClient):
            result = await espocrm.espocrm_get_contacts(limit=1)
            self.assertEqual(json.loads(result), expected)


if __name__ == '__main__':
    unittest.main()
