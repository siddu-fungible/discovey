#!/usr/bin/env python2.7
#
# Test Storage Controller APIs from outside.
#
# StorageController and single FS should be running on local machine.
#

import argparse
import datetime
import json
import os
import random
import requests
import socket
import sys
import time
import unittest
import uuid

MEGABYTE = 1024 * 1024
GIGABYTE = 1024 * MEGABYTE

# Maximum time to wait for response from StorageController.
TIMEOUT_SECS = 10


def execute_command(method, cmd_url, params, show_exceptions=True):
    """Perform an HTTP request to StorageController.

    method: HTTP method.  GET, POST, DELETE, PATCH.
    cmd_url: partial URL for request.
    params: dictionary of additional arguments for POST>
    """
   #if 'SC_HOST' not in os.environ:
   #    raise Exception('Missing environment variable',
   #                    'SC_HOST not set')
    #controller = os.environ['SC_HOST']
    controller = "fs141-come"
    headers = {'content-type': 'application/json'}
    agent_url = 'http://fs141-come:50220/FunCC/v1/{}'.format(cmd_url)
    #agent_url = 'http://fs141-come:50220/FunCC/v1/storage/pools'
    basic_auth = requests.auth.HTTPBasicAuth('admin', 'password')
    r = None

    now = datetime.datetime.now()
    date_str = now.strftime("%d/%m/%Y %H:%M:%S")

    print('{}: Executing {} {}'.format(date_str, method, cmd_url))
    try:
        if method == 'POST':
            r = requests.post(agent_url, json=params, headers=headers,
                              auth=basic_auth, timeout=TIMEOUT_SECS)
        elif method == 'GET':
            r = requests.get(agent_url, json=params, headers=headers,
                             auth=basic_auth, timeout=TIMEOUT_SECS)
        elif method == 'DELETE':
            r = requests.delete(agent_url, json=params, headers=headers,
                                auth=basic_auth, timeout=TIMEOUT_SECS)
        elif method == 'PATCH':
            r = requests.patch(agent_url, json=params, headers=headers,
                               auth=basic_auth, timeout=TIMEOUT_SECS)
        elif method == 'PUT' :
            r = requests.put(agent_url, json=params, headers=headers,
                               auth=basic_auth, timeout=TIMEOUT_SECS)
        else :
            print 'Unknown method {}'.format(method)
            return None
    except requests.exceptions.Timeout as to:
        print('Timeout waiting for request.'
              'Is StorageController running?')
        return None
    except Exception as ex:
        if show_exceptions:
            print("execute_command exception: ", str(ex))
        return None
    return r

def dpu_format_drives(dpu_id) :
    r = execute_command('GET', 'topology/dpus/{}'.format(dpu_id), None)
    try :
        if r.status_code == 200 :
            resp = r.json()
            if resp['status'] == True :
                drives = resp["data"]["drives"]
                for drive_info in drives :
                    drive_uuid = drive_info["uuid"]
                    format_ok = drive_format(drive_uuid)
                    if format_ok == False :
                        return False
        else :
            print('status code for GET topology is {}'.format(r.status_code))
    except Exception as e:
        print('dpu get exception: ', str(e))
        return False
    return True

def drive_format(drive_uuid) :
    params = {}
    r = execute_command('PUT', 'topology/drives/{}'.format(drive_uuid), params)
    try :
        if r.status_code == 200 :
            resp = r.json()
            print("format command response {} {}".format(drive_uuid, resp))
            if resp['status'] == True :
                return
        else :
            print('status code for format of drive {} is {}'.format(drive_uuid, r.status_code))
    except Exception as e:
        print('drive format exception: ', str(e))


