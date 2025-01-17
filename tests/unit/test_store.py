# package imports
import os
import unittest

import fsspec
import responses
from earthaccess import Auth, Store


class TestStoreSessions(unittest.TestCase):
    @responses.activate
    def setUp(self):
        os.environ["EDL_USERNAME"] = "user"
        os.environ["EDL_PASSWORD"] = "password"
        json_response = [
            {"access_token": "EDL-token-1", "expiration_date": "12/15/2021"},
            {"access_token": "EDL-token-2", "expiration_date": "12/16/2021"},
        ]
        responses.add(
            responses.GET,
            "https://urs.earthdata.nasa.gov/api/users/tokens",
            json=json_response,
            status=200,
        )

        self.auth = Auth().login(strategy="environment")
        self.assertEqual(self.auth.authenticated, True)
        self.assertTrue(self.auth.token in json_response)

    def tearDown(self):
        self.auth = None

    def test_store_can_create_https_fsspec_session(self):
        store = Store(self.auth)
        self.assertTrue(isinstance(store.auth, Auth))
        https_fs = store.get_fsspec_session()
        self.assertEqual(type(https_fs), type(fsspec.filesystem("https")))
        return None

    @responses.activate
    def test_store_can_create_s3_fsspec_session(self):
        from earthaccess.daac import DAACS

        responses.add(
            responses.GET,
            "https://urs.earthdata.nasa.gov/profile",
            json={},
            status=200,
        )
        for daac in DAACS:
            if "s3-credentials" in daac:
                responses.add(
                    responses.GET,
                    daac["s3-credentials"],
                    json={
                        "accessKeyId": "sure",
                        "secretAccessKey": "correct",
                        "sessionToken": "whynot",
                    },
                    status=200,
                )
        store = Store(self.auth)
        self.assertTrue(isinstance(store.auth, Auth))
        for daac in ["NSIDC", "PODAAC", "LPDAAC", "ORNLDAAC", "GES_DISC"]:
            s3_fs = store.get_s3fs_session(daac=daac)
            self.assertEqual(type(s3_fs), type(fsspec.filesystem("s3")))

        for provider in ["NSIDC_CPRD", "POCLOUD", "LPCLOUDa", "ORNLCLOUD", "GES_DISC"]:
            s3_fs = store.get_s3fs_session(provider=provider)
            assert isinstance(s3_fs, fsspec.AbstractFileSystem)
        return None