class SimpleAPITest(unittest.TestCase):
    """Test StorageController APIs.

    Code uses raw HTTP requests to document what precisely is run.
    """

    @classmethod
    def setUpClass(cls):
        """Checks that environment is correct before tests begin."""
        # TODO(bowdidge): Initialize docker here?


        if not os.path.exists('/workspace/StorageController'):
            print('/workspace/StorageController does not exist, '
                  'which may mean test is not running in docker.')
            print('Start containers and run test with run_single_fs_test.py')
            sys.exit(1)

        workspace = os.environ.get('WORKSPACE', None)

        if not workspace:
            print('Workspace not set, exiting.')
            sys.exit(1)

        # Drop a file in the test's directory to indicate at least one test
        # started.
        # This allows us to catch cases where docker failed to start all
        # containers.
        started_file = os.path.join(workspace, 'single_fs', 'TEST_STARTED')
        with open(started_file, 'w') as f:
            f.write('Test started')

        tries = 18
        print('Waiting for VMs to fully start.')
        for i in range(tries):
            time.sleep(10)
            r = execute_command('GET', 'storage/pools', None, show_exceptions=False)
            if not r or r.status_code != 200:
                print('No VMs present')
                continue
            time.sleep(10)
            resp = r.json()
            if 'status' not in resp:
                print('Malformed response')
                continue
            if resp['status'] != True:
                print('Status is not true')
                continue
            if 'data' not in resp:
                print('No data')
                continue
            pool_data = resp['data']

            if len(pool_data) == 0:
                print ('No pools')
                continue
            global_pool = pool_data[pool_data.keys()[0]]
            if 'dpus' not in global_pool:
                print('No dpus')
                continue
            if len(global_pool['dpus']) < 1:
                print 'dpu count is {}'.format(len(global_pool['dpus']))
                continue

            #get topology and format drives
            dpus = global_pool["dpus"]
            for dpu in dpus :
                ok = dpu_format_drives(dpu)
                if not ok :
                    #Keep retrying to format drive for now
                    continue

            return True

        print('Testbed not ready after {} tries.'.
              format(tries))
        sys.exit(1)

    @classmethod
    def tearDownClass(cls):
        """Gather additional debugging information after tests complete."""
        pass

    def setUp(self):
        """Prepare for each individual test."""
        self.ip_address = socket.gethostbyname(socket.gethostname())

    def tearDown(self):
        pass
        # Check that no volumes still exist.

    def check_alive(self):
        """Returns true if StorageController is reachable.

        Tests should just bail out if StorageController becomes unreachable.
        """
        r = execute_command('GET', 'storage/pools', None)
        return r and r.status_code == 200

    def get_random_pool(self):
        """Return name of a random pool on StorageController.

        Because test involves only a single machine, we should only
        have a single pool.
        """
        r = execute_command('GET', 'storage/pools', None)
        if r.status_code != 200 :
            return None

        try:
            resp = r.json()
            if resp['status'] != True:
                return None

            pools = resp['data']
            if len(pools) == 0 :
                return None
            return random.choice(pools.keys())
        except Exception as ex:
            return None

    def create_raw_volume(self, pool_uuid, raw_vol_name=None,
                          capacity=100 * MEGABYTE):
        """Create a raw volume quickly.

        Returns (data, uuid), or None if create failed.
        """

        if not raw_vol_name:
            raw_vol_name = "raw-{}".format(str(uuid.uuid4())[:8])

        raw_vol_params = {
            'capacity': capacity,
            'name': raw_vol_name,
            'vol_type': 'VOL_TYPE_BLK_LOCAL_THIN',
            'data_protection': {}
            }

        r = execute_command('POST', 'storage/pools/' + pool_uuid + '/volumes',
                            raw_vol_params)
        if r.status_code != 200:
            print('create_raw_volume: create failed, r was {}'.format(
                r.status_code))
            return None

        resp = r.json()
        if resp['status'] != True:
            print('create_raw_volume: create failed: {}'.format(resp))
            return None

        vol_data = resp['data']
        volume_uuid = vol_data['uuid']
        return (vol_data, volume_uuid)

    def delete_volume(self, volume_data, volume_uuid):
        """Deletes created volume as part of cleanup.

        Returns True if delete succeeded.
        """
        r = execute_command(
            'DELETE',
            'storage/volumes/{}'.format(volume_uuid), {})
        if r.status_code != 200:
            print('Problems deleting volume: status code was {}'.format(
                r.status_code))
            return False
        resp = r.json()
        if not resp['status']:
            print('Problems deleting volume: status code was {}'.format(
                resp))
            return False
        return True

    def testCheckPools(self):
        """Check we can retrieve list of available pools."""
        r = execute_command('GET', 'storage/pools', None)
        self.assertIsNotNone(r)
        self.assertEqual(200, r.status_code)

        resp = r.json()
        self.assertEquals(True, resp['status'])

        pools = resp['data']
        self.assertGreaterEqual(1, len(pools))

    def testHasGlobalPool(self):
        """Check that global pool exists and is configured."""
        pool = self.get_random_pool()
        self.assertIsNotNone(pool)

        r = execute_command('GET', 'storage/pools/' + pool, None)
        self.assertIsNotNone(r, msg='Connection failed')
        self.assertEqual(200, r.status_code)

        resp = r.json()
        self.assertEquals(True, resp['status'])

        pool_data = resp['data']
        print pool_data
        self.assertEqual('global', pool_data['name'])
        self.assertLessEqual(0, len(pool_data['volumes']))
        self.assertLessEqual(1, len(pool_data['dpus']))

    def testCreateRawVolume(self):
        """Checks we can create and destroy a raw volume."""
        pool_uuid = self.get_random_pool()
        self.assertIsNotNone(pool_uuid)

        raw_vol_name = "raw-{}".format(str(uuid.uuid4())[:8])

        raw_vol_params = {
            'capacity': 100 * MEGABYTE,
            'name': raw_vol_name,
            'vol_type': 'VOL_TYPE_BLK_LOCAL_THIN',
            'data_protection': {}
            }

        r = execute_command('POST', 'storage/pools/' + pool_uuid + '/volumes',
                            raw_vol_params)
        self.assertEqual(200, r.status_code)

        resp = r.json()
        self.assertEquals(True, resp['status'],
                          msg='problem creating volume' +
                          resp.get('error-message', ''))

        vol_data = resp['data']
        volume_uuid = vol_data['uuid']

        r = execute_command('DELETE',
                            'storage/volumes/{}'.format(volume_uuid), {})
        self.assertEqual(200, r.status_code)
        resp = r.json()
        self.assertTrue(resp['status'])

    def testCreateRawVolumeRepeatedly(self):
        """Checks we can create and destroy a raw volume."""
        pool_uuid = self.get_random_pool()
        self.assertIsNotNone(pool_uuid)

        for i in range(0, 100):
            r = self.create_raw_volume(pool_uuid)
            self.assertIsNotNone(r, msg='problem creating volume')

            (data, uuid) = r
            self.assertTrue(self.delete_volume(data, uuid),
                            msg='probems deleting volume')

    def testCreateRawVolumeLargerThanSpace(self):
        """Checks that we can't allocate more than the FS holds.

        Each FS has four 2GB drives, so we shouldn't be able to allocate
        more than 8 GB.
        """
        pool_uuid = self.get_random_pool()
        self.assertIsNotNone(pool_uuid)

        raw_vol_name = "toobig-raw-{}".format(str(uuid.uuid4())[:8])

        raw_vol_params = {
            'capacity': 10 * GIGABYTE,
            'name': raw_vol_name,
            'vol_type': 'VOL_TYPE_BLK_LOCAL_THIN',
            'data_protection': {}
            }

        r = execute_command('POST', 'storage/pools/' + pool_uuid + '/volumes',
                            raw_vol_params)
        self.assertEqual(200, r.status_code)

        resp = r.json()

        if resp['status'] == True:
            # Oops - volume got created.  Delete it before logging message.
            self.delete_volume(resp['data'], resp['uuid'])

        # and flag error if the allocation succeeded.
        self.assertEquals(False, resp['status'],
                          msg='expected too-big allocation to fail, but it '
                          'succeeded')

    def testAttachRawVolume(self):
        """Checks we can mount and unmount a raw volume."""
        pool_uuid = self.get_random_pool()
        self.assertIsNotNone(pool_uuid)

        raw_vol_name = "raw-{}".format(str(uuid.uuid4())[:8])

        raw_vol_params = {
            'capacity': 100 * MEGABYTE,
            'name': raw_vol_name,
            'vol_type': 'VOL_TYPE_BLK_LOCAL_THIN',
            'data_protection': {}
            }

        r = execute_command('POST', 'storage/pools/' + pool_uuid + '/volumes',
                            raw_vol_params)
        self.assertEqual(200, r.status_code)

        resp = r.json()
        self.assertEquals(True, resp['status'],
                          msg='problem creating volume' +
                          resp.get('error-message', ''))

        vol_data = resp['data']
        volume_uuid = vol_data['uuid']

        # Mount volume.
        #params = {'remote_ip': self.ip_address, 'transport': 'TCP'}
        params = {'host_nqn': 'nqn.2015-09.com.fungible:testpy-host',
                  'transport': 'TCP'}
        r = execute_command('POST',
                            'storage/volumes/{}/ports'.format(volume_uuid),
                            params)

        self.assertEqual(200, r.status_code)
        resp = r.json()
        self.assertTrue(resp.get('status'))

        print 'Response from attach is %s' % resp
        attach_port = resp['data']
        attach_uuid = attach_port['uuid']

        # Unmount volume.
        r = execute_command('DELETE', 'storage/ports/{}'.format(attach_uuid),
                            params)
        self.assertEqual(200, r.status_code)
        resp = r.json()

        # Delete volume.
        r = execute_command('DELETE',
                            'storage/volumes/{}'.format(volume_uuid), {})
        self.assertEqual(200, r.status_code)
        resp = r.json()
        self.assertTrue(resp['status'])

    def testTopologyRawVolume(self):
        """Checks that topology info for raw volume is expected."""
        pool_uuid = self.get_random_pool()
        self.assertIsNotNone(pool_uuid)

        raw_vol_name = "raw-{}".format(str(uuid.uuid4())[:8])

        raw_vol_params = {
            'capacity': 104857600,
            'name': raw_vol_name,
            'vol_type': 'VOL_TYPE_BLK_LOCAL_THIN',
            'data_protection': {}
            }

        r = execute_command('POST', 'storage/pools/' + pool_uuid + '/volumes',
                            raw_vol_params)
        self.assertEqual(200, r.status_code)

        resp = r.json()
        self.assertEquals(True, resp['status'],
                          msg='problem creating volume' +
                          resp.get('error-message', ''))

        vol_data = resp['data']
        volume_uuid = vol_data['uuid']

        r = execute_command('GET', 'storage/volumes/{}/topology'.format(
                volume_uuid), None)
        self.assertEqual(200, r.status_code,
                         msg='problem getting topology' +
                         resp.get('error-message', ''))
        self.assertTrue(r.status_code)
        resp = r.json()
        print 'topology was %s' % resp
        data = resp.get('data')
        self.assertEqual(4096, data['stats']['stats']['flvm_block_size'])
        self.assertEqual(0, data['stats']['stats']['num_reads'])
        # TODO(bowdidge): Check other expected return values.

        r = execute_command('DELETE',
                            'storage/volumes/{}'.format(volume_uuid), {})
        self.assertEqual(200, r.status_code)
        resp = r.json()
        self.assertTrue(resp['status'])

    def testMountRawVolume(self):
        """Test we can make a volume accessible."""
        pool_uuid = self.get_random_pool()
        self.assertIsNotNone(pool_uuid)

        raw_vol_name = "raw-{}".format(str(uuid.uuid4())[:8])

        raw_vol_params = {
            'capacity': 104857600,
            'name': raw_vol_name,
            'vol_type': 'VOL_TYPE_BLK_LOCAL_THIN',
            'data_protection': {}
            }

        r = execute_command('POST', 'storage/pools/' + pool_uuid + '/volumes',
                            raw_vol_params)
        self.assertEqual(200, r.status_code)

        resp = r.json()
        self.assertEquals(True, resp['status'],
                          msg='problem creating volume' +
                          resp.get('error-message', ''))

        vol_data = resp['data']
        volume_uuid = vol_data['uuid']

        # Mount volume.
        params = {'host_nqn': 'nqn.2015-09.com.fungible:testpy-host',
                  'transport': 'TCP'}
        r = execute_command('POST',
                            'storage/volumes/{}/ports'.format(volume_uuid),
                            params)

        self.assertEqual(200, r.status_code)
        resp = r.json()
        self.assertTrue(resp.get('status'))

        print 'Response from attach is %s' % resp
        attach_port = resp['data']
        attach_uuid = attach_port['uuid']

        # Unmount volume.
        r = execute_command('DELETE', 'storage/ports/{}'.format(attach_uuid),
                            params)
        self.assertEqual(200, r.status_code)
        resp = r.json()

        r = execute_command('DELETE',
                            'storage/volumes/{}'.format(volume_uuid), {})
        self.assertEqual(200, r.status_code)
        resp = r.json()
        self.assertTrue(resp['status'])

    def testCreateDurableVolume(self):
        """Test we can set up an error-correcting volume."""
        pool_uuid = self.get_random_pool()
        self.assertIsNotNone(pool_uuid)

        durable_vol_name = "durable-{}".format(str(uuid.uuid4())[:8])

        durable_vol_params = {
            'capacity': 100 * MEGABYTE,
            'name': durable_vol_name,
            'vol_type': 'VOL_TYPE_BLK_EC',
            'allow_expansion': False,
            'data_protection': {'num_failed_disks': 2,
                                'compression_effort': 4,
                                'encrypt': True},
            }

        r = execute_command('POST', 'storage/pools/' + pool_uuid + '/volumes',
                            durable_vol_params)
        self.assertEqual(200, r.status_code)

        resp = r.json()
        self.assertEquals(True, resp['status'],
                          msg='problem creating volume' +
                          resp.get('error-message', ''))

        vol_data = resp['data']
        volume_uuid = vol_data['uuid']

        # Mount volume.
        params = {'host_nqn': 'nqn.2015-09.com.fungible:testpy-host',
                  'transport': 'TCP'}
        r = execute_command('POST',
                            'storage/volumes/{}/ports'.format(volume_uuid),
                            params)

        self.assertEqual(200, r.status_code)
        resp = r.json()
        self.assertTrue(resp.get('status'))

        print 'Response from attach is %s' % resp
        attach_port = resp['data']
        attach_uuid = attach_port['uuid']

        # Unmount volume.
        r = execute_command('DELETE', 'storage/ports/{}'.format(attach_uuid),
                            params)
        self.assertEqual(200, r.status_code)
        resp = r.json()

        r = execute_command('DELETE',
                            'storage/volumes/{}'.format(volume_uuid), {})
        self.assertEqual(200, r.status_code)
        resp = r.json()
        self.assertTrue(resp['status'])

    def testCreateOneGBDurableVolume(self):
        """Test we can create a larger volume."""
        pool_uuid = self.get_random_pool()
        self.assertIsNotNone(pool_uuid)

        durable_vol_name = "durable-{}".format(str(uuid.uuid4())[:8])

        durable_vol_params = {
            'capacity': 1 * GIGABYTE,
            'name': durable_vol_name,
            'vol_type': 'VOL_TYPE_BLK_EC',
            'allow_expansion': False,
            'data_protection': {'num_failed_disks': 2,
                                'compression_effort': 4,
                                'encrypt': True},
            }

        r = execute_command('POST', 'storage/pools/' + pool_uuid + '/volumes',
                            durable_vol_params)
        self.assertEqual(200, r.status_code)

        resp = r.json()
        self.assertEquals(True, resp['status'],
                          msg='problem creating volume' +
                          resp.get('error-message', ''))

        vol_data = resp['data']
        volume_uuid = vol_data['uuid']

        # Mount volume.
        params = {'host_nqn': 'nqn.2015-09.com.fungible:testpy-host',
                  'transport': 'TCP'}
        r = execute_command('POST',
                            'storage/volumes/{}/ports'.format(volume_uuid),
                            params)

        self.assertEqual(200, r.status_code)
        resp = r.json()
        self.assertTrue(resp.get('status'))

        print 'Response from attach is %s' % resp
        attach_port = resp['data']
        attach_uuid = attach_port['uuid']

        # Unmount volume.
        r = execute_command('DELETE', 'storage/ports/{}'.format(attach_uuid),
                            params)
        self.assertEqual(200, r.status_code)
        resp = r.json()

        r = execute_command('DELETE',
                            'storage/volumes/{}'.format(volume_uuid), {})
        self.assertEqual(200, r.status_code)
        resp = r.json()
        self.assertTrue(resp['status'])

    def testCreateStripedVolume(self):
        """Test we can create a volume that's striped across multiple disks."""
        pool_uuid = self.get_random_pool()
        self.assertIsNotNone(pool_uuid)

        durable_vol_name = "striped-{}".format(str(uuid.uuid4())[:8])

        durable_vol_params = {
            'capacity': 100 * MEGABYTE,
            'name': durable_vol_name,
            'vol_type': 'VOL_TYPE_BLK_LOCAL_THIN',
            'allow_expansion': False,
            'stripe_count': 4,
            'data_protection': {},
            }

        r = execute_command('POST', 'storage/pools/' + pool_uuid + '/volumes',
                            durable_vol_params)
        self.assertEqual(200, r.status_code)

        resp = r.json()
        self.assertEquals(True, resp['status'],
                          msg='problem creating volume' +
                          resp.get('error-message', ''))

        vol_data = resp['data']
        volume_uuid = vol_data['uuid']

        # Check stats comes back with sane data.
        r = execute_command('GET', 'storage/volumes/{}'.format(volume_uuid),
                            {})
        self.assertEqual(200, r.status_code)
        resp = r.json()
        self.assertTrue(resp['status'])
        # Test any stat just to see something exists.
        self.assertEquals(4096, resp['data']['stats']['stats']['flvm_block_size'])

        r = execute_command('DELETE',
                            'storage/volumes/{}'.format(volume_uuid), {})
        self.assertEqual(200, r.status_code)
        resp = r.json()
        self.assertTrue(resp['status'])

    def testTooManyStripes(self):
        """Test we get an error if we try to shard disk too much."""
        pool_uuid = self.get_random_pool()
        self.assertIsNotNone(pool_uuid)

        durable_vol_name = "striped-{}".format(str(uuid.uuid4())[:8])

        durable_vol_params = {
            'capacity': 100 * MEGABYTE,
            'name': durable_vol_name,
            'vol_type': 'VOL_TYPE_BLK_LOCAL_THIN',
            'allow_expansion': False,
            # Limit is 12.
            'stripe_count': 14,
            'data_protection': {},
            }

        r = execute_command('POST', 'storage/pools/' + pool_uuid + '/volumes',
                            durable_vol_params)

        self.assertEqual(200, r.status_code)

        resp = r.json()
        if resp['status']:
            # Oops, volume got created.  Delete before asserting.
            self.delete_volume(resp['data'], resp['uuid'])

        self.assertEquals(False, resp['status'],
                          msg='expected failure when creating excessively'
                          'striped drive, but passed.')

def get_fs_uuid():
    """Check that global pool exists and is configured."""
    r = execute_command('GET', 'storage/pools', None, show_exceptions=False)
    resp = r.json()
   # assertEquals(True, resp['status'])
    pool_data = resp['data']
    print pool_data
   # assertEqual('global', pool_data['name'])
   # assertLessEqual(0, len(pool_data['volumes']))
   # assertLessEqual(1, len(pool_data['dpus']))
   # uuid = pool_data['uuid']
   # uuid = pool_data['uuid']
    global_pool = pool_data[pool_data.keys()[0]]
    uuid = global_pool['uuid']
    return uuid



if __name__ == '__main__':
    print(" Running test")
    # unittest.main()
    r = execute_command('GET', 'storage/pools', None, show_exceptions=False)
    if not r or r.status_code != 200:
        print('No VMs present\n')
    else:
        print('VM present\n')
    uuid = get_fs_uuid()
    print('VM present:uuid={}\n'.format(uuid))
